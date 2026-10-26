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
- Hosting: Cloudflare Pages (Deploy-Hook, `_redirects`, kostenlos) als Vorschlag; alternativ Netlify oder eigener Nginx mit `rsync` aus CI.

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
3. Go-Live-Reihenfolge: CMS produktiv (interne Domain, z. B. `cms.grabnar.de` hinter Auth) → Frontend auf Staging-Domain abnehmen → DNS für `www.grabnar.de` umstellen → Altserver 4 Wochen als Fallback behalten.
4. Google Search Console: Sitemap neu einreichen, 404-Report nach Go-Live wöchentlich prüfen.

## Datenschutz

- Keine externen Requests im Frontend (Fonts, Maps, Analytics) ohne Consent.
- Karte als statisches Bild oder selbst gehostetes Leaflet mit OSM-Tiles von eigenem Proxy, sonst Consent-Overlay.
- Bewerbungsdaten: Löschfrist (z. B. 6 Monate) als Management-Command `purge_applications`, im Admin dokumentiert.
- Analytics falls gewünscht: selbst gehostetes Plausible/Umami, cookielos.
