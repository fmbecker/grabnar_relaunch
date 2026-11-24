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
- Preview: `wagtail-headless-preview` (Setting **`WAGTAIL_HEADLESS_PREVIEW`**, `CLIENT_URLS.default = FRONTEND_URL + "/preview/"`). Endpunkt `/api/v2/page_preview/?content_type=&token=` liefert den ungespeicherten Entwurf (Token ist signiert, Antwort `no-store`). Details im Abschnitt „Live-Vorschau“.
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
- Hosting: siehe Abschnitt „Hosting auf neuem VPS“ – statisches Build-Verzeichnis `web/dist/` wird von Nginx ausgeliefert.

## Live-Vorschau für Redakteure

```
Wagtail-Editor (Vorschau-Panel)
  └─ iframe /admin/pages/<id>/edit/preview/      Wagtail speichert Entwurf als PagePreview (signierter Token)
       └─ iframe /preview/?content_type=…&token=…  Nginx → 127.0.0.1:4322 (grabnar-preview.service)
            └─ Astro SSR (web/src/pages/preview.astro, prerender = false)
                 └─ GET /api/v2/page_preview/…    Entwurf als JSON → PageContent.astro (gleiche Komponenten wie live)
```

- Das Frontend bleibt statisch; nur `/preview/` wird pro Anfrage gerendert (`@astrojs/node`, standalone). Build-Ausgabe: `web/dist/client/` (statisch) und `web/dist/server/` (Vorschau-Server).
- Kein Cache: `wagtail.ts` memoisiert API-Antworten nur im statischen Build; die Vorschau ruft mit `{ fresh: true }` ab.
- Wagtail aktualisiert das Panel beim Tippen automatisch (Intervall 500 ms) – auch für noch nie gespeicherte Seiten.
- Vorschau-Banner, `noindex`, `Cache-Control: no-store`; `/preview/` ist in `robots.txt` gesperrt und nicht in der Sitemap.
- Lokal: `pnpm dev` bedient `/preview/` auf Port 4321 (Standard-`FRONTEND_URL` des CMS). Gegen den gebauten Server: `node web/dist/server/entry.mjs` mit `PORT=4322` und CMS mit `FRONTEND_URL=http://127.0.0.1:4322`.
- E2E-Test aus Redakteurssicht: `e2e/preview_admin.py` (Playwright).

**Weitere E2E-Skripte** (Node + Playwright, gegen einen ausgelieferten Build; Aufruf und
Voraussetzungen in `docs/07-web-standards.md`): `e2e/contact_form.mjs` (Formularfehler
barrierefrei gemeldet), `e2e/job_filter_faq.mjs` (Stellenfilter in der URL, FAQ-Akkordeon),
`e2e/mobile_menu.mjs` (Popover-Menü: Escape, Klick daneben, Kategorien). Sie laufen noch
nicht in CI.

## Hosting auf neuem VPS (entschieden, 20.11.2026)

Der Relaunch läuft auf einem **frischen VPS**, nicht auf dem Linode der Altseite (dessen OS ist zu alt
für die nötigen Updates). `grabnar.de` wird extern verwaltet; deshalb zuerst Abnahme unter
**`mbg.aivii.de`** (Basic-Auth, `noindex`), danach DNS-Umzug auf `www.grabnar.de` –
`docs/09-domainumzug.md`. Domain und Indexierung des Frontends kommen beim Bauen aus
`/srv/grabnar/web.env` (`PUBLIC_SITE_URL`, `PUBLIC_ALLOW_INDEXING`, `web/src/lib/site.ts`);
CMS und Frontend laufen unter derselben Domain, getrennt nach Pfad.

```
Internet → Nginx (:443, mbg.aivii.de → später www.grabnar.de)
            ├── /                → /srv/grabnar/web/dist/        (statische Astro-Dateien)
            ├── /admin/, /api/   → proxy_pass http://127.0.0.1:8000  (Wagtail, Docker)
            ├── /media/          → /srv/grabnar/media/            (Wagtail-Uploads, Renditions)
            ├── /django-static/  → /srv/grabnar/cms-static/       (Admin-Assets)
            ├── /preview/        → proxy_pass http://127.0.0.1:4322  (Astro-SSR, Live-Vorschau)
            └── /_hooks/rebuild  → proxy_pass http://127.0.0.1:9000  (Build-Webhook)
```

