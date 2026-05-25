import json
import time
import requests

from bs4 import BeautifulSoup
from datetime import datetime


HEADERS = {
    "User-Agent":
    "Mozilla/5.0"
}

INPUT_FILE = "channels_data.json"


# ─────────────────────────────
# HELPERS
# ─────────────────────────────

def parse_number(text):

    if not text:
        return 0

    try:

        text = (
            text
            .strip()
            .upper()
            .replace(",", "")
        )

        # 1.2K

        if "K" in text:

            return int(
                float(
                    text.replace("K", "")
                ) * 1000
            )

        # 2.5M

        if "M" in text:

            return int(
                float(
                    text.replace("M", "")
                ) * 1000000
            )

        digits = "".join(
            c for c in text
            if c.isdigit()
        )

        return int(digits)

    except Exception:

        return 0


# ─────────────────────────────
# LANGUAGE DETECTION
# ─────────────────────────────

def detect_language(text):

    if not text:
        return "other"

    text = text.lower()

    # count chars

    arabic_count = sum(

        1

        for c in text

        if '\u0600' <= c <= '\u06FF'

    )

    english_count = sum(

        1

        for c in text

        if 'a' <= c <= 'z'

    )

    russian_count = sum(

        1

        for c in text

        if 'а' <= c <= 'я'
        or
        c == 'ё'

    )

    persian_count = sum(

        1

        for c in text

        if c in [
            'پ',
            'چ',
            'ژ',
            'گ',
            'ک',
            'ی'
        ]

    )

    # Persian → Other

    if (
        arabic_count > 15
        and
        persian_count > 2
    ):
        return "other"

    # Arabic

    if (
        arabic_count > english_count
        and
        arabic_count > russian_count
        and
        arabic_count > 15
    ):
        return "arabic"

    # English

    if (
        english_count > arabic_count
        and
        english_count > russian_count
        and
        english_count > 20
    ):
        return "english"

    # Russian + everything else

    return "other"


# ─────────────────────────────
# LOAD JSON
# ─────────────────────────────

try:

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        channels = json.load(f)

except Exception as e:

    print(
        "FAILED TO LOAD JSON:",
        e
    )

    channels = []


# ─────────────────────────────
# KEEP HISTORY
# ─────────────────────────────

old_channels_map = {

    ch.get("username"): ch

    for ch in channels

    if ch.get("username")

}


# ─────────────────────────────
# UPDATE CHANNELS
# ─────────────────────────────

total = len(channels)

updated_channels = []

