
import requests
import re

url = "https://ble.ir/akhbar_mamllekat"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    )
}

response = requests.get(url, headers=headers, timeout=20)
html = response.text

print("Status:", response.status_code)
print("HTML size:", len(html))

terms = [
    "__next_f",
    "self.__next",
    "buildId",
    "akhbar_mamllekat",
    "initialState",
    "application/json",
    "api/",
    "graphql",
    "post",
    "channel",
    "ble.ir/join",
]

for term in terms:
    print(f"\n--- {term} ---")
    positions = [
        match.start()
        for match in re.finditer(re.escape(term), html, re.IGNORECASE)
    ]
    print("Count:", len(positions))

    for pos in positions[:2]:
        snippet = html[max(0, pos - 180):pos + 350]
        print(snippet)
        print()

with open("inspect_page.html", "w", encoding="utf-8") as file:
    file.write(html)

print("HTML saved to inspect_page.html")