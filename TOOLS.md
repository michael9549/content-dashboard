# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

### Dropbox Backup

- **Token location:** `/root/.openclaw/workspace/credentials/dropbox_token.txt`
- **Skill:** `dropbox-storage` (now installed globally)
- **Quick backup command:**
  ```bash
  export DROPBOX_ACCESS_TOKEN=$(cat /root/.openclaw/workspace/credentials/dropbox_token.txt) && \
  WORKSPACE_DIR="/root/.openclaw/workspace-content-machine" && \
  BACKUP_DIR="/content-machine-backup" && \
  TIMESTAMP=$(date +%Y-%m-%d-%H%M%S) && \
  BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP" && \
  curl -s -X POST https://api.dropboxapi.com/2/files/create_folder_v2 \
    --header "Authorization: Bearer $DROPBOX_ACCESS_TOKEN" \
    --header "Content-Type: application/json" \
    --data "{\"path\": \"$BACKUP_PATH\", \"autorename\": false}" && \
  find "$WORKSPACE_DIR" -type f \( -name "*.md" -o -name "*.json" -o -name "*.txt" \) ! -path "*/.git/*" | while read file; do
    rel_path="${file#$WORKSPACE_DIR/}"
    dropbox_file="$BACKUP_PATH/$rel_path"
    dir_path=$(dirname "$dropbox_file")
    curl -s -X POST https://api.dropboxapi.com/2/files/create_folder_v2 \
      --header "Authorization: Bearer $DROPBOX_ACCESS_TOKEN" \
      --header "Content-Type: application/json" \
      --data "{\"path\": \"$dir_path\", \"autorename\": false}" > /dev/null 2>&1 || true
    curl -s -X POST https://content.dropboxapi.com/2/files/upload \
      --header "Authorization: Bearer $DROPBOX_ACCESS_TOKEN" \
      --header "Content-Type: application/octet-stream" \
      --header "Dropbox-API-Arg: {\"path\": \"$dropbox_file\", \"mode\": \"overwrite\", \"autorename\": false}" \
      --data-binary @"$file" > /dev/null 2>&1
  done && echo "Backup complete: $BACKUP_PATH"
  ```

---

Add whatever helps you do your job. This is your cheat sheet.
