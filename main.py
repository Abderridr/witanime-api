from flask import Flask, jsonify, request
from witanime_scraper import WitAnimeScraper
import time
import re
import os
from urllib.parse import unquote

app = Flask(__name__)
scraper = WitAnimeScraper()

def slugify(text):
    # Simple slugify for IDs
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'Welcome to WitAnime Scraper API! 🎉',
        'status': 'Running',
        'endpoints': [
            '/anime/witanime/recent-episodes',
            '/anime/witanime/info?id={id}',
            '/anime/witanime/watch?episodeId={episodeId}'
        ]
    })

@app.route('/anime/witanime/recent-episodes', methods=['GET'])
def recent_episodes():
    page = request.args.get('page', 1)
    latest = scraper.get_latest_episodes()
    
    results = []
    for ep in latest:
        # Extract anime title and episode number from the string like "Jigokuraku 2nd Season الحلقة 10"
        match = re.search(r'(.*)\s+الحلقة\s+(\d+)', ep['title'])
        if match:
            anime_title = match.group(1).strip()
            episode_num = match.group(2)
        else:
            anime_title = ep['title']
            episode_num = "1"
            
        # The episodeId is the slug from the URL (e.g., jigokuraku-2nd-season-الحلقة-10)
        # We use unquote to handle the Arabic characters correctly
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
        'results': results
    })

@app.route('/anime/witanime/info', methods=['GET'])
def anime_info():
    anime_id = request.args.get('id')
    if not anime_id:
        return jsonify({'error': 'Missing id parameter'}), 400
    
    # Map the ID back to a URL
    anime_url = f"https://witanime.you/anime/{anime_id}/"
    details = scraper.get_anime_details(anime_url)
    
    if not details:
        return jsonify({'error': f'Anime not found at {anime_url}'}), 404
        
    return jsonify({
        'id': anime_id,
        'title': details.get('title'),
        'genres': details.get('genres'),
        'status': details.get('status'),
        'releaseDate': details.get('year'),
        'episodes': details.get('episodes_count'),
        'description': details.get('description', 'No description available.')
    })

@app.route('/anime/witanime/watch', methods=['GET'])
def watch_episode():
    episode_id = request.args.get('episodeId')
    if not episode_id:
        return jsonify({'error': 'Missing episodeId parameter'}), 400
    
    # Ensure the episode_id is properly decoded if it contains % encoding
    decoded_id = unquote(episode_id)
    episode_url = f"https://witanime.you/episode/{decoded_id}/"
    
    data = scraper.get_episode_data(episode_url)
    
    if not data:
        return jsonify({
            'error': 'Episode not found',
            'attempted_url': episode_url
        }), 404
        
    # Format for Consumet 'watch' endpoint
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
        'sources': sources,
        'watch_servers': data.get('watch_servers')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
