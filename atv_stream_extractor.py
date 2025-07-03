import requests
import re
import json
import os
import subprocess
from urllib.parse import urljoin, parse_qs
from datetime import datetime

# BeautifulSoup avtomatik quraşdırılması
try:
    from bs4 import BeautifulSoup
except ImportError:
    subprocess.run(['pip', 'install', 'beautifulsoup4'], check=True)
    from bs4 import BeautifulSoup

def get_secure_stream(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.atv.com.tr/'
        }
        
        # 1. Saytın əsas səhifəsini al
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # 2. BeautifulSoup ilə HTML təhlili
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 3. Video konteynerini tap
        video_container = soup.find('div', {'class': 'player-container'})
        if not video_container:
            raise Exception("Video konteyneri tapılmadı")
        
        # 4. Data-id və ya digər vacib atributları çıxart
        data_id = video_container.get('data-id', '')
        if not data_id:
            raise Exception("Video ID tapılmadı")
        
        # 5. API endpoint-ə müraciət et
        api_url = f"https://api.atv.com.tr/player/video/{data_id}"
        api_response = session.get(api_url, headers=headers)
        api_response.raise_for_status()
        stream_data = api_response.json()
        
        # 6. M3U8 linkini çıxart
        if 'stream_url' in stream_data:
            return stream_data['stream_url']
        elif 'hls_url' in stream_data:
            return stream_data['hls_url']
        else:
            raise Exception("M3U8 linki API cavabında tapılmadı")
            
    except Exception as e:
        print(f"Xəta ({url}): {str(e)}")
        return None

def main():
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    os.makedirs(config['output']['folder'], exist_ok=True)
    results = []
    
    for channel in config['channels']:
        if channel.get('enabled', True):
            print(f"\n🔍 {channel['name']} üçün m3u8 axtarılır...")
            
            # Xüsusi handler istifadə et
            if "atv.com.tr" in channel['url']:
                m3u8_url = get_secure_stream(channel['url'])
            else:
                m3u8_url = None
            
            if m3u8_url:
                filename = f"{channel['slug']}.m3u8"
                filepath = os.path.join(config['output']['folder'], filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(m3u8_url)
                
                print(f"✅ {channel['name']} üçün m3u8 linki tapıldı")
                results.append({
                    'channel': channel['name'],
                    'status': 'success',
                    'url': m3u8_url,
                    'updated_at': datetime.now().isoformat()
                })
            else:
                print(f"❌ {channel['name']} üçün m3u8 linki tapılmadı")
                results.append({
                    'channel': channel['name'],
                    'status': 'failed',
                    'updated_at': datetime.now().isoformat()
                })
    
    with open(os.path.join(config['output']['folder'], 'results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n✨ Əməliyyat tamamlandı!")

if __name__ == "__main__":
    main()
