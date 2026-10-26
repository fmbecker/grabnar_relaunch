# 04 – Aufgaben

Legende: 🤖 kann Claude Code weitgehend allein · 👤 braucht Felix (Zugänge, Entscheidungen, Inhalte) · 🤝 gemeinsam

## Phase 0 – Grundlagen (jetzt / am Handy begonnen)

- [x] Stack-Entscheidung: Headless Wagtail + Astro + Tailwind + React-Islands
- [x] Repo `fmbecker/grabnar_relaunch` angelegt, `CLAUDE.md` und `docs/` erstellt
- [ ] 👤 Inhalte der Altseite erfassen (Seitenbaum, Texte, Bilder, Formulare) → `docs/01-ist-analyse.md` vervollständigen
- [ ] 👤 Versionen und Hosting der Altseite dokumentieren (`pip freeze`, Server, DB, Mailversand)
- [ ] 👤 Entscheidung Hosting: Frontend (Cloudflare Pages?) und CMS (bestehender Server? neuer VPS?)
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

- [ ] 🤝 CMS-Deployment (Docker Compose auf Server, Backup-Strategie für Postgres + Media)
- [ ] 🤝 Frontend-Deployment + Deploy-Hook mit CMS verbinden
- [ ] 👤 Redirect-Tabelle `docs/redirects.csv` befüllen → importieren
- [ ] 👤 Mailversand (SMTP-Zugang) für Formulare
- [ ] 👤 DNS umstellen, TLS prüfen
- [ ] 🤖 Nach Go-Live: 404-Check, Search Console Sitemap
- [ ] 👤 Altserver nach 4 Wochen abschalten

## Später / Ideen

- Referenzen-Seite mit Logos
- News/Blog (`ArticlePage`)
- Stellenanzeigen automatisch an Google for Jobs via JSON-LD (bereits in Phase 2 angelegt) – Indexierung prüfen
- Selbst gehostete Analytics (Plausible/Umami)
