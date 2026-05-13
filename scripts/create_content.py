#!/usr/bin/env python3
"""
Content Machine - Facebook Post Generator
Generates educational posts from YouTube transcripts
"""

import json
import os
import re
import random
import requests
import time
from datetime import datetime
from pathlib import Path

# Config
WORKSPACE = '/root/.openclaw/workspace-content-machine'
POSTS_DIR = f'{WORKSPACE}/content/facebook-posts/personal-profile/unused'
CUSTOMER_POSTS_DIR = f'{WORKSPACE}/content/facebook-posts/customer-group/unused'
TRANSCRIPTS_DIR = f'{WORKSPACE}/personal-profile/transcripts'
TRACKER_FILE = f'{WORKSPACE}/personal-profile/video_tracker.md'
CREDENTIALS_FILE = '/root/.openclaw/workspace/credentials/supadata_api_key.txt'

# Niches to search
NICHES = [
    'entrepreneurship',
    'wealth',
    'AI',
    'network marketing',
    'marketing',
    'mindset',
    'business'
]

# YouTube search queries by niche
SEARCH_QUERIES = {
    'entrepreneurship': ['how to start a business 2024', 'entrepreneurship tips', 'business growth strategies'],
    'wealth': ['how to build wealth', 'passive income ideas', 'financial freedom strategies'],
    'AI': ['AI business tools', 'how to use AI for business', 'AI automation strategies'],
    'network marketing': ['network marketing tips', 'MLM success strategies', 'direct sales techniques'],
    'marketing': ['digital marketing strategies', 'social media marketing tips', 'content marketing 2024'],
    'mindset': ['millionaire mindset', 'success mindset', 'entrepreneur mindset tips'],
    'business': ['business scaling strategies', 'how to grow your business', 'business owner tips']
}

def get_supadata_key():
    """Get Supadata API key"""
    with open(CREDENTIALS_FILE, 'r') as f:
        content = f.read().strip()
        # Handle both plain key and KEY=VALUE format
        if '=' in content:
            return content.split('=')[1].strip()
        return content

def load_video_tracker():
    """Load list of already used video URLs"""
    used_urls = set()
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, 'r') as f:
            content = f.read()
            # Extract YouTube URLs from markdown
            urls = re.findall(r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)', content)
            used_urls.update(urls)
    return used_urls