- `/admin/` zusätzlich mit `allow <Firmen-IP>; allow <Felix-IP>; deny all;` oder Basic-Auth absichern (`auth_basic`). Die `/api/` bleibt offen, liefert aber nur veröffentlichte Inhalte.
- Verzeichnisse auf dem Server: `/srv/grabnar/repo/` (Git-Checkout), `/srv/grabnar/web/dist/` (Build-Ausgabe, atomar per `mv` getauscht), `/srv/grabnar/media/`, `/srv/grabnar/pg/` (Postgres-Volume).
- CMS: `docker compose -f /srv/grabnar/repo/docker-compose.yml up -d` mit Services `cms` (gunicorn, Port 8000 nur auf 127.0.0.1) und `db` (Postgres). Media als Bind-Mount.
- Frontend-Build **auf dem Server**: kleiner Webhook-Dienst (`deploy/rebuild-hook.py`, Python stdlib `http.server`, systemd-Unit `grabnar-rebuild.service`), der bei `POST /_hooks/rebuild` mit gültigem `X-Hook-Secret` das Skript `deploy/build-web.sh` ausführt: `git pull`, `pnpm install --frozen-lockfile`, `pnpm build` nach `dist.new/`, dann atomar `mv dist dist.old && mv dist.new dist`. Debounce 60 s, Lock-Datei gegen Parallelbuilds. Node/pnpm auf dem Host nötig (z. B. via `fnm`).
- Der Wagtail-Signal-Handler ruft `FRONTEND_BUILD_HOOK_URL=http://127.0.0.1:9000/rebuild` auf (intern, nicht über Nginx).
- Redirects: `web` erzeugt beim Build aus `/api/v2/redirects/` eine Nginx-`map`-Datei `/srv/grabnar/web/redirects.map`; Nginx lädt sie per `include` und wird nach dem Build mit `nginx -s reload` neu geladen (sudoers-Regel nur für diesen Befehl).
- TLS: Let's Encrypt per `certbot certonly --webroot -w /var/www/certbot`, Pfade fest in `deploy/nginx/grabnar*.conf` (certbot ändert die Configs nicht).
- Alte Wagtail/CodeRed-Installation: läuft auf dem Linode weiter, bis der DNS-Eintrag umgezogen ist; danach sichern und nach 4 Wochen abschalten.

### Deploy-Workflow

1. `git push` nach `main` → GitHub Actions (`cms.yml`, `web.yml`) prüft Lint/Tests/Build.
2. Deployment per `deploy/deploy.sh` (SSH auf den VPS): `git pull`, `docker compose build cms`, `docker compose up -d`, `manage.py migrate`, `collectstatic`, danach `build-web.sh`.
3. Inhaltsänderungen im CMS lösen nur den Frontend-Rebuild aus, kein Deployment.

### Backup

- Nächtlich `pg_dump` + `tar` von `/srv/grabnar/media/` nach `/srv/backup/` und per `rclone` offsite, z. B. Object Storage des VPS-Anbieters (⬜ Ziel klären). Snapshot-/Backup-Dienst des Anbieters als zweite Ebene, falls gebucht.

### CI (`.github/workflows/`)

- `cms.yml`: ruff, `manage.py check`, Migrations-Check, Tests, Docker-Build.
- `web.yml`: `pnpm lint`, `astro check`, Build gegen Staging-API.

## Versionen und Updates

- **Wagtail: nur LTS-Linien.** Aktuell 7.4 LTS (seit 30.10.2026, vorher 7.3). LTS-Versionen bekommen
  18 Monate Sicherheits- und Fehlerkorrekturen, Nicht-LTS-Versionen wie 8.0 nur bis zur nächsten
  Feature-Version (etwa drei Monate). Laut Release-Prozess folgt eine LTS alle vier Feature-Versionen;
  die nächste ist damit voraussichtlich 8.3 (rund Mai 2027) – dann umsteigen.
- Der Update-Hinweis im Admin zeigt nur LTS-Versionen (`WAGTAIL_ENABLE_UPDATE_CHECK = "lts"` in
  `cms/grabnar/settings/base.py`). Patch-Versionen innerhalb der Linie (7.4.x) kommen mit `uv lock --upgrade`.
- **Django: 5.2 LTS** (Support bis April 2028). Wagtail 7.4 unterstützt 5.2; ein Wechsel auf Django 6.x
  bringt keinen Vorteil, solange 5.2 Sicherheitsupdates bekommt.
- `wagtail-headless-preview` 0.9 ist für Wagtail 7 freigegeben – vor einem Wechsel auf 8.x prüfen.
- Wagtail 7.4 speichert Entwürfe beim Bearbeiten automatisch zwischen (auch neue Seiten). Lokal mit
  SQLite deshalb WAL-Modus und Wartezeit (`base.py`), sonst kollidiert das mit der Vorschau
  („database is locked“). In Produktion (Postgres) nicht relevant.

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
3. Go-Live-Reihenfolge: neuer VPS unter `mbg.aivii.de` einrichten → `import_legacy`, Inhalte prüfen und ergänzen → Abnahme durch die Firma (Basic-Auth) → DNS-Umzug von `grabnar.de`/`www.grabnar.de` durch den Domain-Verwalter, Zertifikat, Umschalten auf `deploy/nginx/grabnar.conf`, Rebuild mit `PUBLIC_SITE_URL=https://www.grabnar.de` (Checkliste `docs/09-domainumzug.md`) → Altserver sichern und nach 4 Wochen abschalten.
4. Google Search Console: Sitemap neu einreichen, 404-Report nach Go-Live wöchentlich prüfen.

## Datenschutz