for index, channel in enumerate(channels):

    username = channel.get(
        "username"
    )

    if not username:

        print(
            f"[{index+1}/{total}]",
            "SKIP EMPTY USERNAME"
        )

        continue

    print(
        f"[{index+1}/{total}]",
        "CHECKING:",
        username
    )

    try:

        url = (
            f"https://t.me/s/{username}"
        )

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )

        # HTTP ERROR

        if r.status_code != 200:

            print(
                "HTTP ERROR:",
                username,
                r.status_code
            )

            updated_channels.append(channel)

            continue

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        # ─────────────────────────────
        # POSTS
        # ─────────────────────────────

        posts = soup.select(
            ".tgme_widget_message"
        )

        if not posts:

            print(
                "NO POSTS:",
                username
            )

            updated_channels.append(channel)

            continue

        # last 2 posts

        last_posts = posts[-2:]

        # ─────────────────────────────
        # LAST POST
        # ─────────────────────────────

        last = last_posts[-1]

        # ─────────────────────────────
        # POST ID
        # ─────────────────────────────

        data_post = last.get(
            "data-post"
        )

        if not data_post:

            print(
                "NO POST ID:",
                username
            )

            updated_channels.append(channel)

            continue

        try:

            post_id = int(
                data_post
                .split("/")[-1]
            )

        except Exception:

            print(
                "BAD POST ID:",
                username
            )

            updated_channels.append(channel)

            continue

        # ─────────────────────────────
        # DATE
        # ─────────────────────────────

        time_el = last.select_one(
            "time"
        )

        post_date = None

        if time_el:

            post_date = (
                time_el.get(
                    "datetime"
                )
            )

        # ─────────────────────────────
        # TIMESTAMP
        # ─────────────────────────────

        timestamp = 0

        if post_date:

            try:

                timestamp = int(

                    datetime
                    .fromisoformat(

                        post_date.replace(
                            "Z",
                            "+00:00"
                        )

                    )
                    .timestamp()

                )

            except Exception as e:

                print(
                    "BAD DATE:",
                    username,
                    e
                )

        # ─────────────────────────────
        # VIEWS
        # ─────────────────────────────

        views = 0

        views_el = last.select_one(
            ".tgme_widget_message_views"
        )

        if views_el:

            views = parse_number(
                views_el.text
            )

        # ─────────────────────────────
        # SUBSCRIBERS
        # ─────────────────────────────

        subscribers = 0

        subs_wrap = soup.select_one(
            ".tgme_channel_info_counters"
        )

        if subs_wrap:

            counters = subs_wrap.select(
                ".tgme_channel_info_counter"
            )

            for counter in counters:

                counter_type = counter.select_one(
                    ".counter_type"
                )

                if not counter_type:
                    continue

                label = (
                    counter_type
                    .text
                    .strip()
                    .lower()
                )

                if (
                    "subscriber" in label
                    or
                    "member" in label
                ):

                    value = counter.select_one(
                        ".counter_value"
                    )

                    if value:

                        subscribers = parse_number(
                            value.text
                        )

                    break

        # ─────────────────────────────
        # LAST 2 POSTS TEXT
        # ─────────────────────────────

        last_posts_text = []

        for p in last_posts:

            txt = p.select_one(
                ".tgme_widget_message_text"
            )

            if txt:

                clean_text = txt.get_text(
                    " ",
                    strip=True
                )

                if clean_text:

                    last_posts_text.append(
                        clean_text[:500]
                    )

        combined_text = " ".join(
            last_posts_text
        )

        # ─────────────────────────────
        # LANGUAGE
        # ─────────────────────────────

        language = detect_language(
            combined_text
        )

        if language not in [
            "arabic",
            "english"
        ]:
            language = "other"

        # ─────────────────────────────
        # SAVE
        # ─────────────────────────────

        channel[
            "last_post_id"
        ] = post_id

        channel[
            "last_post_date"
        ] = post_date

        channel[
            "last_post_timestamp"
        ] = timestamp

        channel[
            "last_post_views"
        ] = views

        channel[
            "subscribers"
        ] = subscribers

        channel[
            "language"
        ] = language

        channel[
            "last_posts_text"
        ] = last_posts_text

        updated_channels.append(channel)

        print(

            "UPDATED:",

            username,

            "| POSTS:",
            post_id,

            "| VIEWS:",
            views,

            "| SUBS:",
            subscribers,

            "| LANG:",
            language

        )

        # avoid rate limit

        time.sleep(0.7)

    except requests.exceptions.Timeout:

        print(
            "TIMEOUT:",
            username
        )

        updated_channels.append(channel)

        continue

    except requests.exceptions.ConnectionError:

        print(
            "CONNECTION ERROR:",
            username
        )

        updated_channels.append(channel)

        continue

    except Exception as e:

        print(
            "UNKNOWN ERROR:",
            username,
            e
        )

        updated_channels.append(channel)

        continue


# ─────────────────────────────
# CLEAN + MERGE HISTORY
# ─────────────────────────────

merged = []

for ch in updated_channels:

    username = ch.get("username")

    old = old_channels_map.get(
        username,
        {}
    )

    # preserve old data

    if not ch.get("last_posts_text"):

        ch["last_posts_text"] = old.get(
            "last_posts_text",
            []
        )

    if not ch.get("language"):

        ch["language"] = old.get(
            "language",
            "other"
        )

    if not ch.get("subscribers"):

        ch["subscribers"] = old.get(
            "subscribers",
            0
        )

    if not ch.get("last_post_views"):

        ch["last_post_views"] = old.get(
            "last_post_views",
            0
        )

    # remove dead channels

    if ch.get(
        "last_post_timestamp",
        0
    ) > 0:

        merged.append(ch)

print(

    "\nREMOVED:",

    len(updated_channels) - len(merged),

    "DEAD CHANNELS"

)

channels = merged


# ─────────────────────────────
# SAVE JSON
# ─────────────────────────────

try:

    with open(
        INPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            channels,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        "\nDONE. JSON UPDATED."
    )

except Exception as e:

    print(
        "FAILED TO SAVE JSON:",
        e
    )
