import requests
from bs4 import BeautifulSoup
import re
import os

# Mənbə URL
url = "https://sepehrtv.ir/live/sahar1"

# Sorğu göndər
headers = {
    "User-Agent": "Mozilla/5.0"
}
response = requests.get(url, headers=headers)
html = response.text

# HTML-dən m3u8 linki çıxar
soup = BeautifulSoup(html, 'html.parser')
scripts = soup.find_all("script")

m3u8_url = None

# Skriptlərdən m3u8 linkini axtar
for script in scripts:
    if script.string:
        matches = re.findall(r'(https?://[^\s"\']+\.m3u8)', script.string)
        if matches:
            m3u8_url = matches[0]
            break

if m3u8_url:
    print("Tapıldı:", m3u8_url)

    # Fayla yaz
    folder = "m3u8_links"
    os.makedirs(folder, exist_ok=True)

    with open(os.path.join(folder, "sahar1.m3u8.txt"), "w") as f:
        f.write(m3u8_url)

    print(f"Link '{folder}/sahar1.m3u8.txt' faylına yazıldı.")
else:
    print("m3u8 link tapılmadı.")
