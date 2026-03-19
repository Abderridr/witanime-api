import requests
from bs4 import BeautifulSoup
import re
import urllib3
from urllib.parse import urlencode

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WitAnimeScraper:
    def __init__(self):
        self.base_url = "https://witanime.you"
        # IMPORTANT: Replace this with your actual ScraperAPI key
        self.api_key = "70b7ccc8c48d7bf60ee80ab2ee12ff09" 
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    def _get_with_scraperapi(self, url, render=False):
        """Helper to call ScraperAPI. Only uses render when needed to save time."""
        params = {'api_key': self.api_key, 'url': url}
        if render:
            params['render'] = 'true'
            params['premium'] = 'true'
            params['wait_for_selector'] = 'a[href*="mediafire"], a[href*="workupload"], a[href*="gofile"]'
        
        api_url = f"http://api.scraperapi.com?{urlencode(params)}"
        try:
            return requests.get(api_url, timeout=110)
        except Exception as e:
            print(f"ScraperAPI Error: {e}")
            return None

    def get_latest_episodes(self):
        response = self._get_with_scraperapi(self.base_url, render=False)
        if not response or response.status_code != 200: return []
        soup = BeautifulSoup(response.text, 'html.parser')
        episodes = []
        for a in soup.find_all('a', href=True):
            if '/episode/' in a['href']:
                title = a.get('title') or (a.find('h3').text.strip() if a.find('h3') else a.text.strip())
                if title and "المزيد" not in title:
                    episodes.append({'title': title, 'url': a['href'] if a['href'].startswith('http') else f"{self.base_url}{a['href']}"})
        seen = set()
        return [e for e in episodes if not (e['url'] in seen or seen.add(e['url']))]

    def get_anime_details(self, anime_url):
        response = self._get_with_scraperapi(anime_url, render=False)
        if not response or response.status_code != 200: return None
        soup = BeautifulSoup(response.text, 'html.parser')
        details = {'title': soup.find('h1').text.strip() if soup.find('h1') else "Unknown", 'genres': list(set([a.text.strip() for a in soup.find_all('a', href=True) if '/anime-genre/' in a['href']]))}
        for el in soup.find_all(['li', 'span']):
            txt = el.text.strip()
            if ':' in txt:
                parts = txt.split(':', 1)
                k, v = parts[0].strip(), parts[1].strip()
                if 'بداية العرض' in k: details['year'] = v
                elif 'حالة الأنمي' in k: details['status'] = v
        return details

    def get_episode_data(self, episode_url):
        # Episode pages need rendering to show download links
        response = self._get_with_scraperapi(episode_url, render=True)
        if not response or response.status_code != 200: return None
        soup = BeautifulSoup(response.text, 'html.parser')
        data = {'watch_servers': [li.text.strip() for li in soup.find_all('li') if any(s in li.text.lower() for s in ['videa', 'streamwish', 'yonaplay', 'multi'])], 'download_links': []}
        
        # Aggressive search for download links
        # Look for all <a> tags and check their href and text
        current_quality = "Unknown"
        for element in soup.find_all(['h3', 'li', 'a', 'span', 'div']):
            text = element.text.strip()
            
            # Detect quality header
            if 'الجودة' in text:
                if 'SD' in text or 'المتوسطة' in text: current_quality = "SD"
                elif 'HD' in text or 'العالية' in text: current_quality = "HD"
                elif 'FHD' in text or 'الخارقة' in text: current_quality = "FHD"
            
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
        
        # Final fallback: just grab any link that looks like a download host from the entire page
        if not data['download_links']:
            for a in soup.find_all('a', href=True):
                href = a['href']
                if any(d in href.lower() for d in ['mediafire', 'workupload', 'gofile', 'mega.nz']):
                    data['download_links'].append({
                        'quality': "Unknown",
                        'host': a.text.strip()[:20] or "Download",
                        'url': href
                    })
        
        # Remove duplicates
        seen_urls = set()
        unique_links = []
        for link in data['download_links']:
            if link['url'] not in seen_urls:
                unique_links.append(link)
                seen_urls.add(link['url'])
        data['download_links'] = unique_links
        
        return data
