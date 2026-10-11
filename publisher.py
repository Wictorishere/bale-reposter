
import os
import tempfile
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BALE_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "توکن BALE_BOT_TOKEN در فایل .env تنظیم نشده است."
    )

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

session = requests.Session()


def send_request(method, data=None, files=None):
    response = session.post(
        f"{BASE_URL}/{method}",
        data=data,
        files=files,
        timeout=120,
    )

    response.raise_for_status()
    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(f"Bale API error: {result}")

    return result.get("result")


def send_text(chat_id, text):
    return send_request(
        "sendMessage",
        data={
            "chat_id": chat_id,
            "text": text,
        },
    )


def download_media(media_url):
    response = session.get(
        media_url,
        timeout=120,
        stream=True,
    )
    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type", ""
    ).lower()

    if not content_type.startswith(("image/", "video/")):
        response.close()
        raise RuntimeError(
            f"آدرس، فایل عکس یا ویدئو برنگرداند: {content_type}"
        )

    suffix = os.path.splitext(
        urlparse(media_url).path
    )[1]

    if not suffix:
        suffix = ".mp4" if content_type.startswith("video/") else ".jpg"

    temp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    )

    try:
        for chunk in response.iter_content(1024 * 64):
            if chunk:
                temp.write(chunk)
        temp.close()
    except Exception:
        temp.close()
        os.remove(temp.name)
        raise
    finally:
        response.close()

    return temp.name, content_type


def send_media(chat_id, media_url, caption, method):
    file_path = None

    try:
        file_path, content_type = download_media(media_url)

        field_name = "photo" if method == "sendPhoto" else "video"

        mime_type = content_type.split(";")[0].strip()

        with open(file_path, "rb") as media_file:
            return send_request(
                method,
                data={
                    "chat_id": chat_id,
                    "caption": caption[:1024],
                },
                files={
                    field_name: (
                        os.path.basename(file_path),
                        media_file,
                        mime_type,
                    )
                },
            )

    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


def send_photo(chat_id, photo_url, caption=""):
    return send_media(
        chat_id,
        photo_url,
        caption,
        "sendPhoto",
    )


def send_video(chat_id, video_url, caption=""):
    return send_media(
        chat_id,
        video_url,
        caption,
        "sendVideo",
    )