def search_youtube_videos(niche, max_results=5):
    """Search YouTube for videos in a niche"""
    queries = SEARCH_QUERIES.get(niche, [f'{niche} tips'])
    query = random.choice(queries)
    
    # Use Supadata's search endpoint
    api_key = get_supadata_key()
    search_url = f"https://api.supadata.ai/v1/youtube/search?query={requests.utils.quote(query)}&maxResults={max_results}"
    
    headers = {'x-api-key': api_key}
    
    try:
        response = requests.get(search_url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            videos = []
            for item in data.get('results', []):
                video_id = item.get('id')
                if video_id:
                    channel_name = 'Unknown'
                    if 'channel' in item and isinstance(item['channel'], dict):
                        channel_name = item['channel'].get('name', 'Unknown')
                    videos.append({
                        'id': video_id,
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'title': item.get('title', 'Unknown'),
                        'channel': channel_name
                    })
            return videos
    except Exception as e:
        print(f"Search error: {e}")
    
    return []

def fetch_transcript(video_id):
    """Fetch transcript using Supadata API"""
    api_key = get_supadata_key()
    transcript_url = f"https://api.supadata.ai/v1/youtube/transcript?videoId={video_id}"
    
    headers = {'x-api-key': api_key}
    
    try:
        response = requests.get(transcript_url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Transcript error: {e}")
    
    return None

def save_transcript(video_id, transcript_data):
    """Save transcript to file"""
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
    filepath = f"{TRANSCRIPTS_DIR}/{video_id}.json"
    with open(filepath, 'w') as f:
        json.dump(transcript_data, f, indent=2)
    return filepath

def extract_transcript_text(transcript_data):
    """Extract full text from transcript"""
    if isinstance(transcript_data, dict) and 'content' in transcript_data:
        text_parts = [item.get('text', '') for item in transcript_data['content']]
        return ' '.join(text_parts)
    return str(transcript_data)

def extract_key_points(transcript_text, num_points=5):
    """Extract key educational points from transcript"""
    # Clean text
    text = re.sub(r'\s+', ' ', transcript_text).strip()
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    
    # Score sentences by educational value
    value_keywords = [
        'how to', 'steps to', 'way to', 'method', 'strategy', 'tactic',
        'secret', 'key', 'important', 'critical', 'essential', 'must',
        'build', 'create', 'start', 'grow', 'scale', 'increase',
        'money', 'revenue', 'profit', 'sales', 'income', 'wealth',
        'mistake', 'avoid', 'never', 'always', 'dont', 'stop',
        'first', 'second', 'third', 'next', 'then', 'finally',
        'because', 'this is why', 'the reason', 'therefore'
    ]
    
    scored_sentences = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 40 or len(sent) > 300:
            continue
        
        score = 0
        sent_lower = sent.lower()
        for kw in value_keywords:
            if kw in sent_lower:
                score += 2
        
        # Bonus for actionable content
        if any(x in sent_lower for x in ['start by', 'begin with', 'focus on', 'the key is']):
            score += 3
        
        # Bonus for numbers/stats
        if re.search(r'\d+', sent):
            score += 1
        
        if score >= 3:
            scored_sentences.append((sent, score))
    
    # Sort by score and return top points
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored_sentences[:num_points]]

def generate_post_content(key_points, niche):
    """Generate unique post content from key points"""
    if not key_points:
        return None
    
    # Randomly choose post structure
    structure = random.choice(['numbered', 'bullet', 'narrative', 'question'])
    
    if structure == 'numbered':
        intro = f"Here are {len(key_points)} powerful insights about {niche} that most people overlook:\n\n"
        body = ""
        for i, point in enumerate(key_points, 1):
            body += f"{i}. {point}\n\n"
        outro = f"Which of these resonates with your current {niche} journey?"
        
    elif structure == 'bullet':
        intro = f"The biggest shifts in {niche} happen when you understand these fundamentals:\n\n"
        body = ""
        for point in key_points:
            body += f"• {point}\n\n"
        outro = f"What's the first one you're implementing?"
        
    elif structure == 'narrative':
        if len(key_points) >= 3:
            intro = f"Most people approach {niche} backwards. Here's what actually works:\n\n"
            body = f"{key_points[0]}\n\n"
            body += f"But here's what changes everything: {key_points[1][0].lower()}{key_points[1][1:]}\n\n"
            body += f"And the result? {key_points[2][0].lower()}{key_points[2][1:]}"
            outro = f"Ready to flip the script on your {niche} approach?"
        else:
            body = "\n\n".join(key_points)
            outro = f"What's your next move in {niche}?"
            intro = f"A different perspective on {niche}:\n\n"
            
    else:  # question
        intro = f"Quick question about {niche}:\n\n"
        body = f"{key_points[0]}\n\n"
        if len(key_points) > 1:
            body += f"Yet most people ignore this and wonder why they're stuck. {key_points[1]}\n\n"
        outro = f"Are you focusing on what actually moves the needle in {niche}?"
    
    return intro + body + outro

def create_post(video_info, transcript_data, niche):
    """Create a Facebook post from video transcript"""
    transcript_text = extract_transcript_text(transcript_data)
    key_points = extract_key_points(transcript_text)
    
    if not key_points:
        return None
    
    content = generate_post_content(key_points, niche)
    if not content:
        return None
    
    post_id = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    post = f"""---
id: {post_id}
status: UNUSED
created: {datetime.now().strftime('%Y-%m-%d')}
type: personal-profile
source: {video_info['url']}
niche: {niche}
---

{content}
"""
    
    return {
        'id': post_id,
        'content': post,
        'video_info': video_info
    }

def save_post(post_data):
    """Save post to file"""
    os.makedirs(POSTS_DIR, exist_ok=True)
    filepath = f"{POSTS_DIR}/{post_data['id']}.md"
    with open(filepath, 'w') as f:
        f.write(post_data['content'])
    return filepath

def update_video_tracker(video_info, niche):
    """Add video to tracker"""
    os.makedirs(os.path.dirname(TRACKER_FILE), exist_ok=True)
    
    entry = f"\n- [{video_info['title']}]({video_info['url']}) - {niche} - {datetime.now().strftime('%Y-%m-%d')}"
    
    with open(TRACKER_FILE, 'a') as f:
        f.write(entry)

def update_posts_json(post_data, niche):
    """Add post to posts.json index"""
    posts_json_path = f'{WORKSPACE}/content/facebook-posts/personal-profile/posts.json'
    
    # Load existing posts
    posts = []
    if os.path.exists(posts_json_path):
        try:
            with open(posts_json_path, 'r') as f:
                posts = json.load(f)
        except:
            posts = []
    
    # Add new post entry
    post_entry = {
        'id': post_data['id'],
        'status': 'UNUSED',
        'created': datetime.now().strftime('%Y-%m-%d'),
        'type': 'personal-profile',
        'niche': niche,
        'source': post_data['video_info']['url']
    }
    posts.append(post_entry)
    
    # Save updated posts.json
    os.makedirs(os.path.dirname(posts_json_path), exist_ok=True)
    with open(posts_json_path, 'w') as f:
        json.dump(posts, f, indent=2)

def main():
    """Main workflow"""
    print("=" * 60)
    print("CONTENT MACHINE - Starting Post Generation")
    print("=" * 60)
    
    # Load used videos
    used_videos = load_video_tracker()
    print(f"Loaded {len(used_videos)} previously used videos")
    
    posts_created = 0
    target_posts = 10
    
    # Rotate through niches
    niche_cycle = random.sample(NICHES, len(NICHES))
    
    for niche in niche_cycle:
        if posts_created >= target_posts:
            break
        
        print(f"\n--- Searching niche: {niche} ---")
        
        # Search for videos
        videos = search_youtube_videos(niche)
        
        for video in videos:
            if posts_created >= target_posts:
                break
            
            # Skip if already used
            if video['id'] in used_videos:
                print(f"  Skipping (used): {video['title'][:50]}...")
                continue
            
            print(f"  Fetching transcript: {video['title'][:50]}...")
            
            # Fetch transcript
            transcript = fetch_transcript(video['id'])
            if not transcript:
                print(f"    ✗ No transcript available")
                continue
            
            # Save transcript
            save_transcript(video['id'], transcript)
            
            # Create post
            print(f"    Creating post...")
            post_data = create_post(video, transcript, niche)
            
            if post_data:
                # Save post
                save_post(post_data)
                
                # Update tracker
                update_video_tracker(video, niche)
                used_videos.add(video['id'])
                
                # Update posts.json index
                update_posts_json(post_data, niche)
                
                posts_created += 1
                print(f"    ✓ Post created: {post_data['id']}")
                
                # Rate limiting - wait 45 seconds between posts
                if posts_created < target_posts:
                    print(f"    ⏳ Waiting 45 seconds before next post...")
                    time.sleep(45)
            else:
                print(f"    ✗ Failed to create post")
    
    print(f"\n{'=' * 60}")
    print(f"COMPLETE: Created {posts_created} posts")
    print(f"{'=' * 60}")
    
    return posts_created

# Customer-group specific content (mindset in trading - no YouTube)
CUSTOMER_TOPICS = [
    {
        'title': 'The Psychology of Winning Trades',
        'points': [
            'Your mindset before entering a trade determines your outcome more than your strategy.',
            'Fear and greed are the two emotions that destroy most traders.',
            'Develop a pre-trade routine that puts you in a calm, focused state.',
            'Review your winning trades to understand what you did right mentally.',
            'The best traders think in probabilities, not predictions.'
        ]
    },
    {
        'title': 'Why Most Traders Fail (And How to Avoid It)',
        'points': [
            'Lack of discipline is the #1 reason traders fail, not bad strategy.',
            'Overtrading stems from emotional need, not market opportunity.',
            'Risk management is 80% psychology and 20% math.',
            'Successful traders have learned to sit on their hands.',
            'Your trading plan is only as good as your ability to follow it.'
        ]
    },
    {
        'title': 'Building Unshakeable Trading Confidence',
        'points': [
            'Confidence comes from preparation, not ego.',
            'Keep a trading journal to track your psychological patterns.',
            'Confidence is built one small win at a time.',
            'Never risk more than you can afford to lose emotionally.',
            'Your self-worth should never be tied to a single trade.'
        ]
    },
    {
        'title': 'The Disciplined Trader Mindset',
        'points': [
            'Discipline means following your rules even when you don't feel like it.',
            'The market rewards patience and punishes impatience.',
            'Every trade should have a clear entry, exit, and stop-loss before you enter.',
            'Emotional trading is expensive trading.',
            'The best trade is sometimes no trade at all.'
        ]
    },
    {
        'title': 'Mastering Emotional Control in Trading',
        'points': [
            'Emotions are data, not instructions.',
            'Notice when you're trading to recover losses - that's revenge trading.',
            'Step away from the screen when you feel overwhelmed.',
            'Breathing exercises can reset your emotional state in 60 seconds.',
            'The trader who controls their emotions controls their results.'
        ]
    },
    {
        'title': 'The Power of Patience in Trading',
        'points': [
            'The market will be here tomorrow, next week, and next year.',
            'Waiting for the perfect setup is a skill, not a weakness.',
            'Impatience leads to forced trades and unnecessary losses.',
            'The best opportunities often come to those who wait.',
            'Patience is the difference between amateur and professional traders.'
        ]
    },
    {
        'title': 'Developing a Growth Mindset for Trading',
        'points': [
            'Every loss is a lesson if you're willing to learn from it.',
            'The market is your teacher - pay attention to what it shows you.',
            'Successful traders are lifelong students of the markets.',
            'Your strategy will evolve as you grow as a trader.',
            'Mistakes are tuition payments to the market - make sure you learn.'
        ]
    },
    {
        'title': 'Trading Psychology: Fear vs. Greed',
        'points': [
            'Fear causes you to exit winners too early.',
            'Greed causes you to hold losers too long.',
            'The middle path is following your predetermined plan.',
            'Both emotions stem from lack of trust in your system.',
            'Master your emotions and you master your trading.'
        ]
    },
    {
        'title': 'Building Mental Toughness for Trading',
        'points': [
            'Losses are part of the game - expect them and accept them.',
            'Mental toughness means sticking to your plan during drawdowns.',
            'Don't let a losing streak shake your confidence in your edge.',
            'The mentally tough trader focuses on process, not outcomes.',
            'Your ability to bounce back determines your long-term success.'
        ]
    },
    {
        'title': 'The Morning Routine of Successful Traders',
        'points': [
            'Start your day with clarity, not chaos.',
            'Review your trading plan before the market opens.',
            'Meditation or visualization can improve your focus.',
            'Physical exercise sharpens your mental edge.',
            'A consistent routine creates consistent results.'
        ]
    }
]

def generate_customer_post_content(topic):
    """Generate a customer-group post from a topic"""
    hook_options = [
        f"{topic['title']} - this changed everything for me:",
        f"If you're struggling with {topic['title'].lower()}, read this:",
        f"The truth about {topic['title'].lower()}:",
        f"Most traders get {topic['title'].lower()} wrong. Here's why:",
        f"A different perspective on {topic['title'].lower()}:"
    ]
    
    hook = random.choice(hook_options)
    
    body = "\n\n".join([f"• {point}" for point in topic['points']])
    
    cta_options = [
        "Which of these resonates with your trading journey?",
        "What's your biggest mindset challenge in trading?",
        "How do you handle emotions during a losing streak?",
        "Save this for when you need a mindset reset.",
        "Tag a trader who needs to see this."
    ]
    
    cta = random.choice(cta_options)
    
    return f"{hook}\n\n{body}\n\n{cta}"

def create_customer_post(topic):
    """Create a customer-group post"""
    post_id = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    content = generate_customer_post_content(topic)
    
    post = f"""---
id: {post_id}
status: UNUSED
created: {datetime.now().strftime('%Y-%m-%d')}
type: customer-group
source: generated
niche: mindset
---

{content}
"""
    
    return {
        'id': post_id,
        'content': post
    }

def save_customer_post(post_data):
    """Save customer post to file"""
    os.makedirs(CUSTOMER_POSTS_DIR, exist_ok=True)
    filepath = f"{CUSTOMER_POSTS_DIR}/{post_data['id']}.md"
    with open(filepath, 'w') as f:
        f.write(post_data['content'])
    return filepath

def update_customer_posts_json(post_data):
    """Add customer post to posts.json index"""
    posts_json_path = f'{WORKSPACE}/content/facebook-posts/customer-group/posts.json'
    
    posts = []
    if os.path.exists(posts_json_path):
        try:
            with open(posts_json_path, 'r') as f:
                posts = json.load(f)
        except:
            posts = []
    
    post_entry = {
        'id': post_data['id'],
        'status': 'UNUSED',
        'created': datetime.now().strftime('%Y-%m-%d'),
        'type': 'customer-group',
        'niche': 'mindset',
        'source': 'generated'
    }
    posts.append(post_entry)
    
    os.makedirs(os.path.dirname(posts_json_path), exist_ok=True)
    with open(posts_json_path, 'w') as f:
        json.dump(posts, f, indent=2)

def generate_customer_posts(target_count=5):
    """Generate customer-group posts about mindset/trading"""
    print("\n" + "=" * 60)
    print("GENERATING CUSTOMER-GROUP POSTS (Mindset/Trading)")
    print("=" * 60)
    
    posts_created = 0
    topics = random.sample(CUSTOMER_TOPICS, min(target_count, len(CUSTOMER_TOPICS)))
    
    for topic in topics:
        if posts_created >= target_count:
            break
        
        print(f"\nCreating post: {topic['title']}")
        
        post_data = create_customer_post(topic)
        save_customer_post(post_data)
        update_customer_posts_json(post_data)
        
        posts_created += 1
        print(f"  ✓ Post created: {post_data['id']}")
        
        # Rate limiting
        if posts_created < target_count:
            print(f"  ⏳ Waiting 30 seconds...")
            time.sleep(30)
    
    print(f"\n{'=' * 60}")
    print(f"COMPLETE: Created {posts_created} customer posts")
    print(f"{'=' * 60}")
    
    return posts_created

def count_unused_posts(folder_type):
    """Count unused posts in a folder"""
    if folder_type == 'timeline':
        posts_dir = POSTS_DIR
    else:
        posts_dir = CUSTOMER_POSTS_DIR
    
    if not os.path.exists(posts_dir):
        return 0
    
    return len([f for f in os.listdir(posts_dir) if f.endswith('.md')])

def main():
    """Main workflow - check inventory and generate posts only if needed"""
    print("=" * 60)
    print("CONTENT MACHINE - Checking Inventory Levels")
    print("=" * 60)
    
    # Check current inventory
    timeline_count = count_unused_posts('timeline')
    customer_count = count_unused_posts('customer')
    
    print(f"\nCurrent Inventory:")
    print(f"  Timeline unused: {timeline_count}")
    print(f"  Customer unused: {customer_count}")
    print(f"  Threshold: 5 posts")
    
    timeline_created = 0
    customer_created = 0
    
    # Generate timeline posts if below threshold
    if timeline_count < 5:
        print(f"\n⚠️  Timeline inventory low ({timeline_count} < 5). Generating 10 posts...")
        timeline_created = main_timeline()
    else:
        print(f"\n✅ Timeline inventory sufficient ({timeline_count} >= 5). Skipping.")
    
    # Generate customer posts if below threshold
    if customer_count < 5:
        print(f"\n⚠️  Customer inventory low ({customer_count} < 5). Generating 10 posts...")
        customer_created = generate_customer_posts(target_count=10)
    else:
        print(f"\n✅ Customer inventory sufficient ({customer_count} >= 5). Skipping.")
    
    print(f"\n{'=' * 60}")
    print(f"SUMMARY:")
    print(f"  Timeline posts created: {timeline_created}")
    print(f"  Customer posts created: {customer_created}")
    print(f"  Total posts created: {timeline_created + customer_created}")
    print(f"{'=' * 60}")

def main_timeline():
    """Original main function - generate timeline posts from YouTube"""
    print("=" * 60)
    print("CONTENT MACHINE - Timeline Posts (YouTube)")
    print("=" * 60)
    
    used_videos = load_video_tracker()
    print(f"Loaded {len(used_videos)} previously used videos")
    
    posts_created = 0
    target_posts = 10
    
    niche_cycle = random.sample(NICHES, len(NICHES))
    
    for niche in niche_cycle:
        if posts_created >= target_posts:
            break
        
        print(f"\n--- Searching niche: {niche} ---")
        
        videos = search_youtube_videos(niche)
        
        for video in videos:
            if posts_created >= target_posts:
                break
            
            if video['id'] in used_videos:
                print(f"  Skipping (used): {video['title'][:50]}...")
                continue
            
            print(f"  Fetching transcript: {video['title'][:50]}...")
            
            transcript = fetch_transcript(video['id'])
            if not transcript:
                print(f"    ✗ No transcript available")
                continue
            
            save_transcript(video['id'], transcript)
            
            print(f"    Creating post...")
            post_data = create_post(video, transcript, niche)
            
            if post_data:
                save_post(post_data)
                update_video_tracker(video, niche)
                update_posts_json(post_data, niche)
                
                posts_created += 1
                print(f"    ✓ Post created: {post_data['id']}")
                
                if posts_created < target_posts:
                    print(f"    ⏳ Waiting 45 seconds before next post...")
                    time.sleep(45)
            else:
                print(f"    ✗ Failed to create post")
    
    print(f"\n{'=' * 60}")
    print(f"COMPLETE: Created {posts_created} timeline posts")
    print(f"{'=' * 60}")
    
    return posts_created

if __name__ == '__main__':
    main()
