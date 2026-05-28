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

MAX_HISTORY_POSTS = 10


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

        if "K" in text:

            return int(
                float(
                    text.replace("K", "")
                ) * 1000
            )

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

        # latest posts

        latest_posts = posts[-2:]

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
        # OLD HISTORY
        # ─────────────────────────────

        old_history = channel.get(
            "posts_history",
            []
        )

        if not isinstance(
            old_history,
            list
        ):
            old_history = []

        existing_ids = {

            p.get("post_id")

            for p in old_history

            if p.get("post_id")

        }

        new_posts = []

        # ─────────────────────────────
        # PROCESS POSTS
        # ─────────────────────────────

        for p in latest_posts:

            try:

                data_post = p.get(
                    "data-post",
                    ""
                )

                post_id = int(
                    data_post
                    .split("/")[-1]
                )

            except Exception:

                continue

            # text

            post_text = ""

            txt = p.select_one(
                ".tgme_widget_message_text"
            )

            if txt:

                post_text = txt.get_text(
                    " ",
                    strip=True
                )[:1500]

            # date

            post_date = ""

            timestamp = 0

            time_el = p.select_one(
                "time"
            )

            if time_el:

                post_date = (
                    time_el.get(
                        "datetime"
                    ) or ""
                )

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

                except Exception:

                    timestamp = 0

            # views

            views = 0

            views_el = p.select_one(
                ".tgme_widget_message_views"
            )

            if views_el:

                views = parse_number(
                    views_el.text
                )

            # image

            image = ""

            img_wrap = p.select_one(
                ".tgme_widget_message_photo_wrap"
            )

            if img_wrap:

                style = (
                    img_wrap.get(
                        "style",
                        ""
                    )
                )

                if "url(" in style:

                    try:

                        image = (
                            style
                            .split("url('")[1]
                            .split("')")[0]
                        )

                    except Exception:

                        pass

            # append only new posts

            if post_id not in existing_ids:

                new_posts.append({

                    "post_id":
                    post_id,

                    "text":
                    post_text,

                    "date":
                    post_date,

                    "timestamp":
                    timestamp,

                    "views":
                    views,

                    "image":
                    image

                })

        # ─────────────────────────────
        # MERGE HISTORY
        # ─────────────────────────────

        full_history = (
            new_posts
            +
            old_history
        )

        full_history.sort(

            key=lambda x:
            x.get(
                "timestamp",
                0
            ),

            reverse=True

        )

        full_history = full_history[
            :MAX_HISTORY_POSTS
        ]

        # ─────────────────────────────
        # LANGUAGE
        # ─────────────────────────────

        combined_text = " ".join([

            p.get("text", "")

            for p in full_history[:2]

        ])

        language = detect_language(
            combined_text
        )

        if language not in [
            "arabic",
            "english"
        ]:
            language = "other"

        # ─────────────────────────────
        # LAST POST
        # ─────────────────────────────

        latest = full_history[0]

        channel[
            "last_post_id"
        ] = latest.get(
            "post_id",
            0
        )

        channel[
            "last_post_date"
        ] = latest.get(
            "date",
            ""
        )

        channel[
            "last_post_timestamp"
        ] = latest.get(
            "timestamp",
            0
        )

        channel[
            "last_post_views"
        ] = latest.get(
            "views",
            0
        )

        channel[
            "subscribers"
        ] = subscribers

        channel[
            "language"
        ] = language

        channel[
            "last_posts_text"
        ] = [

            p.get("text", "")

            for p in full_history[:2]

        ]

        channel[
            "posts_history"
        ] = full_history

        updated_channels.append(
            channel
        )

        print(

            "UPDATED:",

            username,

            "| HISTORY:",
            len(full_history),

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
# REMOVE DEAD CHANNELS
# ─────────────────────────────

merged = []

for ch in updated_channels:

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
