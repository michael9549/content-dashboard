# Content Machine Skill

## Purpose
Generate Facebook content for Michael's trading community. Creates posts for both timeline (personal-profile) and customer-group.

## Cron Job Trigger
When you receive the message: "FACEBOOK_CONTENT_CHECK: Spawn content-machine agent..."

**DO THIS:**
1. Run the content generation script: `python3 /root/.openclaw/workspace-content-machine/scripts/create_content.py`
2. This script will:
   - Check inventory levels in both folders
   - Create 10 timeline posts if < 5 (from YouTube transcripts)
   - Create 10 customer posts if < 5 (mindset/trading content)
   - Push results to GitHub
3. Report back what was created

## Manual Trigger
If Michael asks you to create content, run the same script.

## File Locations
- Timeline posts: `/content/facebook-posts/personal-profile/unused/`
- Customer posts: `/content/facebook-posts/customer-group/unused/`
- Script: `/scripts/create_content.py`
- Video tracker: `/personal-profile/video_tracker.md`

## Process
1. Check current inventory in both folders
2. If timeline < 5: Search YouTube → Get transcripts → Create 10 posts
3. If customer < 5: Generate 10 mindset/trading posts
4. Save to appropriate folders
5. Update posts.json indexes
6. Push to GitHub
7. Report results
