# 04 – Aufgaben

Legende: 🤖 kann Claude Code weitgehend allein · 👤 braucht Felix (Zugänge, Entscheidungen, Inhalte) · 🤝 gemeinsam

## Phase 0 – Grundlagen (jetzt / am Handy begonnen)

- [x] Stack-Entscheidung: Headless Wagtail + Astro + Tailwind + React-Islands
- [x] Repo `fmbecker/grabnar_relaunch` angelegt, `CLAUDE.md` und `docs/` erstellt
- [x] Inhalte der Altseite erfasst: DB-Export → `docs/01-ist-analyse.md`, Texte in `docs/content-export/`, Redirect-Mapping `docs/redirects.csv`
- [x] Versionen der Altseite dokumentiert (Wagtail 2.14, Django 3.2, Python 3.8, MySQL)
- [ ] 👤 Empfängeradresse des Kontaktformulars klären (aktuell `mail@aivii.de`)
- [x] Seitenbaum v2 freigegeben (4 Kategorien auf oberster Ebene, `docs/02-konzept.md`)
- [x] 🤖 `ServiceIndexPage` = Leistungskategorie (Icon, Kurzbeschreibung, Titelbild), `ServiceGridBlock` mit Quelle Kategorien/Kategorie/manuell, Navigation mit Dropdown (Desktop) bzw. aufklappbar (Mobil)
- [x] 🤖 `manage.py import_legacy`: baut den kompletten Seitenbaum aus `docs/content-export/` (4 Kategorien, 22 Leistungen, Kontakt, Karriere, Impressum/Datenschutz/AGB), Kontaktdaten und 28 Redirects aus `docs/redirects.csv`. `seed_dev` = `import_legacy` + Platzhalterbilder + Beispiel-Stellen
- [x] Entscheidung Hosting: alles auf dem bestehenden Linode-VPS, Nginx vor statischem Frontend + Wagtail-Docker, kein DNS-Wechsel (siehe `docs/03-technik.md`)
- [ ] 👤 Linode-Bestandsaufnahme: OS-Version, Nginx-Config der Altseite, certbot-Status, freier Speicher/RAM, ob Docker installiert ist → `docs/01-ist-analyse.md`
- [ ] 👤 Logo, Farben, vorhandene Fotos sammeln → `docs/assets/`

## Phase 1 – CMS-Grundgerüst (`cms/`) ✅ erledigt am 26.10.2026 (Wagtail 7.3 LTS, Django 5.2)

- [x] 🤖 Wagtail-Projekt mit `uv` aufsetzen, Settings-Split, Postgres via `docker-compose.yml`
- [x] 🤖 `BasePage` (abstract) mit SEO-Feldern
- [x] 🤖 Blocks in `cms/blocks/` gemäß `docs/02-konzept.md` (Block-Vertrag)
- [x] 🤖 Seitentypen `HomePage`, `StandardPage`, `ServiceIndexPage`, `ServicePage`, `JobIndexPage`, `JobPage`
- [x] 🤖 `site_settings` (Contact, Footer, Tracking)
- [x] 🤖 API v2 konfigurieren: Pages/Images/Documents + Settings- und Redirects-Endpunkt
- [x] 🤖 `wagtail-headless-preview` einbinden
- [x] 🤖 Beispielinhalte für alle Blocks: Management-Command `manage.py seed_dev` (statt JSON-Fixture, wegen Seitenbaum/Bildern)
- [x] 🤖 `forms_api`: Contact + Application Endpunkte, Honeypot, Mailversand, Admin-Ansicht
- [x] 🤖 `signals.py`: Publish → Build-Hook mit Debounce
- [x] 🤖 Dockerfile, ruff-Konfiguration, GitHub-Workflow `cms.yml`

## Phase 2 – Frontend-Grundgerüst (`web/`) ✅ bis auf Preview erledigt am 26.10.2026 (Astro 7, Tailwind 4, React 19)

