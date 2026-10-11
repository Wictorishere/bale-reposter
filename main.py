import json
import os
import time
import re

from scraper import get_posts
from publisher import send_text, send_photo, send_video


# =========================================================
# CONFIG
# =========================================================

DRY_RUN = False
CHECK_INTERVAL = 60
MAX_POSTS_PER_SOURCE = 10

SENT_FILE = "sent_post_ids_multi.json"
INITIALIZED_FILE = "initialized_sources.json"


# =========================================================
# SOURCES AND DESTINATIONS
# =========================================================

SOURCES = [
    {
        "name": "iran_times_to_plusnew",
        "slug": "iran_times1",
        "destination": "@plusnew",
        "sticker": "☑️",
        "signature": "@plusnew",
    },
    {
        "name": "iran_times_to_depthnews",
        "slug": "iran_times1",
        "destination": "@depthnews",
        "sticker": "🔵",
        "signature": "🔹*Join to* [*Depth New*](ble.ir/join/G5oqsAvUeF)",
    },
    {
            "name": "iran_times_to_depthnews",
            "slug": "iran_times1",
            "destination": "@echovent",
            "sticker": "🔴",
            "signature": "🟥 @echovent",
        },
]


# =========================================================
# SENT POSTS
# =========================================================

def load_sent_posts():
    if not os.path.exists(SENT_FILE):
        return set()

    try:
        with open(SENT_FILE, "r", encoding="utf-8") as file:
            return set(json.load(file))

    except (OSError, json.JSONDecodeError):
        print("خطا: فایل سابقه ارسال قابل خواندن نیست.")
        raise


def save_sent_posts(sent_posts):
    temporary_file = SENT_FILE + ".tmp"

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(
            sorted(sent_posts),
            file,
            ensure_ascii=False,
            indent=2,
        )

    os.replace(temporary_file, SENT_FILE)


# =========================================================
# INITIALIZED ROUTES
# =========================================================

def load_initialized_sources():
    if not os.path.exists(INITIALIZED_FILE):
        return set()

    try:
        with open(INITIALIZED_FILE, "r", encoding="utf-8") as file:
            return set(json.load(file))

    except (OSError, json.JSONDecodeError):
        print("خطا: فایل مسیرهای مقداردهی‌شده قابل خواندن نیست.")
        raise


def save_initialized_sources(initialized_sources):
    temporary_file = INITIALIZED_FILE + ".tmp"

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(
            sorted(initialized_sources),
            file,
            ensure_ascii=False,
            indent=2,
        )

    os.replace(temporary_file, INITIALIZED_FILE)


# =========================================================
# POST IDENTIFICATION
# =========================================================

def post_key(source, post):
    return (
        f"{source['name']}|"
        f"{post['id']}|"
        f"{source['destination']}"
    )


# =========================================================
# TEXT CLEANUP
# =========================================================

def remove_source_signature(text, source):
    slug = source.get("slug", "").strip().lower()

    # برای مثال iran_times1 -> iran_times و irantimes
    slug_without_digits = re.sub(r"\d+$", "", slug)

    possible_names = {
        slug,
        slug_without_digits,
        slug.replace("_", ""),
        slug_without_digits.replace("_", ""),
        slug.replace("_", " "),
        slug_without_digits.replace("_", " "),
    }

    possible_names.discard("")

    # حذف نام نمایشی مشخص کانال ایران تایمز
    text = re.sub(
        r"(?im)^[ \t]*ایران[ \t]*تایمز[ \t]*\|[ \t]*IRAN[ \t]*TIMES[ \t]*$",
        "",
        text,
    )

    # حذف آیدی یا نام مبدا، وقتی در یک خط مستقل آمده باشد
    for name in sorted(possible_names, key=len, reverse=True):
        pattern = (
            r"(?im)^[ \t]*@?"
            + re.escape(name)
            + r"[ \t]*$"
        )

        text = re.sub(pattern, "", text)

    # حذف خطوط خالی ابتدا و انتهای متن
    # و یکسان‌سازی فاصله‌های انتهای خطوط
    lines = [
        line.rstrip()
        for line in text.splitlines()
    ]

    text = "\n".join(lines).strip()

    # حداکثر یک خط خالی بین بخش‌های متن
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)

    return text.strip()




