#!/usr/bin/env bash
# Builds last month's Umami report and mails it via the CMS (same SMTP as the forms).
# Run by grabnar-umami-report.timer on the 1st of each month; by hand:
#   deploy/umami/send-monthly-report.sh [--month=2026-10]
# Config: /srv/grabnar/umami-report.env (template: deploy/umami/umami-report.env.example)
set -euo pipefail
REPO=${REPO:-/srv/grabnar/repo}
ENV_FILE=${ENV_FILE:-/srv/grabnar/umami-report.env}
set -a; source "$ENV_FILE"; set +a
: "${REPORT_RECIPIENTS:?REPORT_RECIPIENTS in $ENV_FILE setzen}"

out=$(mktemp --suffix=.html)
trap 'rm -f "$out"' EXIT
node "$REPO/deploy/umami/monthly-report.mjs" --out="$out" "$@"
subject="Website-Statistik $(grep -o '<title>[^<]*' "$out" | sed 's/<title>Website-Statistik //') – www.grabnar.de"
docker compose -f "$REPO/deploy/docker-compose.yml" --env-file /srv/grabnar/cms.env \
  exec -T cms python manage.py send_report_mail --to "$REPORT_RECIPIENTS" --subject "$subject" < "$out"
