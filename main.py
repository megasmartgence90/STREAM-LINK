import requests
from bs4 import BeautifulSoup
import re

def get_m3u8_links(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        m3u8_links = []
        for script in soup.find_all('script'):
            if script.string:
                found_links = re.findall(r'https?://[^\s]+\.m3u8', script.string)
                m3u8_links.extend(found_links)
        return m3u8_links
    except Exception as e:
        print(f"Error: {e}")
        return []

def main():
    url = "https://www.nowtv.com.tr/canli-yayin"
    m3u8_links = get_m3u8_links(url)
    if m3u8_links:
        print("Found m3u8 links:")
        for link in m3u8_links:
            print(link)
    else:
        print("No m3u8 links found.")

if __name__ == "__main__":
    main()
```
