#!/usr/bin/env bash
# Builds last week's Umami report and mails it via the CMS (same SMTP as the forms).
# Run by grabnar-umami-report.timer every Monday morning; by hand:
#   deploy/umami/send-report.sh [--week=2026-W47] [--month] [--month=2026-10]
# Config: /srv/grabnar/umami-report.env (template: deploy/umami/umami-report.env.example)
set -euo pipefail
REPO=${REPO:-/srv/grabnar/repo}
ENV_FILE=${ENV_FILE:-/srv/grabnar/umami-report.env}
set -a; source "$ENV_FILE"; set +a
: "${REPORT_RECIPIENTS:?REPORT_RECIPIENTS in $ENV_FILE setzen}"

out=$(mktemp --suffix=.html)
trap 'rm -f "$out"' EXIT
node "$REPO/deploy/umami/report.mjs" --out="$out" "$@"
subject="Website-Statistik $(grep -o '<title>[^<]*' "$out" | sed 's/<title>Website-Statistik //') – www.grabnar.de"
docker compose -f "$REPO/deploy/docker-compose.yml" --env-file /srv/grabnar/cms.env \
  exec -T cms python manage.py send_report_mail --to "$REPORT_RECIPIENTS" --subject "$subject" < "$out"
