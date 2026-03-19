from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import re
import json

app = Flask(__name__)

BASE_URL = "https://w1.anime4up.rest"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
    'Referer': 'https://w1.anime4up.rest/',
}

OKRU_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://ok.ru/',
}

@app.route('/test')
def test():
    res = requests.get(BASE_URL, headers=HEADERS)
    return jsonify({'status': res.status_code, 'length': len(res.text)})

@app.route('/search/<query>')
def search(query):
    url = f'{BASE_URL}/?s={query}'
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')
    results = []
    for item in soup.select('.anime-card-container'):
        title = item.select_one('.anime-card-title')
        link = item.select_one('a')
        img = item.select_one('img')
        if title and link:
            slug = link.get('href', '').replace(BASE_URL + '/anime/', '').strip('/')
            results.append({
                'title': title.text.strip(),
                'url': link.get('href'),
                'slug': slug,
                'image': img.get('src') if img else None
            })
    return jsonify({'results': results, 'status': res.status_code})

@app.route('/anime/<path:slug>')
def get_anime(slug):
    url = f'{BASE_URL}/anime/{slug}/'
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')

    episodes = []
    seen = set()
    for ep in soup.select('a[href*="episode"]'):
        ep_url = ep.get('href', '')
        ep_title = ep.text.strip()
        if ep_url and ep_title and 'الحلقة' in ep_title and ep_url not in seen:
            seen.add(ep_url)
            episodes.append({
                'title': ep_title,
                'url': ep_url
            })

    title = soup.select_one('.anime-details-title h1') or soup.select_one('h1')
    cover = soup.select_one('.anime-cover img') or soup.select_one('.img-responsive')
    desc = soup.select_one('.anime-story') or soup.select_one('.story')

    return jsonify({
        'title': title.text.strip() if title else '',
        'cover': cover.get('src') if cover else '',
        'description': desc.text.strip() if desc else '',
        'episodes': episodes,
        'status': res.status_code
    })

@app.route('/episode/<path:slug>')
def get_episode(slug):
    url = f'{BASE_URL}/episode/{slug}/'
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')

    iframes = []
    seen = set()
    for i in soup.select('iframe'):
        src = i.get('src', '')
        if src and src not in seen:
            seen.add(src)
            domain = src.split('/')[2] if len(src.split('/')) > 2 else src
            iframes.append({
                'url': src,
                'server': domain
            })

    return jsonify({
        'iframes': iframes,
        'url': url,
        'status': res.status_code
    })

@app.route('/okru')
def get_okru():
    video_url = requests.utils.unquote(requests.compat.urlparse(
        requests.Request('GET', 'http://x.com', params={'url': ''}).prepare().url
    ).query.split('url=')[-1]) if False else None

    from flask import request
    video_url = request.args.get('url', '')
    if not video_url:
        return jsonify({'error': 'url parameter required'})

    res = requests.get(video_url, headers=OKRU_HEADERS)
    
    match = re.search(r'"videos":\[(.*?)\]', res.text)
    if not match:
        match = re.search(r'var videoData\s*=\s*({.*?});', res.text)
    
    html_match = re.search(r'data-options="([^"]+)"', res.text)
    if html_match:
        try:
            data = json.loads(html_match.group(1).replace('&quot;', '"'))
            videos = data.get('flashvars', {}).get('metadata', {}).get('videos', [])
            if videos:
                mp4_links = [{'quality': v.get('name', ''), 'url': v.get('url', '')} for v in videos]
                return jsonify({'mp4_links': mp4_links, 'status': 200})
        except:
            pass

    return jsonify({
        'status': res.status_code,
        'error': 'could not extract video',
        'length': len(res.text)
    })

@app.route('/latest')
def latest():
    res = requests.get(BASE_URL, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')

    episodes = []
    for item in soup.select('.last-episode-container'):
        title = item.select_one('.anime-title')
        link = item.select_one('a')
        img = item.select_one('img')
        ep_num = item.select_one('.episode-number')
        if title and link:
            episodes.append({
                'title': title.text.strip(),
                'url': link.get('href'),
                'image': img.get('src') if img else None,
                'episode': ep_num.text.strip() if ep_num else ''
            })

    return jsonify({'episodes': episodes, 'status': res.status_code})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
