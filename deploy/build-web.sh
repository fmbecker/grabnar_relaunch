#!/usr/bin/env bash
# Build the Astro site on the server and swap it in atomically.
# Called by rebuild-hook.py and deploy.sh. Requires node + pnpm on the host (e.g. via fnm).
#
# Build output (Astro static + @astrojs/node adapter):
#   web/dist/client/  static site          -> $OUT/dist     (served by Nginx)
#   web/dist/server/  SSR server (preview) -> $OUT/server   (grabnar-preview.service)
set -euo pipefail

REPO=${REPO:-/srv/grabnar/repo}
OUT=${OUT:-/srv/grabnar/web}
LOCK=/tmp/grabnar-build.lock

exec 9>"$LOCK"
flock -n 9 || { echo "build already running"; exit 0; }

cd "$REPO/web"
export ASTRO_TELEMETRY_DISABLED=1
export WAGTAIL_API_URL=${WAGTAIL_API_URL:-http://127.0.0.1:8000/api/v2}
export WAGTAIL_MEDIA_URL=${WAGTAIL_MEDIA_URL:-}            # same origin in production
export PUBLIC_SITE_URL=${PUBLIC_SITE_URL:-https://www.grabnar.de}
export PUBLIC_FORMS_API_URL=${PUBLIC_FORMS_API_URL:-https://www.grabnar.de/api/forms}

pnpm install --frozen-lockfile --prefer-offline
rm -rf dist
pnpm build

mkdir -p "$OUT"
node scripts/redirects.mjs > "$OUT/redirects.map.new"

# Static site: atomic swap, keep the previous version as dist.old for quick rollback.
rm -rf "$OUT/dist.old" "$OUT/server.old"
[ -d "$OUT/dist" ] && mv "$OUT/dist" "$OUT/dist.old"
mv dist/client "$OUT/dist"

# Preview server: same swap; node_modules resolve via a symlink to the repo checkout.
[ -d "$OUT/server" ] && mv "$OUT/server" "$OUT/server.old"
mv dist/server "$OUT/server"
ln -sfn "$REPO/web/node_modules" "$OUT/node_modules"
ln -sfn "$REPO/web/package.json" "$OUT/package.json"   # "type": "module" for entry.mjs

mv "$OUT/redirects.map.new" "$OUT/redirects.map"

# sudoers (see deploy/README.md):
#   felix ALL=(root) NOPASSWD: /usr/sbin/nginx -t, /usr/sbin/nginx -s reload, /usr/bin/systemctl restart grabnar-preview
if sudo -n /usr/sbin/nginx -t 2>/dev/null; then sudo -n /usr/sbin/nginx -s reload; fi
sudo -n /usr/bin/systemctl restart grabnar-preview 2>/dev/null || echo "WARN: could not restart grabnar-preview"
echo "deployed $(date -Is)"
