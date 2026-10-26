#!/usr/bin/env bash
# Full deployment after a git push: run ON the Linode (or via: ssh linode 'bash -s' < deploy/deploy.sh).
set -euo pipefail
REPO=/srv/grabnar/repo
cd "$REPO"
git pull --ff-only
docker compose -f deploy/docker-compose.yml --env-file /srv/grabnar/cms.env build cms
docker compose -f deploy/docker-compose.yml --env-file /srv/grabnar/cms.env up -d
docker compose -f deploy/docker-compose.yml --env-file /srv/grabnar/cms.env exec -T cms python manage.py migrate --noinput
docker compose -f deploy/docker-compose.yml --env-file /srv/grabnar/cms.env exec -T cms python manage.py collectstatic --noinput
sudo systemctl restart grabnar-rebuild.service
"$REPO/deploy/build-web.sh"
