#!/usr/bin/env bash
# Nginx liest die Zertifikate beim Start und behält sie im Speicher: nach einer Erneuerung
# liefert es weiter das alte, bis es neu geladen wird – bis zum Ablauf, also bis zu 30 Tage
# später. Certbot ruft dieses Skript nach jeder erfolgreichen Erneuerung auf.
#
# Installieren (als root, nicht verlinken – certbot führt Hooks als root aus):
#   sudo install -m 755 /srv/grabnar/repo/deploy/certbot-reload-nginx.sh \
#        /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
# Testen: sudo certbot renew --dry-run --run-deploy-hooks
set -euo pipefail

# Eine fehlerhafte Config würde den laufenden nginx beim Reload nicht umbringen, aber die
# Erneuerung als gescheitert melden – deshalb erst prüfen, dann laden.
if ! nginx -t 2>/dev/null; then
    echo "certbot-reload-nginx: nginx -t schlägt fehl, kein Reload." >&2
    exit 1
fi
systemctl reload nginx
echo "certbot-reload-nginx: nginx neu geladen (${RENEWED_DOMAINS:-unbekannt})."
