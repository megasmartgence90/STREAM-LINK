import requests
import re
import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime

def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def extract_m3u8_with_selenium(url, driver):
    try:
        driver.get(url)
        time.sleep(5)  # JavaScript-in yüklənməsini gözlə
        
        # Network trafikini analiz et
        performance_log = driver.get_log('performance')
        for entry in performance_log:
            if '.m3u8' in str(entry):
                matches = re.findall(r'https?://[^\s"]+\.m3u8', str(entry))
                if matches:
                    return matches[0]
        
        # Əgər network log-da tapılmasa, saytın mənbə koduna bax
        page_source = driver.page_source
        source_matches = re.findall(r'(https?://[^\s"\']+\.m3u8)', page_source)
        if source_matches:
            return source_matches[0]
            
        return None
    except Exception as e:
        print(f"Selenium xətası: {str(e)}")
        return None

def get_stream_url(channel):
    try:
        # Əvvəlcə Selenium ilə cəhd edək
        driver = setup_selenium()
        m3u8_url = extract_m3u8_with_selenium(channel['url'], driver)
        driver.quit()
        
        if m3u8_url:
            return m3u8_url
        
        # Əgər Selenium işləməsə, API-ə müraciət edək
        if "api_endpoint" in channel:
            response = requests.get(channel['api_endpoint'], timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('stream_url') or data.get('hls_url')
        
        return None
    except Exception as e:
        print(f"Ümumi xəta ({channel['name']}): {str(e)}")
        return None

def main():
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    os.makedirs(config['output']['folder'], exist_ok=True)
    results = []
    
    for channel in config['channels']:
        if not channel.get('enabled', True):
            continue
            
        print(f"\n🔍 {channel['name']} üçün m3u8 axtarılır...")
        start_time = time.time()
        
        m3u8_url = get_stream_url(channel)
        
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
                'updated_at': datetime.now().isoformat(),
                'duration': round(time.time() - start_time, 2)
            })
        else:
            print(f"❌ {channel['name']} üçün m3u8 linki tapılmadı")
            results.append({
                'channel': channel['name'],
                'status': 'failed',
                'updated_at': datetime.now().isoformat(),
                'duration': round(time.time() - start_time, 2)
            })
    
    with open(os.path.join(config['output']['folder'], 'results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n✨ Əməliyyat tamamlandı!")

if __name__ == "__main__":
    main()
