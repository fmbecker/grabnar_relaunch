# deploy/ – neuer VPS

Der Relaunch läuft auf einem **frischen VPS** (aktuelles Ubuntu LTS), nicht auf dem Linode der
Altseite. Erst unter `mbg.aivii.de` (Basic-Auth, nicht indexiert), nach dem DNS-Umzug unter
`www.grabnar.de` – Ablauf und Checkliste: `docs/09-domainumzug.md`.

Verzeichnisse auf dem Server: `/srv/grabnar/{repo,web,media,cms-static,pg,logs}`,
`/srv/grabnar/cms.env` (aus `cms/.env.example`, plus `POSTGRES_PASSWORD`),
`/srv/grabnar/web.env` (aus `deploy/web.env.example`: Domain und Indexierung des Frontends).

Einmalige Einrichtung (Details: `docs/03-technik.md`):

1. Grundsystem: Benutzer `felix` mit SSH-Key, Passwort-Login aus, Firewall (`ufw allow OpenSSH`,
   `ufw allow 80,443/tcp`), automatische Sicherheitsupdates (`unattended-upgrades`).
   Docker + Compose, Node 22 + pnpm (via fnm), `apache2-utils` (für `htpasswd`), certbot installieren.
   **nginx aus dem nginx.org-Repository**, mindestens 1.30.7 (stable) bzw. 1.31.9 (mainline) –
   ältere Versionen haben aus der Ferne ausnutzbare Lücken (CVE-2026-123007 u. a., 18.11.2026).
   `deploy.sh` bricht auf älteren Versionen ab (`check-nginx.sh`); nur wenn ein Distributionspaket
   die Korrektur nachweislich enthält: `NGINX_PATCHED=1 ./deploy.sh`. Das nginx.org-Paket kennt
   `sites-enabled/` nicht: `sudo mkdir /etc/nginx/sites-enabled` und `include /etc/nginx/sites-enabled/*;`
   im `http`-Block von `/etc/nginx/nginx.conf` ergänzen (die Proxy-Header liefert `nginx/proxy-params.conf`).
2. `git clone` nach `/srv/grabnar/repo`, `cms.env` und `web.env` anlegen (Phase-1-Werte mit `mbg.aivii.de`).
3. **Vorschau-Dienst:** `systemd/grabnar-preview.service` nach `/etc/systemd/system/`, `systemctl enable --now grabnar-preview` (Astro-SSR auf `127.0.0.1:4322`, Nginx leitet `/preview/` dorthin). `FRONTEND_URL` in `cms.env` = Adresse der Seite.
   sudoers-Eintrag (`visudo -f /etc/sudoers.d/grabnar`), damit `build-web.sh` nach jedem Build neu laden darf:
   `felix ALL=(root) NOPASSWD: /usr/sbin/nginx -t, /usr/sbin/nginx -s reload, /usr/bin/systemctl restart grabnar-preview`
3b. `systemd/grabnar-rebuild.service` nach `/etc/systemd/system/`, `HOOK_SECRET` setzen (= `FRONTEND_BUILD_HOOK_SECRET` in `cms.env`; `FRONTEND_BUILD_HOOK_URL=http://host.docker.internal:9000/rebuild`), `systemctl enable --now grabnar-rebuild`.
4. Purge-Timer: beide `grabnar-purge-applications.*` nach `/etc/systemd/system/`, `systemctl enable --now grabnar-purge-applications.timer`.
5. **Nginx** – die Configs werden direkt aus dem Repo verlinkt, Änderungen kommen mit jedem Deployment
   (`build-web.sh` prüft mit `nginx -t` und lädt neu). Genau **eine** davon ist aktiv:
   - `nginx/grabnar-staging.conf` – Phase 1, `mbg.aivii.de`, ganze Seite hinter Basic-Auth, `X-Robots-Tag: noindex`.
   - `nginx/grabnar.conf` – Phase 2, `www.grabnar.de`; `grabnar.de` und `mbg.aivii.de` leiten dorthin.
   - Gemeinsam: `nginx/site.conf` (alle Locations), `nginx/security-headers.conf`, `nginx/cms-proxy.conf`, `nginx/proxy-params.conf`.
   Einrichtung Phase 1 (Zertifikat, Basic-Auth, Symlink): `docs/09-domainumzug.md`.
   - HTTP/2 ist aus. Nach Prüfung der nginx-Version `http2 on;` in allen 443-Server-Blöcken ergänzen (`check-nginx.sh` weist darauf hin).
   - Zusätzliche Zugangsbeschränkung für die Redaktion (IP-Allowlist) in `location ~ ^/(admin|django-admin)/` in `site.conf` einkommentieren – gilt für Wagtail- und Django-Admin.
5b. **Mail:** SMTP-Zugang eines Postfachs unter `aivii.de` in `cms.env` (`EMAIL_URL`, `DEFAULT_FROM_EMAIL`); SPF/DKIM für `aivii.de` müssen den SMTP-Server abdecken. Formular-Mails setzen `Reply-To` auf die Adresse aus dem Formular.
6. **CMS-Image:** wird bei jedem Push auf `main` von GitHub Actions gebaut (`.github/workflows/cms.yml`, Job `image`) und als `ghcr.io/fmbecker/grabnar-cms` veröffentlicht. Einmalig auf GitHub unter *Packages → grabnar-cms → Package settings* die Sichtbarkeit auf **Public** stellen (das Image enthält nur den öffentlichen Code, keine Zugangsdaten). Alternativ privat lassen und auf dem Server `docker login ghcr.io -u fmbecker` mit einem Token (Recht `read:packages`).
   `./deploy.sh` ausführen. Danach `docker compose … exec cms python manage.py createsuperuser`.
7. **Einmalig** die Inhalte der Altseite importieren (ersetzt den Seitenbaum!):
   `docker compose -f deploy/docker-compose.yml --env-file /srv/grabnar/cms.env run --rm -v /srv/grabnar/repo/docs:/docs:ro cms python manage.py import_legacy --source /docs`
8. Backup: `backup.sh` in die root-Crontab.
9. Optional: Monatsbericht aus Umami per E-Mail – `systemd/grabnar-umami-report.{service,timer}`, Einrichtung in `docs/05-tracking.md` („Monatsbericht per E-Mail“). `felix` muss dafür in der Gruppe `docker` sein.

Jedes weitere Deployment: `./deploy.sh`. Es lädt das Image passend zum ausgecheckten Code (Tag `cms-<Tree-Hash von cms/>`) und wartet bis zu 15 Minuten, falls GitHub Actions noch baut. Auf dem Server wird nichts kompiliert.

- Zurückrollen: `CMS_IMAGE=ghcr.io/fmbecker/grabnar-cms:cms-<hash> ./deploy.sh` (der zuletzt laufende Tag steht in `/srv/grabnar/cms-image.txt`, alle Tags unter *Packages* auf GitHub).
- Notfall ohne GitHub: `BUILD_LOCAL=1 ./deploy.sh` baut auf dem Server (braucht ca. 1 GB freien RAM). Inhaltsänderungen im CMS bauen das Frontend automatisch neu (Webhook, 60 s Debounce).
