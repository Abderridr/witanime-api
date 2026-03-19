import cloudscraper
from bs4 import BeautifulSoup
import re

class WitAnimeScraper:
    def __init__(self):
        self.base_url = "https://witanime.you"
        # cloudscraper will handle the headers and Cloudflare bypass
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
         )

    def get_latest_episodes(self):
        try:
            response = self.scraper.get(self.base_url, timeout=15)
            if response.status_code != 200: return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            episodes = []
            for a in soup.find_all('a', href=True):
                if '/episode/' in a['href']:
                    title = a.get('title') or (a.find('h3').text.strip() if a.find('h3') else a.text.strip())
                    if title:
                        episodes.append({
                            'title': title, 
                            'url': a['href'] if a['href'].startswith('http' ) else f"{self.base_url}{a['href']}"
                        })
            seen = set()
            return [e for e in episodes if not (e['url'] in seen or seen.add(e['url']))]
        except Exception as e:
            print(f"Scraper Error: {e}")
            return []

    # ... (rest of the methods updated to use self.scraper.get)
