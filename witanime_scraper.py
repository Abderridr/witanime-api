import requests
from bs4 import BeautifulSoup
import re

class WitAnimeScraper:
    def __init__(self):
        self.base_url = "https://witanime.you"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def get_latest_episodes(self):
        """Scrapes the latest episodes from the homepage."""
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                print(f"Failed to fetch homepage: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            episodes = []
            
            # The website uses <a> tags with title and href containing '/episode/'
            # We'll look for these specifically
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/episode/' in href:
                    # Title is often in the 'title' attribute or nested text
                    title = a.get('title') or a.text.strip()
                    
                    if title:
                        # Ensure absolute URL
                        full_url = href if href.startswith('http') else f"{self.base_url.rstrip('/')}/{href.lstrip('/')}"
                        episodes.append({
                            'title': title,
                            'url': full_url
                        })
            
            # Remove duplicates while preserving order
            seen = set()
            unique_episodes = []
            for ep in episodes:
                if ep['url'] not in seen:
                    unique_episodes.append(ep)
                    seen.add(ep['url'])
                    
            return unique_episodes
        except Exception as e:
            print(f"Error scraping latest episodes: {e}")
            return []

    def get_anime_details(self, anime_url):
        """Scrapes details for a specific anime."""
        try:
            response = requests.get(anime_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            details = {}
            
            # Extract title
            title_tag = soup.find('h1')
            details['title'] = title_tag.text.strip() if title_tag else "Unknown"
            
            # Extract genres
            genres = []
            for a in soup.find_all('a', href=True):
                if '/anime-genre/' in a['href']:
                    genres.append(a.text.strip())
            details['genres'] = list(set(genres))
            
            # Extract info from list items or spans
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
            
            # Extract MAL link
            mal_link = soup.find('a', href=re.compile(r'myanimelist\.net/anime/'))
            if mal_link:
                details['mal_url'] = mal_link['href']
                
            return details
        except Exception as e:
            print(f"Error scraping anime details: {e}")
            return None

    def get_episode_data(self, episode_url):
        """Scrapes video servers and download links for an episode."""
        try:
            response = requests.get(episode_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            data = {
                'title': "Unknown",
                'watch_servers': [],
                'download_links': []
            }
            
            # Extract title
            h3_title = soup.find('h3')
            if h3_title:
                data['title'] = h3_title.text.strip()
            
            # Watch servers
            for li in soup.find_all('li'):
                text = li.text.lower()
                if any(s in text for s in ['videa', 'streamwish', 'yonaplay', 'multi', 'server']):
                    data['watch_servers'].append(li.text.strip())
            
            # Download links
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
            print(f"Error scraping episode data: {e}")
            return None

if __name__ == "__main__":
    scraper = WitAnimeScraper()
    print("Testing latest episodes...")
    latest = scraper.get_latest_episodes()
    print(f"Found {len(latest)} episodes.")
    for ep in latest[:5]:
        print(f"- {ep['title']}: {ep['url']}")
