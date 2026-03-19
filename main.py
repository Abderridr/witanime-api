from flask import Flask, jsonify, request
from witanime_scraper import WitAnimeScraper
import time
import re

app = Flask(__name__)
scraper = WitAnimeScraper()

def slugify(text):
    # Simple slugify for IDs
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

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
            
        results.append({
            'id': slugify(anime_title),
            'title': anime_title,
            'episodeId': ep['url'].split('/')[-2], # Use the slug from URL
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
    
    # In a real app, we'd map the ID back to a URL. 
    # For this demo, we'll assume the ID is the slug.
    anime_url = f"https://witanime.you/anime/{anime_id}/"
    details = scraper.get_anime_details(anime_url)
    
    if not details:
        return jsonify({'error': 'Anime not found'}), 404
        
    return jsonify({
        'id': anime_id,
        'title': details.get('title'),
        'genres': details.get('genres'),
        'status': details.get('status'),
        'releaseDate': details.get('year'),
        # Add more fields as needed by the app
    })

@app.route('/anime/witanime/watch', methods=['GET'])
def watch_episode():
    episode_id = request.args.get('episodeId')
    if not episode_id:
        return jsonify({'error': 'Missing episodeId parameter'}), 400
    
    episode_url = f"https://witanime.you/episode/{episode_id}/"
    data = scraper.get_episode_data(episode_url)
    
    if not data:
        return jsonify({'error': 'Episode not found'}), 404
        
    # Format for Consumet 'watch' endpoint
    sources = []
    for link in data.get('download_links', []):
        # We'll treat download links as sources for the player if they are direct-ish
        sources.append({
            'url': link['url'],
            'isM3U8': '.m3u8' in link['url'],
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
    app.run(host='0.0.0.0', port=3000)
