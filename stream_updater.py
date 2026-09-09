import streamlink
import sys
import os
import json
import re
import time


# ============================================================
# KEYFİYYƏT
# ============================================================

def get_height(quality):
    """
    1080p60 -> 1080
    720p -> 720
    360p -> 360
    """

    if not quality:
        return 0

    match = re.search(r"(\d+)\s*p", str(quality).lower())

    if match:
        return int(match.group(1))

    return 0


def estimate_bandwidth(height):

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

    return values.get(
        height,
        max(height * 7000, 500000)
    )


def estimate_resolution(height):

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

    return values.get(
        height,
        (0, height)
    )


# ============================================================
# STREAM URL
# ============================================================

def get_stream_url(stream):

    if stream is None:
        return None

    # Yeni Streamlink
    try:
        if hasattr(stream, "to_url"):

            url = stream.to_url()

            if url:
                return url

    except Exception:
        pass

    # Köhnə Streamlink
    try:
        if hasattr(stream, "url"):

            url = stream.url

            if url:
                return url

    except Exception:
        pass

    return None


# ============================================================
# STREAM KEY NORMALIZASIYA
# ============================================================

def normalize_quality(name):

    if not name:
        return ""

    return str(name).lower().strip()


def is_quality_stream(name):

    name = normalize_quality(name)

    ignored = {
        "best",
        "worst",
        "audio",
        "audio_only",
        "audio_mp4",
        "audio_webm",
        "video"
    }

    if name in ignored:
        return False

    return get_height(name) > 0


# ============================================================
# MASTER M3U8
# ============================================================

def create_master(streams):

    qualities = []

    for name, stream in streams.items():

        if not is_quality_stream(name):
            continue

        height = get_height(name)

        if height <= 0:
            continue

        url = get_stream_url(stream)

        if not url:
            continue

        qualities.append({
            "name": str(name),
            "height": height,
            "url": url
        })

    # Yüksək keyfiyyətdən aşağı
    qualities.sort(
        key=lambda x: x["height"],
        reverse=True
    )

    # Eyni URL-ləri sil
    unique = []
    used_urls = set()

    for item in qualities:

        if item["url"] in used_urls:
            continue

        used_urls.add(item["url"])
        unique.append(item)

    if not unique:
        return ""

    output = [
        "#EXTM3U",
        "#EXT-X-VERSION:3"
    ]

    for item in unique:

        height = item["height"]

        width, height_res = estimate_resolution(
            height
        )

        bandwidth = estimate_bandwidth(
            height
        )

        output.append(
            f'#EXT-X-STREAM-INF:'
            f'BANDWIDTH={bandwidth},'
            f'RESOLUTION={width}x{height_res},'
            f'NAME="{item["name"]}"'
        )

        output.append(
            item["url"]
        )

    return "\n".join(output) + "\n"


# ============================================================
# BEST
# ============================================================

def create_best(streams):

    # Birbaşa best varsa
    if "best" in streams:

        url = get_stream_url(
            streams["best"]
        )

        if url:

            return (
                "#EXTM3U\n"
                "#EXT-X-VERSION:3\n"
                f"{url}\n"
            )

    # best yoxdursa keyfiyyətlərdən ən yüksək olanı seç
    candidates = []

    for name, stream in streams.items():

        if not is_quality_stream(name):
            continue

        height = get_height(name)

        url = get_stream_url(stream)

        if not url:
            continue

        candidates.append({
            "height": height,
            "url": url
        })

    if not candidates:
        return ""

    candidates.sort(
        key=lambda x: x["height"],
        reverse=True
    )

    url = candidates[0]["url"]

    return (
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        f"{url}\n"
    )


# ============================================================
# STREAM TAPMA
# ============================================================

def get_streams(session, url):

    print("Stream axtarılır...")

    try:

        streams = session.streams(url)

        if streams:
            return streams

    except Exception as e:

        print(
            f"Normal Streamlink sorğusu uğursuz oldu: {e}"
        )

    return {}


# ============================================================
# FAYL YAZ
# ============================================================

