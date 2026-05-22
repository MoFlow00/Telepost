import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

with open("channels_data.json","r",encoding="utf-8") as f:
    channels = json.load(f)

for channel in channels:

    username = channel.get("username")

    if not username:
        continue

    try:

        url = f"https://t.me/s/{username}"

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        posts = soup.select(
            ".tgme_widget_message"
        )

        if not posts:
            continue

        last = posts[-1]

        post_id = (
            last.get("data-post")
            .split("/")[-1]
        )

        time_el = last.select_one("time")

        post_date = (
            time_el.get("datetime")
            if time_el
            else None
        )

        channel["last_post_id"] = int(post_id)

        channel["last_post_date"] = post_date

        if post_date:

            ts = int(
                datetime.fromisoformat(
                    post_date.replace(
                        "Z","+00:00"
                    )
                ).timestamp()
            )

            channel[
                "last_post_timestamp"
            ] = ts

        print("OK:",username)

    except Exception as e:

        print(
            "ERROR:",
            username,
            e
        )

with open(
    "channels_data.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        channels,
        f,
        ensure_ascii=False,
        indent=2
    )
