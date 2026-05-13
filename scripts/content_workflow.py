#!/usr/bin/env python3
"""
Content Machine Workflow
Fetches YouTube transcripts and creates Facebook posts
"""

import json
import time
import requests
import re
import random
from datetime import datetime

# Configuration
# Read Supadata API key (handle both formats: with or without prefix)
with open('/root/.openclaw/workspace/credentials/supadata_api_key.txt', 'r') as f:
    SUPADATA_API_KEY = f.read().strip()
    # Remove prefix if present
    if SUPADATA_API_KEY.startswith('SUPADATA_API_KEY='):
        SUPADATA_API_KEY = SUPADATA_API_KEY.replace('SUPADATA_API_KEY=', '')
# GitHub token is embedded in git remote URL, no separate file needed
RATE_LIMIT_SECONDS = 240  # 4 minutes between requests (well under 10/sec limit)
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
        
        # Search for videos - add educational keywords to get better content
        search_terms = {
            'entrepreneurship': 'entrepreneurship business start company how to',
            'finance': 'personal finance investing money management tips',
            'network marketing': 'network marketing business tips success strategy',
            'affiliate marketing': 'affiliate marketing tutorial how to make money',
            'AI': 'AI business automation artificial intelligence tutorial',
            'wealth': 'wealth building financial freedom money mindset',
            'mindset': 'success mindset entrepreneur motivation business',
            'sales': 'sales techniques closing deals selling tips',
            'marketing': 'marketing strategy business growth digital marketing',
            'business': 'business growth strategy entrepreneur tips'
        }
        
        query = search_terms.get(niche, niche)
        
        search_url = 'https://www.googleapis.com/youtube/v3/search'
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': max_results,
            'order': 'relevance',
            'videoDuration': 'medium',  # 4-20 minutes for good content
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

def clean_text(text):
    """Clean up text for use in a post"""
    text = text.replace('\n', ' ')
    text = ' '.join(text.split())
    return text.strip()

def extract_key_insights(transcript_text, niche):
    """Extract key educational insights from the transcript"""
    clean_transcript = clean_text(transcript_text)
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', clean_transcript)
    
    insights = []
    
    value_keywords = [
        'how to', 'secret', 'key', 'important', 'must', 'need to', 'should',
        'strategy', 'tactic', 'method', 'way to', 'steps', 'formula',
        'success', 'win', 'grow', 'build', 'create', 'start',
        'mistake', 'avoid', 'never', 'always', 'critical', 'essential',
        'money', 'revenue', 'profit', 'sales', 'customer', 'market',
        'mindset', 'belief', 'think', 'perspective', 'approach',
        'first', 'second', 'third', 'next', 'finally', 'ultimately',
        'because', 'therefore', 'this is why', 'the reason',
        'business', 'entrepreneur', 'company', 'product', 'service'
    ]
    
    for sentence in sentences:
        sentence = sentence.strip()
        
        if len(sentence) < 30 or len(sentence) > 250:
            continue
            
        word_count = len(sentence.split())
        if word_count < 6:
            continue
            
        if sentence.endswith('?'):
            continue
            
        sentence_lower = sentence.lower()
        score = 0
        for kw in value_keywords:
            if kw in sentence_lower:
                score += 2
        
        if any(phrase in sentence_lower for phrase in ['start by', 'begin with', 'focus on', 'the key is']):
            score += 3
        if any(c.isdigit() for c in sentence):
            score += 1
            
        filler_phrases = ['i think', 'i believe', 'maybe', 'sort of', 'kind of', 'you know']
        for filler in filler_phrases:
            if filler in sentence_lower:
                score -= 1
                
        if score >= 2:
            sentence = sentence[0].upper() + sentence[1:]
            insights.append((sentence, score))
    
    insights.sort(key=lambda x: x[1], reverse=True)
    
    # If not enough insights, add general ones
    if len(insights) < 3:
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= 40 and len(sentence) <= 200:
                sentence = sentence[0].upper() + sentence[1:]
                if sentence not in [i[0] for i in insights]:
                    insights.append((sentence, 1))
            if len(insights) >= 5:
                break
    
    return [insight[0] for insight in insights[:6]]

