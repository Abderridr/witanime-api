import requests
from bs4 import BeautifulSoup
import re
import urllib3

# Disable SSL warnings for proxy use
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WitAnimeScraper:
    def __init__(self):
        self.base_url = "https://witanime.you"
        # IMPORTANT: Replace this with your actual ScraperAPI key
        self.api_key = "70b7ccc8c48d7bf60ee80ab2ee12ff09" 
        
        # ScraperAPI Proxy Configuration
        self.proxy_url = f"http://scraperapi:{self.api_key}@proxy-server.scraperapi.com:8001"
        self.proxies = {
            "http": self.proxy_url,
            "https": self.proxy_url
        }
        
        # Headers for compatibility with main.py
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64 ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_latest_episodes(self):
        """Scrapes the latest episodes using ScraperAPI to bypass Cloudflare."""
        try:
            # We use the proxy to bypass the "Just a moment" screen
            response = requests.get(self.base_url, proxies=self.proxies, verify=False, timeout=60)
            if response.status_code != 200:
                print(f"Failed to fetch homepage: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            episodes = []
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/episode/' in href:
                    title = a.get('title') or (a.find('h3').text.strip() if a.find('h3') else a.text.strip())
                    if title:
                        full_url = href if href.startswith('http' ) else f"{self.base_url.rstrip('/')}/{href.lstrip('/')}"
                        episodes.append({
                            'title': title,
                            'url': full_url
                        })
            
            seen = set()
            unique_episodes = []
            for ep in episodes:
                if ep['url'] not in seen:
                    unique_episodes.append(ep)
                    seen.add(ep['url'])
                    
            return unique_episodes
        except Exception as e:
            print(f"Proxy Error (Latest): {e}")
            return []

    def get_anime_details(self, anime_url):
        """Scrapes details for a specific anime using ScraperAPI."""
        try:
            response = requests.get(anime_url, proxies=self.proxies, verify=False, timeout=60)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            details = {}
            
            title_tag = soup.find('h1')
            details['title'] = title_tag.text.strip() if title_tag else "Unknown"
            
            genres = []
            for a in soup.find_all('a', href=True):
                if '/anime-genre/' in a['href']:
                    genres.append(a.text.strip())
            details['genres'] = list(set(genres))
            
            for element in soup.find_all(['li', 'span', 'div']):
                text = element.text.strip()
                if 'بداية العرض:' in text:
                    details['year'] = text.split(':')[-1].strip()
                elif 'حالة الأنمي:' in text:
                    details['status'] = text.split(':')[-1].strip()
                elif 'عدد الحلقات:' in text:
                    details['episodes_count'] = text.split(':')[-1].strip()
                elif 'مدة الحلقة:' in text:
                    details['duration'] = text.split(':')[-1].strip()
                elif 'الموسم:' in text:
                    details['season'] = text.split(':')[-1].strip()
                elif 'المصدر:' in text:
                    details['source'] = text.split(':')[-1].strip()
            
            mal_link = soup.find('a', href=re.compile(r'myanimelist\.net/anime/'))
            if mal_link:
                details['mal_url'] = mal_link['href']
                
            return details
        except Exception as e:
            print(f"Proxy Error (Details): {e}")
            return None

    def get_episode_data(self, episode_url):
        """Scrapes video servers and download links using ScraperAPI."""
        try:
            response = requests.get(episode_url, proxies=self.proxies, verify=False, timeout=60)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            data = {
                'title': "Unknown",
                'watch_servers': [],
                'download_links': []
            }
            
            h3_title = soup.find('h3')
            if h3_title:
                data['title'] = h3_title.text.strip()
            
            for li in soup.find_all('li'):
                text = li.text.lower()
                if any(s in text for s in ['videa', 'streamwish', 'yonaplay', 'multi', 'server']):
                    data['watch_servers'].append(li.text.strip())
            
            current_quality = "Unknown"
            for element in soup.find_all(['h3', 'li', 'a', 'span']):
                text = element.text.strip()
                if 'الجودة' in text:
                    current_quality = text
                
                if element.name == 'a' and element.get('href'):
                    href = element['href']
                    if any(d in href.lower() for d in ['mediafire', 'workupload', 'mp4upload', 'gofile', 'hexload', 'mega.nz']):
                        data['download_links'].append({
                            'quality': current_quality,
                            'host': text if len(text) < 20 else "Download",
                            'url': href
                        })
            
            return data
        except Exception as e:
            print(f"Proxy Error (Episode): {e}")
            return None

if __name__ == "__main__":
    scraper = WitAnimeScraper()
    print("Testing latest episodes with ScraperAPI...")
    latest = scraper.get_latest_episodes()
    print(f"Found {len(latest)} episodes.")
    for ep in latest[:5]:
        print(f"- {ep['title']}: {ep['url']}")
