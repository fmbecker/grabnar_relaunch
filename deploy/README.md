# deploy/ – Linode-VPS

Verzeichnisse auf dem Server: `/srv/grabnar/{repo,web,media,cms-static,pg,logs}`, `/srv/grabnar/cms.env` (aus `cms/.env.example`, plus `POSTGRES_PASSWORD`).

Einmalige Einrichtung (Details: `docs/03-technik.md`):

1. Docker + Compose, Node 22 + pnpm (via fnm) installieren.
2. `git clone` nach `/srv/grabnar/repo`, `cms.env` anlegen.
3. `systemd/grabnar-rebuild.service` nach `/etc/systemd/system/`, `HOOK_SECRET` setzen (= `FRONTEND_BUILD_HOOK_SECRET` in `cms.env`; `FRONTEND_BUILD_HOOK_URL=http://host.docker.internal:9000/rebuild`), `systemctl enable --now grabnar-rebuild`.
4. Purge-Timer: beide `grabnar-purge-applications.*` nach `/etc/systemd/system/`, `systemctl enable --now grabnar-purge-applications.timer`.
5. `nginx/grabnar.conf` einbauen (zunächst als Staging-Server-Block auf Port 8443 mit Basic-Auth), certbot-Zeilen aus der bestehenden Config übernehmen.
6. `./deploy.sh` ausführen. Danach `docker compose … exec cms python manage.py createsuperuser`.
7. Backup: `backup.sh` in die root-Crontab.

Jedes weitere Deployment: `./deploy.sh`. Inhaltsänderungen im CMS bauen das Frontend automatisch neu (Webhook, 60 s Debounce).
