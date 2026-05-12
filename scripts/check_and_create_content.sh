#!/bin/bash
# Check content levels and create new posts if needed

cd /root/.openclaw/workspace-content-machine

# Sync with GitHub first
git pull origin main

# Count unused timeline posts
TIMELINE_COUNT=$(find content/facebook-posts/personal-profile/unused/ -name "*.md" -type f | wc -l)

echo "Current timeline posts: $TIMELINE_COUNT"

# If 5 or less, create 10 new posts
if [ "$TIMELINE_COUNT" -le 5 ]; then
    echo "Timeline posts low ($TIMELINE_COUNT). Creating 10 new posts..."
    python3 scripts/content_workflow.py
else
    echo "Timeline posts sufficient ($TIMELINE_COUNT). No action needed."
fi
