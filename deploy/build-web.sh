#!/usr/bin/env bash
# Build the Astro site on the server and swap it in atomically.
# Called by rebuild-hook.py and deploy.sh. Requires node + pnpm on the host (e.g. via fnm).
set -euo pipefail

REPO=${REPO:-/srv/grabnar/repo}
OUT=${OUT:-/srv/grabnar/web}
LOCK=/tmp/grabnar-build.lock

exec 9>"$LOCK"
flock -n 9 || { echo "build already running"; exit 0; }

cd "$REPO/web"
export WAGTAIL_API_URL=${WAGTAIL_API_URL:-http://127.0.0.1:8000/api/v2}
export WAGTAIL_MEDIA_URL=${WAGTAIL_MEDIA_URL:-}            # same origin in production
export PUBLIC_SITE_URL=${PUBLIC_SITE_URL:-https://www.grabnar.de}
export PUBLIC_FORMS_API_URL=${PUBLIC_FORMS_API_URL:-https://www.grabnar.de/api/forms}

pnpm install --frozen-lockfile --prefer-offline
rm -rf dist
pnpm build
node scripts/redirects.mjs > "$OUT/redirects.map.new"

mkdir -p "$OUT"
rm -rf "$OUT/dist.old"
[ -d "$OUT/dist" ] && mv "$OUT/dist" "$OUT/dist.old"
mv dist "$OUT/dist"
mv "$OUT/redirects.map.new" "$OUT/redirects.map"

# sudoers: felix ALL=(root) NOPASSWD: /usr/sbin/nginx -t, /usr/sbin/nginx -s reload
if sudo -n /usr/sbin/nginx -t 2>/dev/null; then sudo -n /usr/sbin/nginx -s reload; fi
echo "deployed $(date -Is)"
