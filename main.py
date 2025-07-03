import os
import sys

def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        print(f"{package} modulu tapılmadı. Quraşdırılır...")
        os.system(f"{sys.executable} -m pip install {package}")

install_and_import("slugify")
install_and_import("requests")
install_and_import("tqdm")

from slugify import slugify
import re
import requests
import json


def get_stream_url(url, pattern):
    try:
        r = requests.get(url, timeout=10)
        results = re.findall(pattern, r.text)
        if results:
            return results[0].replace("\\", "")  # escape-ləri təmizləyirik
        else:
            print(f"Nəticə tapılmadı: {url}")
            return None
    except Exception as e:
        print(f"Xəta baş verdi: {e}")
        return None

def save_stream(name, folder, stream_url):
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, slugify(name.lower()) + ".m3u8")
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(stream_url)
        print(f"Yazıldı: {filename}")
    except Exception as e:
        print(f"Yazılarkən xəta: {e}")

def main():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    pattern = config.get("pattern", r"https?:\/\/.*?\.m3u8")
    output_folder = config["output"]["folder"]

    for ch in config["channels"]:
        name = ch["name"]
        url = ch["url"]
        stream_url = get_stream_url(url, pattern)
        if stream_url:
            save_stream(name, output_folder, stream_url)
        else:
            print(f"{name} üçün stream tapılmadı.")

if __name__ == "__main__":
    main()
