#!/usr/bin/env bash
# Full deployment after a git push: run ON the Linode (or via: ssh linode 'bash -s' < deploy/deploy.sh).
#
# The CMS image comes ready-built from GitHub Actions (ghcr.io/fmbecker/grabnar-cms). Its tag
# "cms-<hash>" is the git tree hash of cms/, so this script pulls exactly the image that matches
# the checked-out code and waits while CI is still building it.
#   BUILD_LOCAL=1 ./deploy.sh   build on the server instead (fallback, needs ~1 GB free RAM)
#   CMS_IMAGE=ghcr.io/fmbecker/grabnar-cms:cms-<hash> ./deploy.sh   pin a specific image (rollback)
set -euo pipefail
REPO=/srv/grabnar/repo
REGISTRY_IMAGE=${REGISTRY_IMAGE:-ghcr.io/fmbecker/grabnar-cms}
WAIT_MINUTES=${WAIT_MINUTES:-15}
compose() { docker compose -f deploy/docker-compose.yml --env-file /srv/grabnar/cms.env "$@"; }

cd "$REPO"
git pull --ff-only

if [[ "${BUILD_LOCAL:-0}" == "1" ]]; then
  export CMS_IMAGE="grabnar-cms:local-$(git rev-parse --short=12 HEAD:cms)"
  compose build cms
else
  export CMS_IMAGE="${CMS_IMAGE:-$REGISTRY_IMAGE:cms-$(git rev-parse --short=12 HEAD:cms)}"
  echo "CMS-Image: $CMS_IMAGE"
  deadline=$((SECONDS + WAIT_MINUTES * 60))
  until docker pull -q "$CMS_IMAGE"; do
    if (( SECONDS >= deadline )); then
      echo "Image nach ${WAIT_MINUTES} Minuten nicht verfügbar. GitHub Actions (Workflow 'cms') prüfen" >&2
      echo "oder mit BUILD_LOCAL=1 auf dem Server bauen." >&2
      exit 1
    fi
    echo "… noch nicht in der Registry (CI baut vermutlich noch), neuer Versuch in 20 s"
    sleep 20
  done
fi

compose up -d
compose exec -T cms python manage.py migrate --noinput
compose exec -T cms python manage.py collectstatic --noinput
echo "$CMS_IMAGE" > /srv/grabnar/cms-image.txt   # what is running now (for rollbacks)
docker image prune -f --filter "until=168h" >/dev/null || true
sudo systemctl restart grabnar-rebuild.service
"$REPO/deploy/build-web.sh"
