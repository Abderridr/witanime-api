import requests
from bs4 import BeautifulSoup
import re

class WitAnimeScraper:
    def __init__(self):
        self.base_url = "https://witanime.you"
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64 ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    def get_latest_episodes(self):
        try:
            response = requests.get(self.base_url, headers=self.headers)
            if response.status_code != 200: return []
            soup = BeautifulSoup(response.text, 'html.parser')
            episodes = []
            for a in soup.find_all('a', href=True):
                if '/episode/' in a['href']:
                    title = a.get('title') or (a.find('h3').text.strip() if a.find('h3') else a.text.strip())
                    if title:
                        episodes.append({'title': title, 'url': a['href'] if a['href'].startswith('http' ) else f"{self.base_url}{a['href']}"})
            seen = set()
            return [e for e in episodes if not (e['url'] in seen or seen.add(e['url']))]
        except: return []

    def get_anime_details(self, anime_url):
        try:
            res = requests.get(anime_url, headers=self.headers)
            if res.status_code != 200: return None
            soup = BeautifulSoup(res.text, 'html.parser')
            details = {'title': soup.find('h1').text.strip() if soup.find('h1') else "Unknown", 'genres': list(set([a.text.strip() for a in soup.find_all('a', href=True) if '/anime-genre/' in a['href']]))}
            for el in soup.find_all(['li', 'span']):
                txt = el.text.strip()
                if 'بداية العرض:' in txt: details['year'] = txt.split(':')[-1].strip()
                elif 'حالة الأنمي:' in txt: details['status'] = txt.split(':')[-1].strip()
            return details
        except: return None

    def get_episode_data(self, episode_url):
        try:
            res = requests.get(episode_url, headers=self.headers)
            if res.status_code != 200: return None
            soup = BeautifulSoup(res.text, 'html.parser')
            data = {'watch_servers': [li.text.strip() for li in soup.find_all('li') if any(s in li.text.lower() for s in ['videa', 'streamwish', 'yonaplay', 'multi'])], 'download_links': []}
            q = "Unknown"
            for el in soup.find_all(['h3', 'li', 'a']):
                if 'الجودة' in el.text: q = el.text.strip()
                if el.name == 'a' and any(d in el.get('href', '').lower() for d in ['mediafire', 'workupload', 'gofile']):
                    data['download_links'].append({'quality': q, 'url': el['href']})
            return data
        except: return None
