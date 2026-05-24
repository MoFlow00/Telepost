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
# UPDATE
# ─────────────────────────────

total = len(channels)

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

            continue

        last = posts[-1]

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

        print(

            "UPDATED:",

            username,

            "| POSTS:",
            post_id,

            "| VIEWS:",
            views,

            "| SUBS:",
            subscribers

        )

        # avoid telegram rate limit

        time.sleep(0.7)

    except requests.exceptions.Timeout:

        print(
            "TIMEOUT:",
            username
        )

        continue

    except requests.exceptions.ConnectionError:

        print(
            "CONNECTION ERROR:",
            username
        )

        continue

    except Exception as e:

        print(
            "UNKNOWN ERROR:",
            username,
            e
        )

        continue

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
