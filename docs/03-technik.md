# 03 – Technik: Architektur, Entscheidungen, Migration

## Entscheidung

**Headless Wagtail (API v2) + Astro (SSG) + Tailwind CSS + React-Islands nur wo nötig.**

Geprüfte Alternativen:

| Option | Verworfen, weil |
|---|---|
| Wagtail + coderedcms upgraden | Zwei Jahre Rückstand bei beiden Paketen, Bootstrap-Frontend, hohe Upgrade-Kopplung an CodeRed |
| Wagtail monolithisch (Django-Templates, Tailwind, HTMX) | Weniger Infrastruktur, aber Frontend-Lebenszyklus bleibt an Wagtail-Upgrades gekoppelt; Felix' Stärken (React/TS) ungenutzt |
| Komplett statisch ohne CMS (Astro + Markdown) | Redakteure der Firma können nicht selbst pflegen |
| Next.js statt Astro | Für eine fast vollständig statische Seite zu viel Laufzeit-JS; Astro-Islands reichen |

## Komponenten

### CMS (`cms/`)

- Python ≥ 3.12, Wagtail aktuelle LTS, Django passend dazu, Postgres 16. Exakte Versionen beim Aufsetzen prüfen (`pip index versions wagtail`), Pins in `cms/pyproject.toml`.
- Paketverwaltung: `uv` (schnell, Lockfile). Alternativ pip-tools.
- Apps: `home`, `services`, `jobs`, `blocks`, `site_settings`, `forms_api`.
- API: `wagtail.api.v2` unter `/api/v2/`; eigener `PagesAPIViewSet` in `cms/grabnar/api.py`, der StreamField als JSON (`api_fields`) liefert, Bilder als Renditions (`ImageRenditionField` mit festen Größen `fill-800x450`, `width-1600` usw.).
- Site-Settings per API: eigener kleiner Endpunkt `/api/v2/settings/` (Wagtail liefert Settings nicht von Haus aus).
- Redirects per API: `/api/v2/redirects/` → Frontend erzeugt daraus `_redirects` (Cloudflare/Netlify) bzw. Nginx-Map beim Build.
- Preview: `wagtail-headless-preview` → `PREVIEW_URL` zeigt auf eine Astro-Route `/preview/` im SSR-Modus oder auf einen laufenden `astro dev`.
- Formulare: `cms/forms_api/` als Django-Views (DRF optional): `POST /api/forms/contact/`, `POST /api/forms/application/` (multipart, Lebenslauf max. 10 MB, erlaubte Typen PDF/DOCX). Speicherung als `FormSubmission`-Model im Admin + Mail an Firma. Spam-Schutz: Honeypot + Zeitstempel, kein externes CAPTCHA.
- Publish-Hook: `cms/grabnar/signals.py` lauscht auf `page_published`/`page_unpublished` und ruft `FRONTEND_BUILD_HOOK_URL` (Deploy-Hook) auf, mit 60 s Debounce.
- Deployment: `cms/Dockerfile` (gunicorn), `docker-compose.yml` mit `cms`, `db`, optional `nginx`. Admin nur über VPN/IP-Allowlist oder Basic-Auth vor `/admin/`.

### Frontend (`web/`)

- Astro (aktuelle Major), `output: "static"`, Tailwind über `@astrojs/tailwind` bzw. Tailwind v4 Vite-Plugin (beim Aufsetzen prüfen, was aktuell empfohlen ist).
- React nur in `src/components/islands/*.tsx` mit `client:visible`/`client:idle`: `ContactForm`, `ApplicationForm`, `JobFilter`, `GalleryLightbox`.
- Datenzugriff zur Build-Zeit in `src/lib/wagtail.ts` (`fetch` gegen `WAGTAIL_API_URL`), Typen in `src/lib/types.ts`. Optional: Typen aus einem OpenAPI-Schema generieren, falls das CMS `drf-spectacular` bekommt.
- Routing: `src/pages/[...slug].astro` mit `getStaticPaths()` aus `/api/v2/pages/?type=…&fields=…`. Pro Seitentyp eine Layout-Komponente, Blocks per `switch(block.type)` auf die Komponenten gemappt.
- Bilder: Wagtail-Renditions, `<picture>` mit `srcset`, `loading="lazy"`.
- SEO: `src/components/Seo.astro` (Title, Description, OG, Canonical), `@astrojs/sitemap`, JSON-LD `LocalBusiness` auf Home/Kontakt, `JobPosting` auf JobPage.
- Fonts selbst gehostet (`public/fonts/`), kein externes CDN.
- Hosting: siehe Abschnitt „Hosting auf dem Linode-VPS“ – statisches Build-Verzeichnis `web/dist/` wird von Nginx ausgeliefert.

## Hosting auf dem Linode-VPS (entschieden)

Die bestehende Linode-Instanz bleibt. `www.grabnar.de` zeigt extern verwaltet auf deren IP – deshalb **keine neue Subdomain**, CMS und Frontend laufen unter derselben Domain, getrennt nach Pfad. So ist kein DNS-Eingriff nötig.

```
Internet → Nginx (:443, www.grabnar.de)
            ├── /                → /srv/grabnar/web/dist/        (statische Astro-Dateien)
            ├── /admin/, /api/   → proxy_pass http://127.0.0.1:8000  (Wagtail, Docker)
            ├── /media/          → /srv/grabnar/media/            (Wagtail-Uploads, Renditions)
            ├── /django-static/  → /srv/grabnar/cms-static/       (Admin-Assets)
            └── /_hooks/rebuild  → proxy_pass http://127.0.0.1:9000  (Build-Webhook)
```

