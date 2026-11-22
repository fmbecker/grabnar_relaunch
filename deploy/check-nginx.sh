#!/usr/bin/env bash
# Refuse to deploy on an nginx with known remotely exploitable bugs.
#
# nginx 1.30.7 (stable) and 1.31.9 (mainline), 18.11.2026, fix CVE-2026-123007 (memory corruption
# in HTTP/2 flow control, rated "major") and further CVEs, some of them independent of HTTP/2
# (e.g. CVE-2026-118899, request bodies over TLS 1.3) – switching HTTP/2 off is not enough.
# Releases before 1.30 get no fix from nginx.org: install nginx from the nginx.org repository.
#
# A distribution package can carry the fix with an older version number. Only then:
#   NGINX_PATCHED=1 ./deploy.sh      (after checking the distribution's security notice)
set -euo pipefail

# deploy.sh runs as felix, whose PATH has no /usr/sbin – call nginx by its path then.
nginx_bin=$(command -v nginx || echo /usr/sbin/nginx)
version=$("$nginx_bin" -v 2>&1 | sed -n 's|.*nginx/\([0-9.]*\).*|\1|p')
if [[ -z "$version" ]]; then
  echo "nginx-Version nicht ermittelbar (nginx -v)." >&2
  exit 1
fi

ge() { [[ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1)" == "$2" ]]; }   # $1 >= $2
IFS=. read -r major minor _ <<< "$version"
fixed=no
if [[ "$major" -gt 1 ]]; then fixed=yes
elif [[ "$major" -eq 1 && "$minor" -eq 30 ]] && ge "$version" 1.30.7; then fixed=yes
elif [[ "$major" -eq 1 && "$minor" -ge 31 ]] && ge "$version" 1.31.9; then fixed=yes
fi

if [[ "$fixed" == yes ]]; then
  echo "nginx $version: enthält die Sicherheitskorrekturen vom 18.11.2026."
  if ! "$nginx_bin" -T 2>/dev/null | grep -Eq '^\s*http2\s+on;'; then
    echo "Hinweis: HTTP/2 ist aus. Kann jetzt mit 'http2 on;' in beiden 443-Server-Blöcken eingeschaltet werden."
  fi
  exit 0
fi

if [[ "${NGINX_PATCHED:-0}" == "1" ]]; then
  echo "nginx $version: als gepatcht bestätigt (NGINX_PATCHED=1)."
  exit 0
fi

cat >&2 <<MSG
nginx $version ist von CVE-2026-123007 und weiteren Lücken betroffen (behoben in 1.30.7 / 1.31.9).
Bitte nginx aus dem nginx.org-Repository aktualisieren, dann erneut deployen.
Nur falls das Distributionspaket die Korrektur nachweislich enthält: NGINX_PATCHED=1 ./deploy.sh
MSG
exit 1