def write_file(path, content):

    temp_path = path + ".tmp"

    with open(
        temp_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(content)

    # Fayl tam yazıldıqdan sonra dəyiş
    os.replace(
        temp_path,
        path
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) < 2:

        print(
            "Istifade:"
        )

        print(
            "python main.py config.json"
        )

        sys.exit(1)

    config_file = sys.argv[1]

    # --------------------------------------------------------
    # CONFIG
    # --------------------------------------------------------

    try:

        with open(
            config_file,
            "r",
            encoding="utf-8"
        ) as f:

            config = json.load(f)

    except Exception as e:

        print(
            f"Config oxunmadi: {e}"
        )

        sys.exit(1)

    # --------------------------------------------------------
    # QOVLUQLAR
    # --------------------------------------------------------

    output_config = config.get(
        "output",
        {}
    )

    folder_name = output_config.get(
        "folder",
        "streams"
    )

    best_folder_name = output_config.get(
        "bestFolder",
        "best"
    )

    master_folder_name = output_config.get(
        "masterFolder",
        "master"
    )

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

    # --------------------------------------------------------
    # STREAMLINK SESSION
    # --------------------------------------------------------

    session = streamlink.Streamlink()

    # HTTP başlıqları
    try:

        session.set_option(
            "http-headers",
            {
                "User-Agent":
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/131.0 Safari/537.36"
            }
        )

    except Exception:
        pass

    # --------------------------------------------------------
    # CHANNELS
    # --------------------------------------------------------

    channels = config.get(
        "channels",
        []
    )

    print()
    print(
        "=" * 70
    )
    print(
        f"Toplam kanal: {len(channels)}"
    )
    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # KANALLAR
    # --------------------------------------------------------

    for index, channel in enumerate(
        channels,
        start=1
    ):

        slug = channel.get(
            "slug"
        )

        url = channel.get(
            "url"
        )

        if not slug or not url:
            continue

        print()
        print(
            "=" * 70
        )

        print(
            f"[{index}/{len(channels)}] "
            f"Kanal: {slug}"
        )

        print(
            f"URL: {url}"
        )

        print(
            "=" * 70
        )

        master_file_path = os.path.join(
            master_folder,
            slug + ".m3u8"
        )

        best_file_path = os.path.join(
            best_folder,
            slug + ".m3u8"
        )

        try:

            # ------------------------------------------------
            # STREAMLƏRİ TAP
            # ------------------------------------------------

            streams = get_streams(
                session,
                url
            )

            if not streams:

                raise Exception(
                    "Streamlink heç bir yayım tapmadı"
                )

            # ------------------------------------------------
            # STREAMLƏR
            # ------------------------------------------------

            stream_names = list(
                streams.keys()
            )

            print(
                "Tapılan streamlər:"
            )

            print(
                ", ".join(
                    map(
                        str,
                        stream_names
                    )
                )
            )

            # ------------------------------------------------
            # BEST
            # ------------------------------------------------

            best_text = create_best(
                streams
            )

            # ------------------------------------------------
            # MASTER
            # ------------------------------------------------

            master_text = create_master(
                streams
            )

            # ------------------------------------------------
            # MASTER YOXDURSA BEST İSTİFADƏ ET
            # ------------------------------------------------

            if not master_text and best_text:

                master_text = best_text

                print(
                    "Master üçün BEST stream istifadə olunur."
                )

            # ------------------------------------------------
            # FAYLLARI YAZ
            # ------------------------------------------------

            if master_text:

                write_file(
                    master_file_path,
                    master_text
                )

                print(
                    f"MASTER yaradıldı: "
                    f"{master_file_path}"
                )

            if best_text:

                write_file(
                    best_file_path,
                    best_text
                )

                print(
                    f"BEST yaradıldı: "
                    f"{best_file_path}"
                )

            # ------------------------------------------------
            # HEÇ BİRİ YOXDUR
            # ------------------------------------------------

            if not master_text and not best_text:

                raise Exception(
                    "İşlək HLS URL tapılmadı"
                )

            print(
                "OK"
            )

        except Exception as e:

            print()
            print(
                f"XƏTA [{slug}]: {e}"
            )

            # ------------------------------------------------
            # KÖHNƏ FAYLLARI SİLMƏ
            # ------------------------------------------------
            # Burada köhnə faylı dərhal silmirik.
            # Beləliklə müvəqqəti YouTube/API xətasında
            # işləyən əvvəlki link saxlanılır.

            print(
                "Köhnə playlist saxlanıldı."
            )

        # Serveri yükləməmək üçün kiçik fasilə
        time.sleep(1)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
