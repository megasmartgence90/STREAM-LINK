import requests
import json
import os
from datetime import datetime

def generate_m3u8_content(channel_name, stream_url, bandwidth=2000000, resolution="1920x1080"):
    return f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH={bandwidth},CODECS="",RESOLUTION={resolution}
{stream_url}"""

def main():
    # Konfiqurasiya faylını oxu
    with open('channels.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Çıxış qovluğunu yarat
    output_dir = config['output']['folder']
    os.makedirs(output_dir, exist_ok=True)
    
    # Master playlist üçün ümumi məlumat
    master_playlist = "#EXTM3U\n"
    
    for channel in config['channels']:
        if not channel.get('enabled', True):
            continue
            
        print(f"\n🔍 {channel['name']} işlənir...")
        
        try:
            # Burada real stream URL-ni alın (nümunə üçün konfiqdan götürürük)
            stream_url = channel.get('https://www.atv.com.tr/canli-yayin', '')
            
            if not stream_url:
                # Əgər URL yoxdursa, saytdan çıxarmaq üçün funksiya çağırın
                stream_url = get_stream_url(channel['url'])
            
            if stream_url:
                # Hər kanal üçün ayrı fayl yarat
                content = generate_m3u8_content(
                    channel['name'],
                    stream_url,
                    channel.get('bandwidth', 2000000),
                    channel.get('resolution', '1920x1080')
                )
                
                filename = f"{channel['slug']}.m3u8"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Master playlist-ə əlavə et
                master_playlist += f"#EXTINF:-1 tvg-name=\"{channel['name']}\",{channel['name']}\n{filename}\n"
                
                print(f"✅ {channel['name']} uğurla yaradıldı")
            else:
                print(f"❌ {channel['name']} üçün stream URL tapılmadı")
                
        except Exception as e:
            print(f"⚠️ {channel['name']} xətası: {str(e)}")
    
    # Master playlist faylını yarat
    with open(os.path.join(output_dir, 'playlist.m3u8'), 'w', encoding='utf-8') as f:
        f.write(master_playlist)
    
    print("\n✨ Bütün kanallar uğurla yaradıldı")

def get_stream_url(channel_url):
    """Bu funksiya real tətbiqdə saytdan stream URL-ni çıxarmalıdır"""
    # Burada sizin parsing məntiqinizi əlavə edin
    # Nümunə üçün:
    if "atv.com.tr" in channel_url:
        return "https://example.com/atv_stream.m3u8"
    elif "showtv.com.tr" in channel_url:
        return "https://example.com/showtv_stream.m3u8"
    return None

if __name__ == "__main__":
    main()