- [x] 🤖 Astro + Tailwind + React-Integration initialisieren, `pnpm`
- [x] 🤖 `src/lib/types.ts` aus dem Block-Vertrag ableiten
- [x] 🤖 `src/lib/wagtail.ts` (Pages, Settings, Redirects, Renditions)
- [x] 🤖 Layouts + `[...slug].astro` mit `getStaticPaths()`
- [x] 🤖 Alle Block-Komponenten in `src/components/blocks/` (zunächst unstyled, dann Design)
- [x] 🤖 Islands: `ContactForm.tsx` (Kontakt + Bewerbung in einer Komponente, `variant`), `JobFilter.tsx`
- [x] 🤖 `Seo.astro`, Sitemap, JSON-LD (`LocalBusiness`, `JobPosting`)
- [x] 🤖 Nginx-`map`-Generierung aus der Redirects-API (`web/scripts/redirects.mjs`)
- [ ] 🤖 Preview-Route für Headless-Preview fertigstellen: `web/src/pages/preview.astro` ist nur ein Platzhalter. Plan: kleine SSR-Route (Astro `output: 'static'` + `prerender = false` für `/preview/`, Node-Adapter oder separater `astro dev`-Prozess auf dem Server), die `?content_type=&token=` an `GET <CMS>/api/v2/page_preview/1/?content_type=…&token=…` weiterreicht und `PageContent.astro` rendert
- [x] 🤖 GitHub-Workflow `web.yml`

## Phase 3 – Design & Inhalte

- [ ] 🤝 Design-System in Tailwind (`tailwind.config` / CSS-Variablen): Farben aus Logo, Typo, Spacing
- [ ] 🤖 Startseite, Leistungsseiten, Karriere, Kontakt ausgestalten
- [x] 🤖 Texte der Altseite migriert (1:1 übernommen)
- [ ] 🤝 Texte überarbeiten: Teaser im Hero wiederholt den ersten Satz des Fließtexts; Kategorie-Seiten haben kaum eigenen Text; SEO-Titel/Descriptions sind automatisch erzeugt; „IFSG“ → „IfSG“
- [ ] 🤖 Seite „Unternehmen“ anlegen (Altseite hatte keine; Texte von der Startseite + Meisterbetrieb/QM)
- [ ] 👤 Bilder einpflegen (Wagtail-Admin)
- [ ] 👤 Impressum / Datenschutz / AGB rechtlich prüfen. Datenschutz muss neue Formulare (Bewerbung mit Upload, Speicherfrist 180 Tage) und ggf. Umami abdecken; Impressum: Feld „Vertretungsberechtigt“ ist in der Altseite leer
- [ ] 🤖 Lighthouse ≥ 95 auf Mobile, a11y-Check (axe)
- [ ] 🤖 Karte in `Map.astro`: selbst gehostetes Leaflet mit OSM-Tiles (aktuell nur Adresse + OSM-Link)
- [ ] 🤖 Schriften selbst hosten (`web/public/fonts/`, Inter Variable), aktuell System-Font-Stack

## Phase 4 – Go-Live

- [x] 🤖 `deploy/`: `docker-compose.yml`, `nginx/grabnar.conf`, `rebuild-hook.py` + systemd-Unit, `build-web.sh`, `deploy.sh`, Backup-Skript
- [ ] 🤝 Docker, Node/pnpm (fnm) auf dem Linode installieren, CMS parallel zur Altseite hochfahren
- [ ] 🤝 Staging-Server-Block (Port 8443, Basic-Auth) für Abnahme
- [ ] 🤝 Backup nach `/srv/backup/` + Offsite-Ziel einrichten und Restore einmal testen
- [x] Redirect-Tabelle `docs/redirects.csv` erstellt; Import erfolgt über `import_legacy`
- [ ] 👤 Mailversand (SMTP-Zugang) für Formulare
- [ ] 👤 Nginx auf neue Struktur umschalten, TLS prüfen (kein DNS-Wechsel nötig)
- [ ] 🤖 Nach Go-Live: 404-Check, Search Console Sitemap
- [ ] 👤 Altserver nach 4 Wochen abschalten

## Später / Ideen

- Referenzen-Seite mit Logos
- News/Blog (`ArticlePage`)
- Stellenanzeigen automatisch an Google for Jobs via JSON-LD (bereits in Phase 2 angelegt) – Indexierung prüfen
- Selbst gehostete Analytics (Plausible/Umami)
