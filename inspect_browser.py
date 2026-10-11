
from playwright.sync_api import sync_playwright

URL = "https://ble.ir/s/akhbar_mamllekat"
TARGET = "ادعای وزیر خزانه‌داری آمریکا"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        executable_path=(
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        ),
    )

    page = browser.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(7000)

    result = page.evaluate("""(target) => {
        const elements = [...document.querySelectorAll("body *")];

        const matches = elements.filter(el => {
            const text = el.innerText || "";
            return text.includes(target);
        }).sort((a, b) => {
            return (a.innerText || "").length -
                   (b.innerText || "").length;
        });

        if (!matches.length) {
            return "متن هدف پیدا نشد.";
        }

        let el = matches[0];
        const output = [];

        for (let i = 0; i < 7 && el; i++, el = el.parentElement) {
            output.push({
                level: i,
                tag: el.tagName,
                className: String(el.className || ""),
                text: (el.innerText || "").slice(0, 350),
                html: el.outerHTML.slice(0, 900)
            });
        }

        return output;
    }""", TARGET)

    print(result)
    browser.close()