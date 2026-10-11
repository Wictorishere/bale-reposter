
from playwright.sync_api import sync_playwright
import re

CHANNEL = "akhbar_mamllekat"
URL = f"https://ble.ir/s/{CHANNEL}"

def clean_text(text):
    text = text.replace("\u200c", "\u200c")
    text = re.sub(
        r"Join to\s+𝗔𝗸𝗵𝗯𝗮𝗿.*$",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return text.strip()

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        executable_path=(
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        ),
    )

    page = browser.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)

    posts = page.locator(
        "div.MessageItem_messageWrapper__E9ZFU"
    )

    print("تعداد پست‌های پیدا شده:", posts.count())

    for i in range(min(posts.count(), 10)):
        post = posts.nth(i)

        sid = post.get_attribute("data-sid")
        text_element = post.locator("div.Text_text__Um9IF")
        text = clean_text(text_element.inner_text()) if text_element.count() else ""

        print("\n" + "=" * 50)
        print("شناسه:", sid)
        print("متن:", text[:1000])

    browser.close()