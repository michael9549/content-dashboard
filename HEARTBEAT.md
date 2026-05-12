# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

## Nightly Content Check
**Trigger message:** "Check content levels and create posts if needed"
**When:** Every night at 2 AM

When this message is received:
1. Run `/root/.openclaw/workspace-content-machine/scripts/check_and_create_content.sh`
2. This will check if timeline posts are 5 or less
3. If so, it will run the content workflow to create 10 new posts
4. Each post takes ~4 minutes (Supadata rate limiting)
5. Total time: ~40 minutes for 10 posts
