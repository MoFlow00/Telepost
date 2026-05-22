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

    print("FAILED TO LOAD JSON:", e)

    channels = []

# ─────────────────────────────
# UPDATE CHANNELS
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

        posts = soup.select(
            ".tgme_widget_message"
        )

        # NO POSTS

        if not posts:

            print(
                "NO POSTS:",
                username
            )

            continue

        last = posts[-1]

        data_post = last.get(
            "data-post"
        )

        # NO POST ID

        if not data_post:

            print(
                "NO POST ID:",
                username
            )

            continue

        # BAD POST ID

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

        # DATE

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

        # TIMESTAMP

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

        # SAVE DATA

        channel[
            "last_post_id"
        ] = post_id

        channel[
            "last_post_date"
        ] = post_date

        channel[
            "last_post_timestamp"
        ] = timestamp

        print(
            "UPDATED:",
            username,
            post_id
        )

        # SMALL DELAY
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
