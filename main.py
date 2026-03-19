from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
}

@app.route('/episode/<path:slug>')
def get_episode(slug):
    url = f'https://witanime.you/episode/{slug}/'
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    servers = []
    for link in soup.select('.server-link'):
        server_id = link.get('data-server-id')
        name = link.select_one('.ser').text.strip()
        servers.append({'id': server_id, 'name': name})
    
    return jsonify({'servers': servers, 'url': url})

@app.route('/search/<query>')
def search(query):
    url = f'https://witanime.you/?s={query}'
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    results = []
    for item in soup.select('.anime-card-container'):
        title = item.select_one('.anime-card-title')
        link = item.select_one('a')
        img = item.select_one('img')
        if title and link:
            results.append({
                'title': title.text.strip(),
                'url': link.get('href'),
                'image': img.get('src') if img else None
            })
    
    return jsonify({'results': results})

@app.route('/anime/<path:slug>')
def get_anime(slug):
    url = f'https://witanime.you/anime/{slug}/'
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    episodes = []
    for ep in soup.select('.all-episodes-list li a'):
        import base64
        onclick = ep.get('onclick', '')
        match = re.search(r"openEpisode\('(.+?)'\)", onclick)
        if match:
            decoded = base64.b64decode(match.group(1)).decode('utf-8')
            episodes.append({
                'title': ep.text.strip(),
                'url': decoded
            })
    
    return jsonify({'episodes': episodes})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
