#!/bin/bash
# Content Machine Workflow Runner

echo "=========================================="
echo "Content Machine - Workflow Starting"
echo "=========================================="

WORKSPACE="/root/.openclaw/workspace-content-machine"
cd "$WORKSPACE"

# Run the Python script
echo ""
echo "Generating content..."
python3 scripts/create_content.py

# Check if posts were created
POST_COUNT=$(ls -1 content/facebook-posts/personal-profile/unused/*.md 2>/dev/null | wc -l)
echo ""
echo "Posts created: $POST_COUNT"

# Push to GitHub if posts exist
if [ "$POST_COUNT" -gt 0 ]; then
    echo ""
    echo "Pushing to GitHub..."
    git add content/facebook-posts/personal-profile/unused/
    git add personal-profile/transcripts/
    git add personal-profile/video_tracker.md
    git commit -m "Add $POST_COUNT new posts - $(date +%Y-%m-%d)"
    git push origin main
    echo "✓ Pushed to GitHub"
else
    echo "✗ No posts to push"
fi

echo ""
echo "=========================================="
echo "Workflow Complete"
echo "=========================================="
