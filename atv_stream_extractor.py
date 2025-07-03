import requests
import re
import json
import os
from urllib.parse import urljoin

def extract_m3u8(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 1. Ana səhifəni al
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 2. Video iframe və ya script tag-larını tap
        iframe_match = re.search(r'<iframe[^>]+src="([^"]+)"', response.text)
        script_match = re.search(r'<script[^>]+src="([^"]+)"', response.text)
        
        # 3. Video player URL-ni tap
        player_url = None
        if iframe_match:
            player_url = iframe_match.group(1)
            if not player_url.startswith('http'):
                player_url = urljoin(url, player_url)
        elif script_match:
            player_url = script_match.group(1)
        
        if not player_url:
            raise Exception("Video player URL tapılmadı")
        
        # 4. Player səhifəsini al
        player_response = requests.get(player_url, headers=headers, timeout=10)
        player_response.raise_for_status()
        
        # 5. M3U8 linkini çıxart
        m3u8_pattern = r'(https?://[^\s"\']+\.m3u8)'
        m3u8_matches = re.findall(m3u8_pattern, player_response.text)
        
        if not m3u8_matches:
            raise Exception("M3U8 linki tapılmadı")
        
        return m3u8_matches[0]
        
    except Exception as e:
        print(f"Xəta: {str(e)}")
        return None

def main():
    # Konfiqurasiya faylını oxu
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Çıxış qovluğunu yarat
    os.makedirs(config['output']['folder'], exist_ok=True)
    
    # Bütün kanalları emal et
    results = []
    for channel in config['channels']:
        if channel.get('enabled', True):
            print(f"\n🔍 {channel['name']} üçün m3u8 axtarılır...")
            m3u8_url = extract_m3u8(channel['url'])
            
            if m3u8_url:
                # Fayl yolu
                filename = f"{channel['slug']}.m3u8"
                filepath = os.path.join(config['output']['folder'], filename)
                
                # Fayla yaz
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(m3u8_url)
                
                print(f"✅ {channel['name']} üçün m3u8 linki tapıldı və saxlanıldı")
                results.append({
                    'channel': channel['name'],
                    'status': 'success',
                    'm3u8_url': m3u8_url,
                    'file': filename
                })
            else:
                print(f"❌ {channel['name']} üçün m3u8 linki tapılmadı")
                results.append({
                    'channel': channel['name'],
                    'status': 'failed'
                })
    
    # Nəticələri yadda saxla
    with open(os.path.join(config['output']['folder'], 'results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n✨ Əməliyyat tamamlandı!")

if __name__ == "__main__":
    main()
