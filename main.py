import os
import sys

# Lazımi modulların yoxlanması və avtomatik quraşdırılması
def ensure_module(module_name, package_name=None):
    try:
        __import__(module_name)
    except ImportError:
        print(f"{module_name} modulu tapılmadı. Quraşdırılır...")
        os.system(f'pip install {package_name or module_name}')

ensure_module("slugify", "python-slugify")
ensure_module("tqdm")

# Modul idxalları
import re
import requests
import json
from urllib.parse import urljoin
from slugify import slugify
from tqdm import tqdm

def get_stream_url(url, pattern, method="GET", headers={}, body={}):
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
        elif method == "POST":
            r = requests.post(url, json=body, headers=headers)
        else:
            print(method, "dəstəklənmir və ya yanlışdır.")
            return None
        results = re.findall(pattern, r.text)
        if results:
            return results[0]
        else:
            print(f"Nəticə tapılmadı: {url}")
            return None
    except Exception as e:
        print(f"Xəta baş verdi: {e}")
        return None

def playlist_text(url):
    text = ""
    r = requests.get(url)
    if r.status_code == 200:
        for line in r.iter_lines():
            line = line.decode()
            if not line:
                continue
            if line[0] != "#":
                text += urljoin(url, line)
            else:
                text += line
            text += "\n"
        return text
    return ""

def main():
    with open(sys.argv[1], "r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    output_folder = config["output"].get("folder", "streams")
    os.makedirs(output_folder, exist_ok=True)

    for channel in tqdm(config["channels"]):
        name = channel["name"]
        slug = channel["slug"]
        url = channel["url"]
        filename = slugify(name.lower()) + ".txt"  # və ya .m3u8 əgər link tapılırsa

        # Dummy bir regex pattern – realda dəyişdirilməlidir!
        # Əgər real pattern varsa, config-ə əlavə et və buradan götür.
        pattern = r"https?:\/\/.*?\.m3u8"

        stream_url = get_stream_url(url, pattern)
        if not stream_url:
            continue

        file_path = os.path.join(output_folder, filename)

        text = playlist_text(stream_url)
        if text:
            with open(file_path, "w+", encoding="utf-8") as f:
                f.write(text)
        else:
            print(f"{name} üçün yazı tapılmadı.")

if __name__ == "__main__":
    main()
