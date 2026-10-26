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
6. `./deploy.sh` ausführen. Danach `docker compose … exec cms python manage.py createsuperuser`.
7. **Einmalig** die Inhalte der Altseite importieren (ersetzt den Seitenbaum!):
   `docker compose -f deploy/docker-compose.yml --env-file /srv/grabnar/cms.env run --rm -v /srv/grabnar/repo/docs:/docs:ro cms python manage.py import_legacy --source /docs`
8. Backup: `backup.sh` in die root-Crontab.

Jedes weitere Deployment: `./deploy.sh`. Inhaltsänderungen im CMS bauen das Frontend automatisch neu (Webhook, 60 s Debounce).