- `/admin/` zusätzlich mit `allow <Firmen-IP>; allow <Felix-IP>; deny all;` oder Basic-Auth absichern (`auth_basic`). Die `/api/` bleibt offen, liefert aber nur veröffentlichte Inhalte.
- Verzeichnisse auf dem Server: `/srv/grabnar/repo/` (Git-Checkout), `/srv/grabnar/web/dist/` (Build-Ausgabe, atomar per `mv` getauscht), `/srv/grabnar/media/`, `/srv/grabnar/pg/` (Postgres-Volume).
- CMS: `docker compose -f /srv/grabnar/repo/docker-compose.yml up -d` mit Services `cms` (gunicorn, Port 8000 nur auf 127.0.0.1) und `db` (Postgres). Media als Bind-Mount.
- Frontend-Build **auf dem Server**: kleiner Webhook-Dienst (`deploy/rebuild-hook.py`, Python stdlib `http.server`, systemd-Unit `grabnar-rebuild.service`), der bei `POST /_hooks/rebuild` mit gültigem `X-Hook-Secret` das Skript `deploy/build-web.sh` ausführt: `git pull`, `pnpm install --frozen-lockfile`, `pnpm build` nach `dist.new/`, dann atomar `mv dist dist.old && mv dist.new dist`. Debounce 60 s, Lock-Datei gegen Parallelbuilds. Node/pnpm auf dem Host nötig (z. B. via `fnm`).
- Der Wagtail-Signal-Handler ruft `FRONTEND_BUILD_HOOK_URL=http://127.0.0.1:9000/rebuild` auf (intern, nicht über Nginx).
- Redirects: `web` erzeugt beim Build aus `/api/v2/redirects/` eine Nginx-`map`-Datei `/srv/grabnar/web/redirects.map`; Nginx lädt sie per `include` und wird nach dem Build mit `nginx -s reload` neu geladen (sudoers-Regel nur für diesen Befehl).
- TLS: bestehendes Let's-Encrypt-Setup (certbot) weiternutzen. ⬜ prüfen, ob certbot aktuell und automatisch erneuert.
- Alte Wagtail/CodeRed-Installation: parallel laufen lassen, bis Nginx umgeschaltet ist, dann stoppen und nach 4 Wochen entfernen.

### Deploy-Workflow

1. `git push` nach `main` → GitHub Actions (`cms.yml`, `web.yml`) prüft Lint/Tests/Build.
2. Deployment per `deploy/deploy.sh` (SSH auf den Linode): `git pull`, `docker compose build cms`, `docker compose up -d`, `manage.py migrate`, `collectstatic`, danach `build-web.sh`.
3. Inhaltsänderungen im CMS lösen nur den Frontend-Rebuild aus, kein Deployment.

### Backup

- Nächtlich `pg_dump` + `tar` von `/srv/grabnar/media/` nach `/srv/backup/` und per `rclone`/Linode Object Storage offsite (⬜ Ziel klären). Linode-Backup-Service als zweite Ebene, falls gebucht.

### CI (`.github/workflows/`)

- `cms.yml`: ruff, `manage.py check`, Migrations-Check, Tests, Docker-Build.
- `web.yml`: `pnpm lint`, `astro check`, Build gegen Staging-API.

## Lokale Entwicklung

```
docker compose up db                 # Postgres
cd cms && uv run manage.py migrate && uv run manage.py runserver   # http://localhost:8000/admin/
cd web && pnpm dev                   # http://localhost:4321, WAGTAIL_API_URL=http://localhost:8000/api/v2
```

Seed: `cms/fixtures/dev.json` mit Beispielseiten für alle Blocks, damit das Frontend ohne echte Inhalte entwickelt werden kann.

## Migration von der Altseite

1. Inhalte exportieren (siehe `docs/01-ist-analyse.md`): Texte als Markdown nach `docs/content-export/`, Bilder nach `cms/fixtures/media/`.
2. Alte URL-Liste → Mapping-Tabelle `docs/redirects.csv` (`alt,neu,status`) → beim Go-Live als `wagtail.contrib.redirects` importieren (Management-Command `import_redirects`).
3. Go-Live-Reihenfolge (alles auf demselben Linode, kein DNS-Wechsel): neues CMS auf Port 8000 parallel zur Altinstallation starten → Inhalte einpflegen, Admin über `/admin-neu/` (temporärer Nginx-Pfad) → Frontend-Build unter `/srv/grabnar/web/dist/` erzeugen und über einen Staging-Server-Block (z. B. Port 8443 mit Basic-Auth) abnehmen → Nginx-Konfiguration für `www.grabnar.de` auf die neue Struktur umschalten (`nginx -t && nginx -s reload`) → Altinstallation stoppen, 4 Wochen aufbewahren.
4. Google Search Console: Sitemap neu einreichen, 404-Report nach Go-Live wöchentlich prüfen.

## Datenschutz

- Keine externen Requests im Frontend (Fonts, Maps, Analytics) ohne Consent.
- Karte als statisches Bild oder selbst gehostetes Leaflet mit OSM-Tiles von eigenem Proxy, sonst Consent-Overlay.
- Bewerbungsdaten: Löschfrist (z. B. 6 Monate) als Management-Command `purge_applications`, im Admin dokumentiert.
- Analytics falls gewünscht: selbst gehostetes Plausible/Umami, cookielos.
