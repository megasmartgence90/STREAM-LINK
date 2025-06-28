from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import os
import time

# Başsız brauzer üçün ayarlar
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)

url = "https://sepehrtv.ir/live/sahar1"
driver.get(url)

# JavaScript-in yüklənməsi üçün bir az gözlə
time.sleep(5)

# Saytdakı bütün səhifə məzmununu al
page_source = driver.page_source

# m3u8 linkini tap
matches = re.findall(r'(https?://[^\s"\']+\.m3u8)', page_source)
driver.quit()

if matches:
    m3u8_url = matches[0]
    print("Tapıldı:", m3u8_url)

    folder = "m3u8_links"
    os.makedirs(folder, exist_ok=True)

    with open(os.path.join(folder, "sahar1.m3u8"), "w") as f:
        f.write(m3u8_url)

    print("Link fayla yazıldı.")
else:
    print("m3u8 link tapılmadı.")
