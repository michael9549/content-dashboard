#!/usr/bin/env python3
"""
Content Machine v2 - Long-Form Educational Facebook Posts
Generates educational posts from YouTube transcripts
Process:
1. Read video tracker
2. Search YouTube for videos in niches (mindset, affiliate marketing, network marketing, entrepreneurship, business, wealth)
3. Compare to tracker - skip duplicates
4. Get transcripts via Supadata (30-60 sec apart)
5. Write LONG-FORM educational posts (not first-person, not claiming I did the things)
6. Add videos to tracker
7. Stop when 10 posts created
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
POSTS_DIR = f'{WORKSPACE}/content/facebook-posts/timeline'
TRANSCRIPTS_DIR = f'{WORKSPACE}/personal-profile/transcripts'
TRACKER_FILE = f'{WORKSPACE}/personal-profile/video_tracker.md'
CREDENTIALS_FILE = '/root/.openclaw/workspace/credentials/supadata_api_key.txt'

# Niches to search (exactly as specified)
NICHES = [
    'mindset',
    'affiliate marketing',
    'network marketing',
    'entrepreneurship',
    'business',
    'wealth'
]

# YouTube search queries by niche
SEARCH_QUERIES = {
    'mindset': ['millionaire mindset secrets', 'success mindset psychology', 'mindset for entrepreneurs', 'growth mindset business'],
    'affiliate marketing': ['affiliate marketing strategies 2024', 'affiliate marketing tips', 'how to succeed affiliate marketing'],
    'network marketing': ['network marketing success tips', 'MLM strategies that work', 'direct sales training'],
    'entrepreneurship': ['entrepreneurship lessons', 'how to start a business', 'business growth strategies'],
    'business': ['business scaling strategies', 'business owner tips', 'how to grow business'],
    'wealth': ['wealth building strategies', 'financial freedom tips', 'passive income ideas']
}

def get_supadata_key():
    """Get Supadata API key"""
    with open(CREDENTIALS_FILE, 'r') as f:
        content = f.read().strip()
        if '=' in content:
            return content.split('=')[1].strip()
        return content

def load_video_tracker():
    """Load list of already used video URLs from tracker"""
    used_urls = set()
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, 'r') as f:
            content = f.read()
            # Extract YouTube URLs
            urls = re.findall(r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)', content)
            used_urls.update(urls)
    return used_urls

def search_youtube_videos(niche, max_results=10):
    """Search YouTube for videos in a niche"""
    queries = SEARCH_QUERIES.get(niche, [f'{niche} tips'])
    query = random.choice(queries)

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
                    videos.append({
                        'id': video_id,
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'title': item.get('title', 'Unknown'),
                        'channel': item.get('channel', {}).get('name', 'Unknown') if isinstance(item.get('channel'), dict) else 'Unknown'
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

def extract_transcript_text(transcript_data):
    """Extract full text from transcript"""
    if isinstance(transcript_data, dict) and 'content' in transcript_data:
        text_parts = [item.get('text', '') for item in transcript_data['content']]
        return ' '.join(text_parts)
    return str(transcript_data)

def extract_key_lessons(transcript_text, min_lessons=5):
    """
    Extract key educational lessons from transcript.
    Looking for actionable, valuable insights.
    """
    # Clean text
    text = re.sub(r'\s+', ' ', transcript_text).strip()

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

    # Keywords that indicate valuable content
    value_indicators = [
        'how to', 'step', 'first', 'second', 'third', 'next', 'then', 'finally',
        'strategy', 'method', 'approach', 'technique', 'tactic',
        'secret', 'key', 'important', 'critical', 'essential', 'crucial',
        'build', 'create', 'start', 'grow', 'scale', 'develop',
        'money', 'revenue', 'profit', 'sales', 'income', 'wealth', 'financial',
        'mistake', 'avoid', 'never', 'always', 'dont', 'stop', 'prevent',
        'because', 'this is why', 'the reason', 'therefore', 'as a result',
        'most people', 'the problem is', 'the solution is', 'what most dont realize',
        'here\'s the truth', 'the reality is', 'understand this'
    ]

    scored_sentences = []
    for sent in sentences:
        sent = sent.strip()
        # Look for substantial sentences (not too short, not too long)
        if len(sent) < 60 or len(sent) > 400:
            continue

        score = 0
        sent_lower = sent.lower()

        # Score based on value indicators
        for indicator in value_indicators:
            if indicator in sent_lower:
                score += 3

        # Bonus for actionable content
        if any(x in sent_lower for x in ['start by', 'begin with', 'focus on', 'the key is', 'what you need to']):
            score += 5

        # Bonus for contrarian/insightful statements
        if any(x in sent_lower for x in ['most people think', 'but the truth is', 'here\'s what actually', 'the problem with']):
            score += 4

        # Bonus for numbers/stats
        if re.search(r'\d+%|\$\d+|\d+ (days?|weeks?|months?|years?)', sent):
            score += 2

        if score >= 6:
            scored_sentences.append((sent, score))

    # Sort by score and return top lessons
    scored_sentences.sort(key=lambda x: x[1], reverse=True)

    # Ensure we have at least min_lessons
    lessons = [s[0] for s in scored_sentences[:min_lessons*2]]

    return lessons

def generate_long_form_post(lessons, video_title, niche):
    """
    Generate a LONG-FORM educational Facebook post.
    NOT first-person. NOT claiming I did these things.
    Educational value extraction from the transcript.
    """
    if not lessons or len(lessons) < 3:
        return None

    # Select best lessons (up to 7 for long-form)
    selected_lessons = lessons[:7]

    # Hook options - educational, not first-person
    hooks = [
        f"Some powerful insights from the world of {niche}:",
        f"Valuable lessons on {niche} worth considering:",
        f"Key perspectives on {niche} that can shift your approach:",
        f"Important concepts in {niche} that deserve attention:",
        f"Worthwhile insights about {niche}:"
    ]

    hook = random.choice(hooks)

    # Build the body with depth and context
    body_parts = []

    # Opening context
    body_parts.append(f"Understanding {niche} requires looking at what actually works versus what people assume works. Here are some key insights:")

    # Add lessons with context
    for i, lesson in enumerate(selected_lessons[:5], 1):
        # Clean up the lesson
        lesson = lesson.strip()
        if not lesson.endswith(('.', '!', '?')):
            lesson += '.'
        body_parts.append(f"\n{i}. {lesson}")

    # Add expansion on key concepts
    if len(selected_lessons) > 5:
        body_parts.append(f"\nAdditionally, consider this: {selected_lessons[5]}")

    # Closing insight
    closings = [
        f"\nThe common thread across successful {niche} approaches is consistency and willingness to adapt based on results.",
        f"\nWhat separates those who succeed in {niche} from those who don't is often simply the willingness to implement what they learn.",
        f"\nThese concepts aren't complicated, but they do require consistent application to see results.",
        f"\nThe question isn't whether these strategies work — it's whether you're willing to put them into practice.",
        f"\nKnowledge without action won't change your results. The key is taking these insights and applying them consistently."
    ]

    closing = random.choice(closings)
    body_parts.append(closing)

    # Call to action - engagement focused
    ctas = [
        f"\nWhich of these insights resonates most with where you are in your {niche} journey?",
        f"\nWhat's one concept here you could implement this week?",
        f"\nHave you found other approaches in {niche} that work well?",
        f"\nWhat's your biggest challenge when it comes to {niche}?",
        f"\nShare your thoughts — what would you add to this list?"
    ]

    cta = random.choice(ctas)

    # Combine everything
    full_post = f"{hook}\n\n" + "\n".join(body_parts) + f"\n{cta}"

    return full_post

def create_post(video_info, transcript_data, niche):
    """Create a Facebook post from video transcript"""
    transcript_text = extract_transcript_text(transcript_data)
    lessons = extract_key_lessons(transcript_text)

    if not lessons or len(lessons) < 3:
        print(f"    ✗ Not enough valuable content extracted")
        return None

    content = generate_long_form_post(lessons, video_info['title'], niche)
    if not content:
        return None

    post_id = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}"

    post = f"""---
