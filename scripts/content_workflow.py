#!/usr/bin/env python3
"""
Content Machine Workflow
Fetches YouTube transcripts and creates Facebook posts
"""

import json
import time
import requests
import re
from datetime import datetime

# Configuration
# Read Supadata API key (handle both formats: with or without prefix)
with open('/root/.openclaw/workspace/credentials/supadata_api_key.txt', 'r') as f:
    SUPADATA_API_KEY = f.read().strip()
    # Remove prefix if present
    if SUPADATA_API_KEY.startswith('SUPADATA_API_KEY='):
        SUPADATA_API_KEY = SUPADATA_API_KEY.replace('SUPADATA_API_KEY=', '')
# GitHub token is embedded in git remote URL, no separate file needed
RATE_LIMIT_SECONDS = 2  # 2 seconds between requests (well under 10/sec limit)
VIDEO_TRACKER_PATH = '/root/.openclaw/workspace-content-machine/personal-profile/video_tracker.md'
OUTPUT_DIR = '/root/.openclaw/workspace-content-machine/content/facebook-posts/personal-profile/unused'
TRANSCRIPT_DIR = '/root/.openclaw/workspace-content-machine/personal-profile/transcripts'

# Niches to search
NICHES = [
    'entrepreneurship',
    'finance',
    'network marketing',
    'affiliate marketing',
    'AI',
    'wealth',
    'mindset',
    'sales',
    'marketing',
    'business'
]

def get_used_urls():
    """Read video tracker and get list of already used URLs"""
    used_urls = set()
    try:
        with open(VIDEO_TRACKER_PATH, 'r') as f:
            content = f.read()
            # Extract URLs from markdown table
            urls = re.findall(r'https://www\.youtube\.com/watch\?v=[\w-]+', content)
            used_urls.update(urls)
    except Exception as e:
        print(f"Error reading video tracker: {e}")
    return used_urls

def search_youtube(niche, max_results=5):
    """Search YouTube for videos in a niche using YouTube Data API"""
    print(f"Searching YouTube for: {niche}")
    
    try:
        # Read YouTube API key
        with open('/root/.openclaw/workspace/credentials/youtube_api_key.txt', 'r') as f:
            api_key = f.read().strip().replace('YOUTUBE_API_KEY=', '')
        
        # Search for videos
        search_url = 'https://www.googleapis.com/youtube/v3/search'
        params = {
            'part': 'snippet',
            'q': niche,
            'type': 'video',
            'maxResults': max_results,
            'order': 'relevance',
            'key': api_key
        }
        
        response = requests.get(search_url, params=params)
        if response.status_code != 200:
            print(f"YouTube API error: {response.status_code}")
            return []
        
        data = response.json()
        videos = []
        
        for item in data.get('items', []):
            video_id = item['id']['videoId']
            video_info = {
                'url': f'https://www.youtube.com/watch?v={video_id}',
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle'],
                'niche': niche,
                'id': video_id
            }
            videos.append(video_info)
        
        return videos
        
    except Exception as e:
        print(f"Error searching YouTube: {e}")
        return []

def get_transcript(video_url):
    """Get transcript from Supadata"""
    try:
        response = requests.get(
            'https://api.supadata.ai/v1/youtube/transcript',
            headers={'X-API-Key': SUPADATA_API_KEY},
            params={'url': video_url}
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting transcript: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def write_post_from_transcript(transcript, video_info):
    """Write Facebook post from transcript"""
    # Extract text from transcript
    if isinstance(transcript, dict) and 'content' in transcript:
        text_parts = [item['text'] for item in transcript['content']]
        full_text = ' '.join(text_parts)
    else:
        full_text = str(transcript)
    
    # Create post - third person style
    post = f"""I came across this video about {video_info.get('niche', 'business')}...

{full_text[:800]}...

This creator shared some valuable insights about {video_info.get('niche', 'success')}.

What stood out to me most was how they emphasized taking action over just consuming content.

The strategies they shared could be game-changers if applied consistently.

What's one insight from this that you could implement today?"""
    
    return post

def save_post(post_content, video_info, transcript):
    """Save post to file and update tracker"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"post_{timestamp}.md"
    filepath = f"{OUTPUT_DIR}/{filename}"
    
    # Save post
    with open(filepath, 'w') as f:
        f.write(f"---\n")
        f.write(f"id: {filename.replace('.md', '')}\n")
        f.write(f"status: UNUSED\n")
        f.write(f"created: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"type: personal-profile\n")
        f.write(f"source: {video_info.get('url', '')}\n")
        f.write(f"niche: {video_info.get('niche', '')}\n")
        f.write(f"---\n\n")
        f.write(post_content)
    
    # Save transcript
    transcript_file = f"{TRANSCRIPT_DIR}/{filename.replace('.md', '.json')}"
    with open(transcript_file, 'w') as f:
        json.dump(transcript, f, indent=2)
    
    return filename

def update_video_tracker(video_info):
    """Add video to tracker"""
    with open(VIDEO_TRACKER_PATH, 'a') as f:
        f.write(f"\n| {video_info.get('id', 'TBD')} | {video_info.get('niche', '')} | {video_info.get('title', 'TBD')} | {video_info.get('channel', 'TBD')} | {video_info.get('url', '')} | {datetime.now().strftime('%Y-%m-%d')} | {video_info.get('post_file', '')} | Auto-added |")

def push_to_github():
    """Push changes to GitHub"""
    import subprocess
    import os
    
    os.chdir('/root/.openclaw/workspace-content-machine')
    
    # Configure git
    subprocess.run(['git', 'config', 'user.email', 'agent@openclaw.ai'])
    subprocess.run(['git', 'config', 'user.name', 'Content Machine'])
    
    # Add, commit, push
    subprocess.run(['git', 'add', '.'])
    subprocess.run(['git', 'commit', '-m', f'Add new content - {datetime.now().strftime("%Y-%m-%d")}'])
    subprocess.run(['git', 'push', 'origin', 'main'])

def main():
    """Main workflow"""
    print("Starting Content Machine Workflow...")
    
    # Get already used URLs
    used_urls = get_used_urls()
    print(f"Found {len(used_urls)} already used videos")
    
    posts_created = 0
    target_posts = 10
    
    for niche in NICHES:
        if posts_created >= target_posts:
            break
            
        print(f"\nSearching niche: {niche}")
        videos = search_youtube(niche)
        
        for video in videos:
            if posts_created >= target_posts:
                break
                
            video_url = video.get('url')
            
            # Skip if already used
            if video_url in used_urls:
                print(f"Skipping used video: {video_url}")
                continue
            
            print(f"Processing: {video_url}")
            
            # Get transcript
            transcript = get_transcript(video_url)
            if not transcript:
                continue
            
            # Write post
            post_content = write_post_from_transcript(transcript, video)
            
            # Save files
            filename = save_post(post_content, video, transcript)
            video['post_file'] = filename
            
            # Update tracker
            update_video_tracker(video)
            
            posts_created += 1
            print(f"Created post {posts_created}/{target_posts}")
            
            # Wait 4 minutes before next request
            if posts_created < target_posts:
                print(f"Waiting {RATE_LIMIT_SECONDS} seconds...")
                time.sleep(RATE_LIMIT_SECONDS)
    
    # Push to GitHub
    print("\nPushing to GitHub...")
    push_to_github()
    
    print(f"\nComplete! Created {posts_created} posts.")

if __name__ == '__main__':
    main()
