import requests
from bs4 import BeautifulSoup
import re
import urllib3
from urllib.parse import urlencode

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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _get_with_scraperapi(self, url):
        """Helper to call ScraperAPI with advanced features to bypass Cloudflare."""
        params = {
            'api_key': self.api_key,
            'url': url,
            'render': 'true',  # Render JavaScript to bypass advanced challenges
            'premium': 'true'  # Use premium residential IPs
        }
        api_url = f"http://api.scraperapi.com?{urlencode(params)}"
        try:
            # We call the API directly instead of using proxies for better reliability with render=true
            response = requests.get(api_url, timeout=90)
            return response
        except Exception as e:
            print(f"ScraperAPI Error: {e}")
            return None

    def get_latest_episodes(self):
        """Scrapes the latest episodes using ScraperAPI advanced features."""
        try:
            response = self._get_with_scraperapi(self.base_url)
            if not response or response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            episodes = []
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/episode/' in href:
                    title = a.get('title') or (a.find('h3').text.strip() if a.find('h3') else a.text.strip())
                    if title and "المزيد من الحلقات" not in title:
                        full_url = href if href.startswith('http') else f"{self.base_url.rstrip('/')}/{href.lstrip('/')}"
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
            print(f"Error (Latest): {e}")
            return []

    def get_anime_details(self, anime_url):
        """Scrapes details for a specific anime using ScraperAPI advanced features."""
        try:
            response = self._get_with_scraperapi(anime_url)
            if not response or response.status_code != 200:
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
            
            # Improved info extraction for year, status, etc.
            for element in soup.find_all(['li', 'span', 'div']):
                text = element.text.strip()
                if ':' in text:
                    parts = text.split(':', 1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                    if 'بداية العرض' in key: details['year'] = val
                    elif 'حالة الأنمي' in key: details['status'] = val
                    elif 'عدد الحلقات' in key: details['episodes_count'] = val
                    elif 'مدة الحلقة' in key: details['duration'] = val
                    elif 'الموسم' in key: details['season'] = val
                    elif 'المصدر' in key: details['source'] = val
            
            desc_tag = soup.find('p', class_='anime-story') or soup.find('div', class_='anime-story')
            details['description'] = desc_tag.text.strip() if desc_tag else "No description available."
            
            mal_link = soup.find('a', href=re.compile(r'myanimelist\.net/anime/'))
            if mal_link:
                details['mal_url'] = mal_link['href']
                
            return details
        except Exception as e:
            print(f"Error (Details): {e}")
            return None

    def get_episode_data(self, episode_url):
        """Scrapes video servers and download links using ScraperAPI advanced features."""
        try:
            response = self._get_with_scraperapi(episode_url)
            if not response or response.status_code != 200:
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
            
            # Watch servers
            for li in soup.find_all('li'):
                text = li.text.lower()
                if any(s in text for s in ['videa', 'streamwish', 'yonaplay', 'multi', 'server']):
                    data['watch_servers'].append(li.text.strip())
            
            # Improved Download links extraction
            # The website groups links under quality headers
            current_quality = "Unknown"
            for element in soup.find_all(['h3', 'li', 'a', 'span']):
                text = element.text.strip()
                
                # Detect quality header
                if 'الجودة' in text:
                    if 'SD' in text or 'المتوسطة' in text: current_quality = "SD"
                    elif 'HD' in text or 'العالية' in text: current_quality = "HD"
                    elif 'FHD' in text or 'الخارقة' in text: current_quality = "FHD"
                    else: current_quality = text
                
                # Detect download link
                if element.name == 'a' and element.get('href'):
                    href = element['href']
                    link_text = element.text.strip().lower()
                    
                    # Check for common download hosts
                    if any(d in href.lower() for d in ['mediafire', 'workupload', 'mp4upload', 'gofile', 'hexload', 'mega.nz', 'drive.google']):
                        data['download_links'].append({
                            'quality': current_quality,
                            'host': link_text if len(link_text) < 30 else "Download",
                            'url': href
                        })
            
            # Final fallback: just grab any link that looks like a download host
            if not data['download_links']:
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if any(d in href.lower() for d in ['mediafire', 'workupload', 'gofile', 'mega.nz']):
                        data['download_links'].append({
                            'quality': "Unknown",
                            'host': a.text.strip()[:20] or "Download",
                            'url': href
                        })
            
            return data
        except Exception as e:
            print(f"Error (Episode): {e}")
            return None

if __name__ == "__main__":
    scraper = WitAnimeScraper()
    print("Testing latest episodes with ScraperAPI Advanced...")
    latest = scraper.get_latest_episodes()
    print(f"Found {len(latest)} episodes.")
    for ep in latest[:5]:
        print(f"- {ep['title']}: {ep['url']}")
