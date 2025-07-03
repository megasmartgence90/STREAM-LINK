import os
import sys

# --- Lazımi modulların yoxlanması və avtomatik quraşdırılması ---
def ensure_module(module_name, package_name=None):
    try:
        __import__(module_name)
    except ImportError:
        print(f"{module_name} modulu tapılmadı. Quraşdırılır...")
        os.system(f'pip install {package_name or module_name}')

ensure_module("slugify", "python-slugify")
ensure_module("tqdm")

# --- Modul idxalları ---
import re
import requests
import json
from urllib.parse import urljoin
from slugify import slugify
from tqdm import tqdm

def get_stream_url(url, pattern, method="GET", headers={}, body={}):
    if method == "GET":
        r = requests.get(url, headers=headers)
    elif method == "POST":
        r = requests.post(url, json=body, headers=headers)
    else:
        print(method, "dəstəklənmir və ya səhv yazılıb.")
        return None
    results = re.findall(pattern, r.text)
    if len(results) > 0:
        return results[0]
    else:
        print("Cavabda uyğun nəticə tapılmadı. Regex patterni yoxlayın: {} üçün {}".format(method, url))
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
    config_file = open(sys.argv[1], "r", encoding="utf-8")
    config = json.load(config_file)
    for site in config:
        site_path = os.path.join(os.getcwd(), site["slug"])
        os.makedirs(site_path, exist_ok=True)
        for channel in tqdm(site["channels"]):
            channel_file_path = os.path.join(site_path, slugify(channel["name"].lower()) + ".m3u8")
            channel_url = site["url"]
            for variable in channel["variables"]:
                channel_url = channel_url.replace(variable["name"], variable["value"])
            stream_url = get_stream_url(channel_url, site["pattern"])
            if not stream_url:
                if os.path.isfile(channel_file_path):
                    os.remove(channel_file_path)
                continue
            if site["output_filter"] not in stream_url:
                if os.path.isfile(channel_file_path):
                    os.remove(channel_file_path)
                continue
            if site["mode"] == "variant":
                text = playlist_text(stream_url)
            elif site["mode"] == "master":
                text = "#EXTM3U\n##EXT-X-VERSION:3\n#EXT-X-STREAM-INF:BANDWIDTH={}\n{}".format(site["bandwidth"], stream_url)
            else:
                print("playlist mode yanlışdır və ya qeyd olunmayıb.")
                text = ""
            if text:
                with open(channel_file_path, "w+", encoding="utf-8") as channel_file:
                    channel_file.write(text)
            else:
                if os.path.isfile(channel_file_path):
                    os.remove(channel_file_path)

if __name__ == "__main__": 
    main()
