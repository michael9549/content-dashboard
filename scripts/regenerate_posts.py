#!/usr/bin/env python3
"""
Content Machine Post Regenerator
Regenerates Facebook posts using existing transcripts with AI-powered content extraction
"""

import json
import os
import re
import random
from datetime import datetime
from pathlib import Path

# Directory paths
POSTS_DIR = '/root/.openclaw/workspace-content-machine/content/facebook-posts/personal-profile/unused'
TRANSCRIPTS_DIR = '/root/.openclaw/workspace-content-machine/personal-profile/transcripts'

def extract_transcript_text(transcript_data):
    """Extract full text from transcript JSON"""
    if isinstance(transcript_data, dict) and 'content' in transcript_data:
        text_parts = [item['text'] for item in transcript_data['content']]
        return ' '.join(text_parts)
    return str(transcript_data)

def clean_text(text):
    """Clean up text for use in a post"""
    # Remove newlines and extra spaces
    text = text.replace('\n', ' ')
    text = ' '.join(text.split())
    return text.strip()

def extract_key_insights(transcript_text, niche):
    """Extract key educational insights from the transcript"""
    # Clean the text first
    clean_transcript = clean_text(transcript_text)
    
    # Split into sentences more carefully
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', clean_transcript)
    
    insights = []
    
    # Keywords that indicate valuable content
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
    
    # Filter and score sentences
    for sentence in sentences:
        sentence = sentence.strip()
        
        # Basic length filters
        if len(sentence) < 30:
            continue
        if len(sentence) > 250:
            # Try to split long sentences
            continue
            
        word_count = len(sentence.split())
        if word_count < 6:
            continue
            
        # Skip questions and incomplete sentences for main insights
        if sentence.endswith('?') or sentence.lower().startswith(('okay', 'so', 'um', 'uh')):
            continue
            
        # Score based on value keywords
        sentence_lower = sentence.lower()
        score = 0
        for kw in value_keywords:
            if kw in sentence_lower:
                score += 2
        
        # Bonus for actionable content
        if any(phrase in sentence_lower for phrase in ['start by', 'begin with', 'focus on', 'the key is']):
            score += 3
        if any(c.isdigit() for c in sentence):
            score += 1
            
        # Penalty for filler phrases
        filler_phrases = ['i think', 'i believe', 'maybe', 'sort of', 'kind of', 'you know']
        for filler in filler_phrases:
            if filler in sentence_lower:
                score -= 1
                
        if score >= 2:
            # Capitalize first letter
            sentence = sentence[0].upper() + sentence[1:]
            insights.append((sentence, score))
    
    # Sort by score and return top insights
    insights.sort(key=lambda x: x[1], reverse=True)
    
    # If we don't have enough scored insights, add some general ones
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
        return "The key insights from this content will help you approach things differently."
    
    if structure_type == 1:
        # Numbered list
        body = "Here are the key insights:\n\n"
        for i, insight in enumerate(insights[:5], 1):
            body += f"{i}. {insight}\n\n"
        return body.strip()
    
    elif structure_type == 2:
        # Bullet points
        body = "What stood out:\n\n"
        for insight in insights[:4]:
            body += f"→ {insight}\n\n"
        return body.strip()
    
    elif structure_type == 3:
        # Narrative style
        if len(insights) >= 3:
            body = f"First, {insights[0][0].lower() + insights[0][1:]}\n\n"
            body += f"Second, {insights[1][0].lower() + insights[1][1:]}\n\n"
            body += f"And perhaps most importantly: {insights[2][0].lower() + insights[2][1:]}"
            return body
        else:
            return "\n\n".join(insights)
    
    elif structure_type == 4:
        # Problem/solution style
        if len(insights) >= 2:
            body = f"The challenge: {insights[0]}\n\n"
            body += f"The approach that works: {insights[1]}\n\n"
            if len(insights) >= 3:
                body += f"The result: {insights[2]}"
            return body
        else:
            return "\n\n".join(insights)
    
    elif structure_type == 5:
        # Quote + analysis
        body = f"\"{insights[0]}\"\n\n"
        if len(insights) >= 2:
            body += f"This matters because {insights[1][0].lower() + insights[1][1:]}\n\n"
        if len(insights) >= 3:
            body += f"And it gets better: {insights[2][0].lower() + insights[2][1:]}"
        return body.strip()
    
    else:
        # Simple paragraph style with transitions
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

def parse_frontmatter(content):
    """Parse frontmatter from existing post"""
    frontmatter = {}
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            for line in fm_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()
    return frontmatter

def regenerate_post(post_file):
    """Regenerate a single post using its corresponding transcript"""
    # Read existing post
    with open(post_file, 'r') as f:
        post_content = f.read()
    
    # Parse frontmatter
    frontmatter = parse_frontmatter(post_content)
    
    # Find corresponding transcript
    post_id = frontmatter.get('id', '')
    transcript_file = os.path.join(TRANSCRIPTS_DIR, f"{post_id}.json")
    
    if not os.path.exists(transcript_file):
        print(f"  Transcript not found for {post_id}")
        return None
    
    # Read transcript
    with open(transcript_file, 'r') as f:
        transcript_data = json.load(f)
    
    transcript_text = extract_transcript_text(transcript_data)
    
    niche = frontmatter.get('niche', 'business')
    
    # Generate varied components
    hook = generate_varied_hook(niche)
    insights = extract_key_insights(transcript_text, niche)
    structure_type = random.randint(1, 6)
    body = format_body_structure(insights, niche, structure_type)
    cta = generate_varied_cta(niche)
    
    # Combine into full post
    new_post = f"{hook}\n\n{body}\n\n{cta}"
    
    # Reconstruct with frontmatter
    full_post = f"---\n"
    for key, value in frontmatter.items():
        full_post += f"{key}: {value}\n"
    full_post += f"---\n\n"
    full_post += new_post
    
    return full_post

def main():
    """Main regeneration workflow"""
    print("Starting Post Regeneration...")
    
    # Get all post files
    post_files = sorted([f for f in os.listdir(POSTS_DIR) if f.endswith('.md')])
    
    print(f"Found {len(post_files)} posts to regenerate")
    
    regenerated_count = 0
    
    for post_file in post_files:
        post_path = os.path.join(POSTS_DIR, post_file)
        print(f"\nRegenerating: {post_file}")
        
        try:
            new_post = regenerate_post(post_path)
            if new_post:
                # Write regenerated post
                with open(post_path, 'w') as f:
                    f.write(new_post)
                regenerated_count += 1
                print(f"  ✓ Regenerated successfully")
            else:
                print(f"  ✗ Failed to regenerate")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n\nComplete! Regenerated {regenerated_count}/{len(post_files)} posts.")

if __name__ == '__main__':
    main()
