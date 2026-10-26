# 04 – Aufgaben

Legende: 🤖 kann Claude Code weitgehend allein · 👤 braucht Felix (Zugänge, Entscheidungen, Inhalte) · 🤝 gemeinsam

## Phase 0 – Grundlagen (jetzt / am Handy begonnen)

- [x] Stack-Entscheidung: Headless Wagtail + Astro + Tailwind + React-Islands
- [x] Repo `fmbecker/grabnar_relaunch` angelegt, `CLAUDE.md` und `docs/` erstellt
- [ ] 👤 Inhalte der Altseite erfassen (Seitenbaum, Texte, Bilder, Formulare) → `docs/01-ist-analyse.md` vervollständigen
- [ ] 👤 Versionen und Hosting der Altseite dokumentieren (`pip freeze`, Server, DB, Mailversand)
- [x] Entscheidung Hosting: alles auf dem bestehenden Linode-VPS, Nginx vor statischem Frontend + Wagtail-Docker, kein DNS-Wechsel (siehe `docs/03-technik.md`)
- [ ] 👤 Linode-Bestandsaufnahme: OS-Version, Nginx-Config der Altseite, certbot-Status, freier Speicher/RAM, ob Docker installiert ist → `docs/01-ist-analyse.md`
- [ ] 👤 Logo, Farben, vorhandene Fotos sammeln → `docs/assets/`

## Phase 1 – CMS-Grundgerüst (`cms/`)

- [ ] 🤖 Wagtail-Projekt mit `uv` aufsetzen, Settings-Split, Postgres via `docker-compose.yml`
- [ ] 🤖 `BasePage` (abstract) mit SEO-Feldern
- [ ] 🤖 Blocks in `cms/blocks/` gemäß `docs/02-konzept.md` (Block-Vertrag)
- [ ] 🤖 Seitentypen `HomePage`, `StandardPage`, `ServiceIndexPage`, `ServicePage`, `JobIndexPage`, `JobPage`
- [ ] 🤖 `site_settings` (Contact, Footer, Tracking)
- [ ] 🤖 API v2 konfigurieren: Pages/Images/Documents + Settings- und Redirects-Endpunkt
- [ ] 🤖 `wagtail-headless-preview` einbinden
- [ ] 🤖 Fixture `cms/fixtures/dev.json` mit Beispielinhalten für alle Blocks
- [ ] 🤖 `forms_api`: Contact + Application Endpunkte, Honeypot, Mailversand, Admin-Ansicht
- [ ] 🤖 `signals.py`: Publish → Build-Hook mit Debounce
- [ ] 🤖 Dockerfile, ruff-Konfiguration, GitHub-Workflow `cms.yml`

## Phase 2 – Frontend-Grundgerüst (`web/`)

- [ ] 🤖 Astro + Tailwind + React-Integration initialisieren, `pnpm`
- [ ] 🤖 `src/lib/types.ts` aus dem Block-Vertrag ableiten
- [ ] 🤖 `src/lib/wagtail.ts` (Pages, Settings, Redirects, Renditions)
- [ ] 🤖 Layouts + `[...slug].astro` mit `getStaticPaths()`
- [ ] 🤖 Alle Block-Komponenten in `src/components/blocks/` (zunächst unstyled, dann Design)
- [ ] 🤖 Islands: `ContactForm.tsx`, `ApplicationForm.tsx`, `JobFilter.tsx`
- [ ] 🤖 `Seo.astro`, Sitemap, JSON-LD (`LocalBusiness`, `JobPosting`)
- [ ] 🤖 `_redirects`-Generierung aus der Redirects-API
- [ ] 🤖 Preview-Route für Headless-Preview
- [ ] 🤖 GitHub-Workflow `web.yml`

## Phase 3 – Design & Inhalte

- [ ] 🤝 Design-System in Tailwind (`tailwind.config` / CSS-Variablen): Farben aus Logo, Typo, Spacing
- [ ] 🤖 Startseite, Leistungsseiten, Karriere, Kontakt ausgestalten
- [ ] 👤 Texte der Altseite migrieren und überarbeiten (Claude kann Entwürfe liefern)
- [ ] 👤 Bilder einpflegen (Wagtail-Admin)
- [ ] 👤 Impressum / Datenschutz aktualisieren
- [ ] 🤖 Lighthouse ≥ 95 auf Mobile, a11y-Check (axe)

## Phase 4 – Go-Live

- [ ] 🤖 `deploy/`: `docker-compose.yml`, `nginx/grabnar.conf`, `rebuild-hook.py` + systemd-Unit, `build-web.sh`, `deploy.sh`, Backup-Skript
- [ ] 🤝 Docker, Node/pnpm (fnm) auf dem Linode installieren, CMS parallel zur Altseite hochfahren
- [ ] 🤝 Staging-Server-Block (Port 8443, Basic-Auth) für Abnahme
- [ ] 🤝 Backup nach `/srv/backup/` + Offsite-Ziel einrichten und Restore einmal testen
- [ ] 👤 Redirect-Tabelle `docs/redirects.csv` befüllen → importieren
- [ ] 👤 Mailversand (SMTP-Zugang) für Formulare
- [ ] 👤 Nginx auf neue Struktur umschalten, TLS prüfen (kein DNS-Wechsel nötig)
- [ ] 🤖 Nach Go-Live: 404-Check, Search Console Sitemap
- [ ] 👤 Altserver nach 4 Wochen abschalten

## Später / Ideen

- Referenzen-Seite mit Logos
- News/Blog (`ArticlePage`)
- Stellenanzeigen automatisch an Google for Jobs via JSON-LD (bereits in Phase 2 angelegt) – Indexierung prüfen
- Selbst gehostete Analytics (Plausible/Umami)
