import streamlink
import sys
import os
import json
import re
from urllib.parse import urlparse


def get_height(quality):
    """
    1080p60 -> 1080
    720p -> 720
    360p -> 360
    """
    match = re.search(r"(\d+)p", quality.lower())
    if match:
        return int(match.group(1))
    return 0


def estimate_bandwidth(height):
    """
    M3U8 master playlist üçün təxmini bandwidth.
    """
    values = {
        144: 300000,
        240: 500000,
        360: 1000000,
        480: 1800000,
        540: 2500000,
        720: 4500000,
        1080: 8000000,
        1440: 16000000,
        2160: 30000000
    }

    return values.get(height, max(height * 7000, 500000))


def estimate_resolution(height):
    """
    YouTube-un standart 16:9 resolution-ları.
    """
    values = {
        144: (256, 144),
        240: (426, 240),
        360: (640, 360),
        480: (854, 480),
        540: (960, 540),
        720: (1280, 720),
        1080: (1920, 1080),
        1440: (2560, 1440),
        2160: (3840, 2160)
    }

    return values.get(height, (0, height))


def stream_url(stream):
    """
    Yeni Streamlink versiyalarında stream URL-ni götürür.
    """
    try:
        if hasattr(stream, "to_url"):
            return stream.to_url()

        if hasattr(stream, "url"):
            return stream.url

    except Exception:
        pass

    return None


def create_master(streams):
    """
    Mövcud video key-lərindən master m3u8 yaradır.
    """

    qualities = []

    for name, stream in streams.items():

        # best/worst ayrıca variant deyil
        if name.lower() in (
            "best",
            "worst",
            "audio",
            "audio_only",
            "audio_mp4",
            "audio_webm"
        ):
            continue

        height = get_height(name)

        if height <= 0:
            continue

        url = stream_url(stream)

        if not url:
            continue

        qualities.append({
            "name": name,
            "height": height,
            "url": url
        })

    # yüksək keyfiyyətdən aşağıya
    qualities.sort(
        key=lambda x: x["height"],
        reverse=True
    )

    # Eyni URL-ləri sil
    unique = []
    used_urls = set()

    for item in qualities:
        if item["url"] not in used_urls:
            unique.append(item)
            used_urls.add(item["url"])

    if not unique:
        return ""

    text = "#EXTM3U\n"
    text += "#EXT-X-VERSION:3\n"

    for item in unique:

        height = item["height"]
        width, height_res = estimate_resolution(height)
        bandwidth = estimate_bandwidth(height)

        text += (
            f'#EXT-X-STREAM-INF:'
            f'BANDWIDTH={bandwidth},'
            f'RESOLUTION={width}x{height_res},'
            f'NAME="{item["name"]}"\n'
        )

        text += item["url"] + "\n"

    return text


def create_best(streams):

    if "best" not in streams:
        return ""

    url = stream_url(streams["best"])

    if not url:
        return ""

    return (
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        f"{url}\n"
    )


def main():

    if len(sys.argv) < 2:
        print("Istifade:")
        print("python main.py config.json")
        sys.exit(1)

    config_file = sys.argv[1]

    try:
        with open(
            config_file,
            "r",
            encoding="utf-8"
        ) as f:
            config = json.load(f)

    except Exception as e:
        print(f"Config oxunmadi: {e}")
        sys.exit(1)

    folder_name = config["output"]["folder"]
    best_folder_name = config["output"]["bestFolder"]
    master_folder_name = config["output"]["masterFolder"]

    current_dir = os.getcwd()

    root_folder = os.path.join(
        current_dir,
        folder_name
    )

    best_folder = os.path.join(
        root_folder,
        best_folder_name
    )

    master_folder = os.path.join(
        root_folder,
        master_folder_name
    )

    os.makedirs(
        best_folder,
        exist_ok=True
    )

    os.makedirs(
        master_folder,
        exist_ok=True
    )

    session = streamlink.Streamlink()

    channels = config.get(
        "channels",
        []
    )

    for channel in channels:

        slug = channel.get("slug")
        url = channel.get("url")

        if not slug or not url:
            continue

        print()
        print("=" * 60)
        print(f"Kanal: {slug}")
        print(f"URL: {url}")

        master_file_path = os.path.join(
            master_folder,
            slug + ".m3u8"
        )

        best_file_path = os.path.join(
            best_folder,
            slug + ".m3u8"
        )

        try:

            streams = session.streams(url)

            if not streams:
                raise Exception(
                    "Streamlink heç bir yayım tapmadı"
                )

            print(
                "Tapilan streamler:",
                ", ".join(streams.keys())
            )

            master_text = create_master(
                streams
            )

            best_text = create_best(
                streams
            )

            if master_text:

                with open(
                    master_file_path,
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write(master_text)

                print(
                    f"MASTER yaradildi: "
                    f"{master_file_path}"
                )

            else:

                # Bəzən YouTube yalnız best qaytara bilər
                if best_text:
                    master_text = best_text

                    with open(
                        master_file_path,
                        "w",
                        encoding="utf-8"
                    ) as f:
                        f.write(master_text)

            if best_text:

                with open(
                    best_file_path,
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write(best_text)

                print(
                    f"BEST yaradildi: "
                    f"{best_file_path}"
                )

            else:
                raise Exception(
                    "Best stream tapilmadi"
                )

        except Exception as e:

            print(
                f"XETA [{slug}]: {e}"
            )

            # işləməyən köhnə faylları sil
            for filepath in (
                master_file_path,
                best_file_path
            ):

                try:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                except Exception:
                    pass


if __name__ == "__main__":
    main()