def generate_varied_hook(niche):
    """Generate a varied hook"""
    hooks = [
        f"Most people get {niche} completely wrong. Here's the truth.",
        f"Here's what nobody tells you about {niche}.",
        f"I just watched something that completely shifted how I think about {niche}.",
        f"This might be the most important thing you read about {niche} today.",
        f"Stop what you're doing. This changes everything about {niche}.",
        f"The biggest myth about {niche}? That it's complicated. It's not.",
        f"If you're struggling with {niche}, read this carefully.",
        f"I came across a video that breaks down {niche} in a way I've never seen before.",
        f"What if everything you believed about {niche} was backwards?",
        f"This creator has built multiple successful businesses. Here's what they said about {niche}.",
        f"The real secret to {niche} isn't what you think.",
        f"I used to think {niche} was about working harder. I was wrong.",
        f"Want to win at {niche}? Start here.",
        f"This is why most people fail at {niche} (and how to fix it).",
        f"The {niche} game has changed. Here's what works now.",
        f"I came across this video about {niche} and had to share it.",
        f"This creator shared some powerful insights about {niche}.",
    ]
    return random.choice(hooks)

def format_body_structure(insights, niche, structure_type):
    """Format insights into various body structures"""
    if not insights or len(insights) < 2:
        return f"This content dives deep into {niche} strategies that actually work. The insights shared here come from real-world experience and can help you avoid common pitfalls while accelerating your growth."
    
    if structure_type == 1:
        body = "Here are the key insights:\n\n"
        for i, insight in enumerate(insights[:5], 1):
            body += f"{i}. {insight}\n\n"
        return body.strip()
    
    elif structure_type == 2:
        body = "What stood out:\n\n"
        for insight in insights[:4]:
            body += f"→ {insight}\n\n"
        return body.strip()
    
    elif structure_type == 3:
        if len(insights) >= 3:
            body = f"First, {insights[0][0].lower() + insights[0][1:]}\n\n"
            body += f"Second, {insights[1][0].lower() + insights[1][1:]}\n\n"
            body += f"And perhaps most importantly: {insights[2][0].lower() + insights[2][1:]}"
            return body
        else:
            return "\n\n".join(insights)
    
    elif structure_type == 4:
        if len(insights) >= 2:
            body = f"The challenge: {insights[0]}\n\n"
            body += f"The approach that works: {insights[1]}\n\n"
            if len(insights) >= 3:
                body += f"The result: {insights[2]}"
            return body
        else:
            return "\n\n".join(insights)
    
    elif structure_type == 5:
        body = f"\"{insights[0]}\"\n\n"
        if len(insights) >= 2:
            body += f"This matters because {insights[1][0].lower() + insights[1][1:]}\n\n"
        if len(insights) >= 3:
            body += f"And it gets better: {insights[2][0].lower() + insights[2][1:]}"
        return body.strip()
    
    else:
        if len(insights) >= 3:
            body = f"{insights[0]}\n\n"
            body += f"Here's why this matters: {insights[1][0].lower() + insights[1][1:]}\n\n"
            body += f"The key takeaway: {insights[2][0].lower() + insights[2][1:]}"
            return body
        else:
            return "\n\n".join(insights)

def generate_varied_cta(niche):
    """Generate varied call-to-action"""
    ctas = [
        f"Which of these insights resonates most with where you are in your {niche} journey?",
        f"What's the biggest challenge you're facing with {niche} right now?",
        f"Drop a comment if you're implementing any of these strategies.",
        f"If you found this valuable, share it with someone who needs to see it.",
        f"What's one action you're taking this week based on what you just read?",
        f"Save this for later. You'll want to come back to it.",
        f"Agree or disagree? Let's discuss in the comments.",
        f"What's your experience with {niche}? I'd love to hear your perspective.",
        f"The difference between those who succeed and those who don't? Action. What's your next move?",
        f"Knowledge without action is just entertainment. What's one thing you're implementing today?",
        f"Tag someone who needs to see this.",
        f"Which point hit home for you? Let me know below.",
        f"What's your biggest takeaway? Comment below.",
        f"Ready to level up your {niche} game? Start with one of these insights today.",
    ]
    return random.choice(ctas)

def write_post_from_transcript(transcript, video_info):
    """Write Facebook post from transcript using AI-powered extraction"""
    # Extract text from transcript
    if isinstance(transcript, dict) and 'content' in transcript:
        text_parts = [item['text'] for item in transcript['content']]
        full_text = ' '.join(text_parts)
    else:
        full_text = str(transcript)
    
    niche = video_info.get('niche', 'business')
    
    # Extract key insights
    insights = extract_key_insights(full_text, niche)
    
    # Generate varied components
    hook = generate_varied_hook(niche)
    structure_type = random.randint(1, 6)
    body = format_body_structure(insights, niche, structure_type)
    cta = generate_varied_cta(niche)
    
    # Combine into full post
    post = f"{hook}\n\n{body}\n\n{cta}"
    
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
    transcript_file = f"{TRANSCRIPT_DIR}/{filename.replace('.md', '.json')}"\n    with open(transcript_file, 'w') as f:
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
