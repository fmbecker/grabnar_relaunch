# deploy/ – Linode-VPS

Verzeichnisse auf dem Server: `/srv/grabnar/{repo,web,media,cms-static,pg,logs}`, `/srv/grabnar/cms.env` (aus `cms/.env.example`, plus `POSTGRES_PASSWORD`).

Einmalige Einrichtung (Details: `docs/03-technik.md`):

1. Docker + Compose, Node 22 + pnpm (via fnm) installieren.
2. `git clone` nach `/srv/grabnar/repo`, `cms.env` anlegen.
3. **Vorschau-Dienst:** `systemd/grabnar-preview.service` nach `/etc/systemd/system/`, `systemctl enable --now grabnar-preview` (Astro-SSR auf `127.0.0.1:4322`, Nginx leitet `/preview/` dorthin). In `cms.env`: `FRONTEND_URL=https://www.grabnar.de`.
   sudoers-Eintrag (`visudo -f /etc/sudoers.d/grabnar`), damit `build-web.sh` nach jedem Build neu laden darf:
   `felix ALL=(root) NOPASSWD: /usr/sbin/nginx -t, /usr/sbin/nginx -s reload, /usr/bin/systemctl restart grabnar-preview`
3b. `systemd/grabnar-rebuild.service` nach `/etc/systemd/system/`, `HOOK_SECRET` setzen (= `FRONTEND_BUILD_HOOK_SECRET` in `cms.env`; `FRONTEND_BUILD_HOOK_URL=http://host.docker.internal:9000/rebuild`), `systemctl enable --now grabnar-rebuild`.
4. Purge-Timer: beide `grabnar-purge-applications.*` nach `/etc/systemd/system/`, `systemctl enable --now grabnar-purge-applications.timer`.
5. `nginx/grabnar.conf` einbauen (zunächst als Staging-Server-Block auf Port 8443 mit Basic-Auth), certbot-Zeilen aus der bestehenden Config übernehmen.
   - **nginx mindestens 1.30.7 (stable) bzw. 1.31.9 (mainline)**, aus dem nginx.org-Repository – ältere Versionen haben aus der Ferne ausnutzbare Lücken (CVE-2026-123007 u. a., 18.11.2026), für Versionen vor 1.30 gibt es keine Korrektur. `deploy.sh` bricht auf älteren Versionen ab (`check-nginx.sh`); nur wenn das Distributionspaket die Korrektur nachweislich enthält: `NGINX_PATCHED=1 ./deploy.sh`.
   - HTTP/2 ist in `grabnar.conf` aus. Nach dem Update `http2 on;` in beiden 443-Server-Blöcken ergänzen (`check-nginx.sh` weist darauf hin).
   - Die Sicherheits-Header (`nginx/security-headers.conf`) und der CMS-Proxy (`nginx/cms-proxy.conf`) werden direkt aus `/srv/grabnar/repo/deploy/nginx/` eingebunden; Änderungen daran wirken nach dem nächsten Deployment (`build-web.sh` prüft mit `nginx -t` und lädt neu).
   - Zugangsbeschränkung (IP-Allowlist oder Basic-Auth) in `location ~ ^/(admin|django-admin)/` einkommentieren – sie gilt für Wagtail- und Django-Admin.
6. **CMS-Image:** wird bei jedem Push auf `main` von GitHub Actions gebaut (`.github/workflows/cms.yml`, Job `image`) und als `ghcr.io/fmbecker/grabnar-cms` veröffentlicht. Einmalig auf GitHub unter *Packages → grabnar-cms → Package settings* die Sichtbarkeit auf **Public** stellen (das Image enthält nur den öffentlichen Code, keine Zugangsdaten). Alternativ privat lassen und auf dem Server `docker login ghcr.io -u fmbecker` mit einem Token (Recht `read:packages`).
   `./deploy.sh` ausführen. Danach `docker compose … exec cms python manage.py createsuperuser`.
7. **Einmalig** die Inhalte der Altseite importieren (ersetzt den Seitenbaum!):
   `docker compose -f deploy/docker-compose.yml --env-file /srv/grabnar/cms.env run --rm -v /srv/grabnar/repo/docs:/docs:ro cms python manage.py import_legacy --source /docs`
8. Backup: `backup.sh` in die root-Crontab.
9. Optional: Monatsbericht aus Umami per E-Mail – `systemd/grabnar-umami-report.{service,timer}`, Einrichtung in `docs/05-tracking.md` („Monatsbericht per E-Mail“). `felix` muss dafür in der Gruppe `docker` sein.

Jedes weitere Deployment: `./deploy.sh`. Es lädt das Image passend zum ausgecheckten Code (Tag `cms-<Tree-Hash von cms/>`) und wartet bis zu 15 Minuten, falls GitHub Actions noch baut. Auf dem Server wird nichts kompiliert.

- Zurückrollen: `CMS_IMAGE=ghcr.io/fmbecker/grabnar-cms:cms-<hash> ./deploy.sh` (der zuletzt laufende Tag steht in `/srv/grabnar/cms-image.txt`, alle Tags unter *Packages* auf GitHub).
- Notfall ohne GitHub: `BUILD_LOCAL=1 ./deploy.sh` baut auf dem Server (braucht ca. 1 GB freien RAM). Inhaltsänderungen im CMS bauen das Frontend automatisch neu (Webhook, 60 s Debounce).