def format_text(text, source):
    text = remove_source_signature(
        text or "",
        source,
    )

    slug = source.get("slug", "").strip().lower()

    # حذف امضای کانکت‌نیوز از مبدأ خودش
    
    # حذف خط امضای کانکت‌نیوز، چه لینک داشته باشد چه نداشته باشد
    if slug in ("connect_news", "iran_times1"):
        text = re.sub(
            r"(?im)^[ \t]*.*(?:connect[_ ]news|𝙘𝙤𝙣𝙣𝙚𝙘𝙩[_ ]𝙣𝙚𝙬𝙨|ble\.ir/join/BJQoZvDAgk).*$",
            "",
            text,
        )

    # حذف استیکر قرمز ابتدای خبر مبدأ ایران تایمز
    if slug == "iran_times1":
        text = re.sub(
            r"^\s*🔴\s*",
            "",
            text,
            count=1,
        )

        # حذف امضای کانکت‌نیوز از پست‌های ایران تایمز
        text = re.sub(
            r"(?im)^.*(?:connect[_ ]news|ble\.ir/join/BJQoZvDAgk).*$",
            "",
            text,
        )

    # مرتب‌سازی خطوط خالی
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)
    text = text.strip()

    sticker = source.get("sticker", "")
    signature = source.get("signature", "").strip()

    # فاصله بعد از استیکر فقط برای پلاس
    if sticker and text:
        if source.get("name") == "iran_times_to_depthnews":
            text = f"{sticker}{text}"
        else:
            text = f"{sticker} {text}"

    if text and signature:
        text = f"{text.rstrip()}\n\n{signature}"
    elif signature:
        text = signature

    return text


# =========================================================
# PUBLISH POST
# =========================================================

def publish_post(source, post):
    destination = source["destination"]

    text = format_text(
        post.get("text", ""),
        source,
    )

    media_url = post.get("media_url")
    media_type = post.get("media_type")

    if DRY_RUN:
        print("\n[حالت تست]")
        print("مبدأ:", source["slug"])
        print("مقصد:", destination)
        print("شناسه پست:", post["id"])
        print("نوع رسانه:", media_type)
        print("آدرس رسانه:", media_url)
        print("متن نهایی:")
        print(text)
        print("-" * 45)

        return False

    if media_url and media_type == "photo":
        send_photo(destination, media_url, text)

    elif media_url and media_type == "video":
        send_video(destination, media_url, text)

    elif text:
        send_text(destination, text)

    else:
        raise RuntimeError(
            "پست نه متن دارد و نه رسانه قابل ارسال."
        )

    return True


# =========================================================
# MAIN LOOP
# =========================================================


def main():
    sent_posts = load_sent_posts()

    # این مجموعه فقط برای اجرای فعلی ربات است.
    # در هر اجرای جدید، هر مسیر دوباره مبناگذاری می‌شود.
    baseline_done = set()

    print("ربات بازنشر شروع شد.")
    print("تعداد مسیرهای انتشار:", len(SOURCES))
    print("حالت تست:", DRY_RUN)

    while True:
        for source in SOURCES:
            route_name = source["name"]
            slug = source["slug"]
            destination = source["destination"]

            print(
                f"\nبررسی مبدأ: {slug} "
                f"-> مقصد: {destination}"
            )

            try:
                posts = get_posts(
                    slug,
                    limit=MAX_POSTS_PER_SOURCE,
                )

                if not posts:
                    print("پستی پیدا نشد.")
                    continue

                # اولین بررسی این مسیر در اجرای فعلی:
                # تمام پست‌های فعلی ثبت می‌شوند و منتشر نمی‌شوند.
                if route_name not in baseline_done:
                    for post in posts:
                        sent_posts.add(post_key(source, post))

                    save_sent_posts(sent_posts)
                    baseline_done.add(route_name)

                    print(
                        f"مبنای اولیه مسیر {route_name} ثبت شد؛ "
                        f"{len(posts)} پست فعلی نادیده گرفته شد."
                    )
                    continue

                # فقط پست‌هایی که بعد از مبناگذاری دیده می‌شوند
                # و قبلاً ثبت نشده‌اند، برای انتشار انتخاب می‌شوند.
                new_posts = [
                    post for post in posts
                    if post_key(source, post) not in sent_posts
                ]

                # انتشار از قدیمی‌تر به جدیدتر
                for post in reversed(new_posts):
                    key = post_key(source, post)

                    try:
                        published = publish_post(source, post)

                        if published:
                            sent_posts.add(key)
                            save_sent_posts(sent_posts)

                            print(
                                "ارسال موفق:",
                                post["id"],
                                "->",
                                destination,
                            )

                    except Exception as error:
                        print(
                            f"خطا در پردازش پست {post['id']} "
                            f"برای {destination}: {error}"
                        )

            except Exception as error:
                print(
                    f"خطا در بررسی {slug} "
                    f"برای {destination}: {error}"
                )

        print(
            f"\nبررسی بعدی تا {CHECK_INTERVAL} ثانیه دیگر."
        )

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()