id: {post_id}
status: UNUSED
created: {datetime.now().strftime('%Y-%m-%d')}
type: personal-profile
source: {video_info['url']}
niche: {niche}
channel: {video_info['channel']}
---

{content}
"""

    return {
        'id': post_id,
        'content': post,
        'video_info': video_info,
        'niche': niche
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

def update_posts_json(post_data):
    """Add post to posts.json index"""
    posts_json_path = f'{WORKSPACE}/content/facebook-posts/posts.json'

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
        'type': 'personal-profile',
        'niche': post_data['niche'],
        'source': post_data['video_info']['url']
    }
    posts.append(post_entry)

    os.makedirs(os.path.dirname(posts_json_path), exist_ok=True)
    with open(posts_json_path, 'w') as f:
        json.dump(posts, f, indent=2)

def main():
    """Main workflow"""
    print("=" * 70)
    print("CONTENT MACHINE v2 - Long-Form Educational Posts")
    print("=" * 70)

    # Load used videos from tracker
    used_videos = load_video_tracker()
    print(f"\n📋 Loaded {len(used_videos)} previously used videos from tracker")

    posts_created = 0
    target_posts = 10
    videos_processed = 0

    # Rotate through niches
    niche_cycle = random.sample(NICHES, len(NICHES))

    for niche in niche_cycle:
        if posts_created >= target_posts:
            break

        print(f"\n{'='*70}")
        print(f"🔍 Searching niche: {niche.upper()}")
        print(f"{'='*70}")

        # Search for videos
        videos = search_youtube_videos(niche, max_results=15)
        print(f"   Found {len(videos)} videos")

        for video in videos:
            if posts_created >= target_posts:
                break

            videos_processed += 1

            # Check if already used
            if video['id'] in used_videos:
                print(f"   ⏭️  Skipping (already in tracker): {video['title'][:60]}...")
                continue

            print(f"\n   📹 Processing: {video['title'][:60]}...")
            print(f"      Channel: {video['channel']}")

            # Fetch transcript
            transcript = fetch_transcript(video['id'])
            if not transcript:
                print(f"      ✗ No transcript available")
                continue

            print(f"      ✓ Transcript fetched")

            # Create post
            post_data = create_post(video, transcript, niche)

            if post_data:
                # Save post
                save_post(post_data)

                # Update tracker
                update_video_tracker(video, niche)
                used_videos.add(video['id'])

                # Update posts.json index
                update_posts_json(post_data)

                posts_created += 1
                post_length = len(post_data['content'])
                print(f"      ✓ Post created: {post_data['id']}")
                print(f"      📊 Post length: {post_length} characters")

                # Rate limiting - 30-60 seconds between posts
                if posts_created < target_posts:
                    wait_time = random.randint(30, 60)
                    print(f"      ⏳ Waiting {wait_time} seconds before next post...")
                    time.sleep(wait_time)
            else:
                print(f"      ✗ Failed to create post (insufficient valuable content)")

    print(f"\n{'='*70}")
    print(f"✅ COMPLETE")
    print(f"{'='*70}")
    print(f"   Videos processed: {videos_processed}")
    print(f"   Posts created: {posts_created}")
    print(f"   Target was: {target_posts}")
    print(f"{'='*70}")

    return posts_created

if __name__ == '__main__':
    main()
