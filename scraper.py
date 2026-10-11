
from playwright.sync_api import sync_playwright
import re


def clean_text(text):
    text = re.split(
        r"\n\s*Join to\b",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    return text.strip()


def get_posts(channel, limit=10):
    url = f"https://ble.ir/s/{channel}"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=(
                r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            ),
        )

        try:
            page = browser.new_page()
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(4000)

            posts = page.locator(
                "div.MessageItem_messageWrapper__E9ZFU"
            )

            count = posts.count()
            print(f"{channel}: {count} پست پیدا شد.")

            for i in range(min(count, limit)):
                try:
                    post = posts.nth(i)
                    post_id = post.get_attribute("data-sid")

                    # کپشن عکس را به پیش‌نمایش لینک ترجیح بده.
                    caption = post.locator(
                        "div.Photo_caption__B_CHL"
                    )

                    if caption.count() > 0:
                        text = caption.last.inner_text()
                    else:
                        text_blocks = post.locator(
                            "div.Text_text__Um9IF"
                        )

                        if text_blocks.count() == 0:
                            text = ""
                        else:
                            # اگر چند بخش متنی وجود دارد،
                            # آخرین بخش معمولاً متن اصلی یا کپشن است.
                            text = text_blocks.last.inner_text()

                    text = clean_text(text)

                   
                    # استخراج عکس‌های پست
                    images = post.locator("img").evaluate_all("""
                        elements => elements.map(img => ({
                            url: img.currentSrc || img.src,
                            width: img.naturalWidth,
                            height: img.naturalHeight
                        }))
                    """)

                    image_urls = [
                        img["url"]
                        for img in images
                        if img["url"].startswith("http")
                        and img["width"] >= 150
                        and img["height"] >= 150
                    ]

                    # استخراج ویدئوهای پست
                    videos = post.locator("video, video source").evaluate_all("""
                        elements => elements.map(el => {
                            const video = el.tagName === "VIDEO" ? el : el.parentElement;
                            return el.currentSrc || el.src || video?.src || "";
                        })
                    """)

                    video_urls = [
                        url for url in videos
                        if url.startswith("http")
                    ]

                    media_url = None
                    media_type = None

                    if video_urls:
                        media_url = video_urls[0]
                        media_type = "video"
                    elif image_urls:
                        media_url = image_urls[0]
                        media_type = "photo"

                    if post_id and (text or media_url):
                        results.append({
                            "id": post_id,
                            "text": text,
                            "channel": channel,
                            "media_url": media_url,
                            "media_type": media_type,
                        })

                except Exception as error:
                    print(
                        f"خطا در استخراج پست شماره {i + 1} "
                        f"از {channel}: {error}"
                    )
                    continue

        finally:
            browser.close()

    return results


if __name__ == "__main__":
    for post in get_posts("tasnimnews", limit=10):
        print("-" * 50)
        print("ID:", post["id"])
        print("متن:", post["text"])
        print("نوع رسانه:", post.get("media_type"))
        print("آدرس رسانه:", post.get("media_url"))