#!/usr/bin/env bash
# Nightly backup: Postgres dump + media. Add to cron: 0 3 * * * /srv/grabnar/repo/deploy/backup.sh
set -euo pipefail
DEST=/srv/backup/grabnar
DATE=$(date +%F)
mkdir -p "$DEST"
docker compose -f /srv/grabnar/repo/deploy/docker-compose.yml --env-file /srv/grabnar/cms.env exec -T db pg_dump -U grabnar grabnar | gzip > "$DEST/db-$DATE.sql.gz"
tar -czf "$DEST/media-$DATE.tar.gz" -C /srv/grabnar media
find "$DEST" -type f -mtime +14 -delete
# Offsite (configure rclone remote first): rclone sync "$DEST" linode-objstore:grabnar-backup
