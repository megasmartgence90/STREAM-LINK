import json
import os
import subprocess
import time
from datetime import datetime
import yt_dlp

# Config dosyasını yükle
with open('config.json', 'r') as f:
    config = json.load(f)

# Çıktı klasörünü oluştur
os.makedirs(config['output_folder'], exist_ok=True)

def get_live_streams():
    live_streams = []
    for url in config['youtube_links']:
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'forceurl': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info.get('is_live', False):
                    live_streams.append({
                        'url': url,
                        'title': info.get('title', 'untitled'),
                        'stream_url': info.get('url')
                    })
        except Exception as e:
            print(f"Error checking {url}: {str(e)}")
    return live_streams

def record_stream(stream_info):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in stream_info['title'] if c.isalnum() or c in (' ', '_')).rstrip()
    output_filename = f"{safe_title}_{now}.m3u8"
    output_path = os.path.join(config['output_folder'], output_filename)
    
    ffmpeg_cmd = [
        config['ffmpeg_path'],
        '-i', stream_info['stream_url'],
        '-c', 'copy',
        '-f', 'hls',
        '-hls_time', '6',
        '-hls_list_size', '0',
        '-hls_segment_filename', os.path.join(config['output_folder'], f"{safe_title}_{now}_%03d.ts"),
        '-t', str(config['max_duration']),
        output_path
    ]
    
    print(f"Recording {stream_info['title']} to {output_path}")
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"Finished recording {stream_info['title']}")
    except subprocess.CalledProcessError as e:
        print(f"Recording failed for {stream_info['title']}: {str(e)}")

def main():
    print("YouTube Live Recorder started...")
    while True:
        live_streams = get_live_streams()
        if live_streams:
            for stream in live_streams:
                record_stream(stream)
        else:
            print(f"No live streams found. Checking again in {config['check_interval']} seconds.")
        
        time.sleep(config['check_interval'])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Script terminated by user")
