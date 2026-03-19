import requests
from bs4 import BeautifulSoup
import json
import time
import re
import sys

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
            response = requests.get(self.base_url, headers=self.headers)
            if response.status_code != 200:
                print(f"Failed to fetch homepage: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            episodes = []
            
            # Find all episode links
            for a in soup.find_all('a', href=True):
                if '/episode/' in a['href']:
                    title = a.get('title') or a.text.strip()
                    if title:
                        episodes.append({
                            'title': title,
                            'url': a['href']
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
            response = requests.get(anime_url, headers=self.headers)
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
            
            # Extract info from list items
            for li in soup.find_all('li'):
                text = li.text.strip()
                if 'بداية العرض:' in text:
                    details['year'] = text.replace('بداية العرض:', '').strip()
                elif 'حالة الأنمي:' in text:
                    details['status'] = text.replace('حالة الأنمي:', '').strip()
                elif 'عدد الحلقات:' in text:
                    details['episodes_count'] = text.replace('عدد الحلقات:', '').strip()
                elif 'مدة الحلقة:' in text:
                    details['duration'] = text.replace('مدة الحلقة:', '').strip()
                elif 'الموسم:' in text:
                    details['season'] = text.replace('الموسم:', '').strip()
                elif 'المصدر:' in text:
                    details['source'] = text.replace('المصدر:', '').strip()
            
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
            response = requests.get(episode_url, headers=self.headers)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            data = {
                'title': soup.find('h3').text.strip() if soup.find('h3') else "Unknown",
                'watch_servers': [],
                'download_links': []
            }
            
            # Watch servers
            for li in soup.find_all('li'):
                if any(s in li.text.lower() for s in ['videa', 'streamwish', 'yonaplay', 'multi']):
                    data['watch_servers'].append(li.text.strip())
            
            # Download links
            current_quality = "Unknown"
            for element in soup.find_all(['h3', 'li', 'a']):
                text = element.text.strip()
                if 'الجودة' in text:
                    current_quality = text
                
                if element.name == 'a' and element.get('href'):
                    href = element['href']
                    if any(d in href for d in ['mediafire', 'workupload', 'mp4upload', 'gofile', 'hexload']):
                        data['download_links'].append({
                            'quality': current_quality,
                            'host': text,
                            'url': href
                        })
            
            return data
        except Exception as e:
            print(f"Error scraping episode data: {e}")
            return None

def main():
    scraper = WitAnimeScraper()
    
    # Example usage
    print("Fetching latest episodes...")
    latest = scraper.get_latest_episodes()
    
    results = []
    for ep in latest[:5]:
        print(f"Processing: {ep['title']}")
        ep_data = scraper.get_episode_data(ep['url'])
        if ep_data:
            results.append({
                'episode_title': ep['title'],
                'episode_url': ep['url'],
                'data': ep_data
            })
        time.sleep(1) # Be polite to the server
        
    # Save results to a file
    with open('witanime_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nScraping complete. Results saved to witanime_results.json")

if __name__ == "__main__":
    main()