- Keine externen Requests im Frontend (Fonts, Maps, Analytics) ohne Consent.
- Karte: selbst gehostetes Leaflet (`web/src/components/blocks/Map.astro`), Kacheln über den
  eigenen Proxy `/tiles/` in `deploy/nginx/site.conf`. Dadurch kein Request des Besucher-Browsers
  an Dritte, die CSP bleibt bei `img-src 'self'`, und es braucht kein Consent-Overlay.
  Die [OSMF-Tile-Policy](https://operations.osmfoundation.org/policies/tiles/) erlaubt einen
  Cache-Proxy mit erkennbarem User-Agent, korrektem Referer und mindestens 7 Tagen Cache –
  alles gesetzt. Sie sagt aber auch zu: kein SLA, und gerade gewerblichen Seiten kann der
  Zugang ohne Vorankündigung entzogen werden. Fällt er aus, zeigt die Karte leere Kacheln;
  Adresse und OSM-Link bleiben. Ausweichwege dann: ein anderer OSM-Tile-Anbieter hinter
  demselben Proxy (nur die `proxy_pass`-Zeile) oder ein statisches Kartenbild.
- Bewerbungsdaten: Löschfrist (z. B. 6 Monate) als Management-Command `purge_applications`, im Admin dokumentiert.
- Analytics falls gewünscht: selbst gehostetes Plausible/Umami, cookielos.

### Auftragsverarbeitung Hosting (Akamai Connected Cloud / Linode)

Der Server ist ein Auftragsverarbeiter nach Art. 28 DSGVO, es braucht also einen Vertrag.
Eine **Unterschrift ist dafür nicht nötig**: Akamai bezieht seine Kunden-AVV über die
Nutzungsbedingungen ein („incorporated into and made a part of the most recent Terms
between Akamai and the customer"), und Art. 28 Abs. 9 lässt das elektronische Format
ausdrücklich zu. Zu tun ist deshalb nur: herunterladen, mit Datum ablegen, ins
Verarbeitungsverzeichnis eintragen.

- **Kunden-AVV:** <https://www.akamai.com/site/en/documents/corporate/akamai-data-protection-addendum.pdf>
- **Unterauftragsverarbeiter + Änderungsmitteilungen abonnieren:** <https://trust.akamai.com/>

**Achtung, verwechselbar:** die alte Adresse `linode.com/legal-dpa/` leitet inzwischen auf die
**Partner**-Fassung weiter (`partner-data-protection-agreement.pdf`). Die gilt für
Wiederverkäufer, die selbst Auftragsverarbeiter sind und Akamai als Unterauftragsverarbeiter
einsetzen – nicht für uns. Ebenso betrifft das Master Provider Agreement
(<https://www.akamai.com/legal/mpa>) nur das Provider-Programm.

Offen und nur im Dokument bzw. im Kundenbereich prüfbar (Akamais Edge weist automatisierte
Abrufe der PDFs mit „Access Denied" ab, daher hier ungeprüft): ob die
EU-Standardvertragsklauseln enthalten sind – Vertragspartner ist nach Drittquellen die
US-Gesellschaft Akamai Technologies, Inc., weshalb sie relevant wären –, und welche Region
tatsächlich gebucht ist. Die Angabe „Frankfurt am Main" in der Datenschutzerklärung stammt
aus der IP-Geolokalisierung, nicht aus dem Vertrag.

Eine gegengezeichnete Fassung ist nicht per Selbstbedienung vorgesehen; wer sie braucht, fragt
über den Account- oder Support-Kontakt im Kundenbereich. `support@linode.com` ist im MPA nur
als Adresse für formelle Mitteilungen genannt, nicht als AVV-Antragsstelle.

## Qualitätsprüfung (Lighthouse + Barrierefreiheit)

- `web/scripts/audit.mjs`: Lighthouse im Mobil-Profil und axe-core (WCAG 2.1/2.2 AA, bei 390 und 1280 px) für 8 repräsentative Seiten. Ziele: Barrierefreiheit, Best Practices, SEO ≥ 95, Performance ≥ 90 (CI: ≥ 80, geteilte Runner schwanken), 0 axe-Verstöße. Exit-Code 1 bei Verfehlung.
- `web/scripts/serve-prod.mjs` bildet `deploy/nginx/grabnar.conf` nach (gzip/Brotli, Cache-Header, Proxy für `/media/`, `/api/`, `/preview/`), damit lokal und in CI produktionsnah gemessen wird. Build dafür mit `WAGTAIL_MEDIA_URL=` und `PUBLIC_FORMS_API_URL=/api/forms` (alles unter einer Domain).
- CI: Job `audit` in `.github/workflows/web.yml`, Bericht als Artefakt `audit-report`.
- Stand 29.10.2026: alle 8 Seiten 100/100/100/100, LCP 0,8–1,0 s, CLS 0.
- Regeln, die daraus folgen: Links in dichten Listen mindestens 24 px hoch (`py-1`), Fließtext beginnt mit `<h2>` (Import normalisiert, Test `test_rich_text_heading_order`), jede Seite hat eine Meta-Beschreibung (Rückfall: Kurztext → Einleitung → Website-Text).
