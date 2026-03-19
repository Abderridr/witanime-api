from flask import Flask, jsonify, request
from witanime_scraper import WitAnimeScraper
import time
import re
import os
import requests
from urllib.parse import unquote

app = Flask(__name__)
scraper = WitAnimeScraper()

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'Welcome to WitAnime Scraper API! 🎉',
        'status': 'Running',
        'endpoints': [
            '/anime/witanime/recent-episodes',
            '/anime/witanime/info?id={id}',
            '/anime/witanime/watch?episodeId={episodeId}',
            '/debug/test-connection'
        ]
    })

@app.route('/debug/test-connection', methods=['GET'])
def test_connection():
    """Debug endpoint to see what the server is actually receiving from the website."""
    try:
        response = requests.get("https://witanime.you", headers=scraper.headers, timeout=10)
        return jsonify({
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content_snippet': response.text[:1000],
            'is_captcha': 'captcha' in response.text.lower() or 'cloudflare' in response.text.lower()
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/anime/witanime/recent-episodes', methods=['GET'])
def recent_episodes():
    page = request.args.get('page', 1)
    latest = scraper.get_latest_episodes()
    
    results = []
    for ep in latest:
        match = re.search(r'(.*)\s+الحلقة\s+(\d+)', ep['title'])
        if match:
            anime_title = match.group(1).strip()
            episode_num = match.group(2)
        else:
            anime_title = ep['title']
            episode_num = "1"
            
        episode_id = ep['url'].strip('/').split('/')[-1]
            
        results.append({
            'id': slugify(anime_title),
            'title': anime_title,
            'episodeId': episode_id, 
            'episodeNumber': int(episode_num),
            'url': ep['url']
        })
        
    return jsonify({
        'currentPage': page,
        'hasNextPage': False,
        'results': results,
        'count': len(results)
    })

@app.route('/anime/witanime/info', methods=['GET'])
def anime_info():
    anime_id = request.args.get('id')
    if not anime_id:
        return jsonify({'error': 'Missing id parameter'}), 400
    
    anime_url = f"https://witanime.you/anime/{anime_id}/"
    details = scraper.get_anime_details(anime_url)
    
    if not details:
        return jsonify({'error': f'Anime not found at {anime_url}'}), 404
        
    return jsonify(details)

@app.route('/anime/witanime/watch', methods=['GET'])
def watch_episode():
    episode_id = request.args.get('episodeId')
    if not episode_id:
        return jsonify({'error': 'Missing episodeId parameter'}), 400
    
    decoded_id = unquote(episode_id)
    episode_url = f"https://witanime.you/episode/{decoded_id}/"
    
    data = scraper.get_episode_data(episode_url)
    
    if not data:
        return jsonify({
            'error': 'Episode not found',
            'attempted_url': episode_url
        }), 404
        
    sources = []
    for link in data.get('download_links', []):
        sources.append({
            'url': link['url'],
            'isM3U8': '.m3u8' in link['url'].lower(),
            'quality': link['quality']
        })
        
    return jsonify({
        'headers': {
            'Referer': 'https://witanime.you/',
            'User-Agent': scraper.headers['User-Agent']
        },
        'sources': sources,
        'watch_servers': data.get('watch_servers')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
