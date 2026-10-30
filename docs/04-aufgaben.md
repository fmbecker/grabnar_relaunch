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
- [x] Logo (`docs/assets/logo-mbgrabnar.png`) und Markenfarben (`#2D78BC`, `#8BC1E5`) von der Altseite übernommen
- [ ] 👤 Eigene Fotos (Team, Objekte, Fahrzeuge) sammeln → Wagtail-Mediathek
- [ ] 👤 Logo als Vektor (SVG/PDF/EPS) bei der Firma oder Agentur anfragen

## Phase 1 – CMS-Grundgerüst (`cms/`) ✅ erledigt am 26.10.2026 (Wagtail 7.3, Django 5.2; am 30.10.2026 auf Wagtail 7.4 LTS aktualisiert)

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

## Phase 2 – Frontend-Grundgerüst (`web/`) ✅ erledigt am 26.10.2026 (Astro 7, Tailwind 4, React 19)

- [x] 🤖 Astro + Tailwind + React-Integration initialisieren, `pnpm`
- [x] 🤖 `src/lib/types.ts` aus dem Block-Vertrag ableiten
- [x] 🤖 `src/lib/wagtail.ts` (Pages, Settings, Redirects, Renditions)
- [x] 🤖 Layouts + `[...slug].astro` mit `getStaticPaths()`
- [x] 🤖 Alle Block-Komponenten in `src/components/blocks/` (zunächst unstyled, dann Design)
- [x] 🤖 Islands: `ContactForm.tsx` (Kontakt + Bewerbung in einer Komponente, `variant`), `JobFilter.tsx`
- [x] 🤖 `Seo.astro`, Sitemap, JSON-LD (`LocalBusiness`, `JobPosting`)
- [x] 🤖 Nginx-`map`-Generierung aus der Redirects-API (`web/scripts/redirects.mjs`)
- [x] 🤖 Live-Vorschau: `/preview/` als Astro-SSR-Route (`@astrojs/node`), API `/api/v2/page_preview/`, Dienst `grabnar-preview.service`, Nginx-Route; E2E-Test `e2e/preview_admin.py` (bestehende + neue Seite, Live-Update beim Tippen)
- [x] 🤖 GitHub-Workflow `web.yml`

## Phase 3 – Design & Inhalte

- [x] 🤖 Farb-Tokens aus dem Logo in `web/src/styles/global.css` (Kontraste geprüft), Logo im Header, Favicon/Touch-Icon aus den Logo-Türmen
- [ ] 🤝 Design-System weiter ausbauen: Typo-Skala, Abstände, Bildsprache, Hero mit Foto
- [ ] 🤖 Startseite, Leistungsseiten, Karriere, Kontakt ausgestalten
- [x] 🤖 Texte der Altseite migriert (1:1 übernommen)
- [x] 🤖 Seiten aus den Alttexten aufgebaut: Kurztext im Kopf der Leistungsseiten wird nicht mehr im Fließtext wiederholt; Kategorieseiten mit Einleitung aus ihren Leistungen; „IFSG“ → „IfSG“; Leistungslisten als zweispaltige Häkchenlisten
- [x] 🤖 Redaktionelle Texte für 30 Seiten in `docs/content-overrides.csv`: Kurztexte der 22 Leistungen, Einleitungen der 4 Kategorien, SEO-Titel (≤ 60 Zeichen) und Meta-Beschreibungen (≤ 158 Zeichen); nur Aussagen aus den Alttexten, Quelle je Zeile in Spalte `quelle_hinweis`
- [ ] 👤 `docs/content-overrides.csv` mit der Firma durchgehen (Excel öffnet sie direkt), Spalte `status` von „Vorschlag“ auf „freigegeben“ setzen; Änderungen dort eintragen, `import_legacy` übernimmt sie
- [x] 🤖 Neutexte (Vorschläge) für 22 Leistungen, Startseite und „Unternehmen“ in `docs/content-neu/` – nur Aussagen der Altseite, offene Fragen je Datei unter „Hinweise“; `import_legacy` übernimmt sie (`--originaltexte` zeigt die Alttexte). Doppelter Eintrag „Verkehrsmittel“ dort bereits entfernt
- [x] 👤 Neutexte in `docs/content-neu/` von der Firma freigegeben (30.10.2026), Status in allen Dateien auf „freigegeben“
- [x] 🤖 Seite „Unternehmen“ (`/unternehmen/`): Leitgedanke + Firmentext, 6 Merkmale („Was uns auszeichnet“) ausschließlich aus Aussagen der Altseite (Quellen in `import_legacy.FEATURES`), Leistungsbereiche, CTA
- [ ] 👤 Merkmale auf „Unternehmen“ von der Firma bestätigen lassen (z. B. ob die QM-Zertifizierung noch gültig ist, Name des Zertifikats), ggf. ergänzen: Gründungsjahr, Mitarbeiterzahl, Team-Fotos
- [ ] 👤 Bilder einpflegen (Wagtail-Admin)
- [ ] 👤 Impressum / Datenschutz / AGB rechtlich prüfen. Datenschutz muss neue Formulare (Bewerbung mit Upload, Speicherfrist 180 Tage) und ggf. Umami abdecken; Impressum: Feld „Vertretungsberechtigt“ ist in der Altseite leer
- [x] 🤖 Lighthouse (mobil) + axe-core (WCAG 2.1/2.2 AA) für 8 Seitentypen: überall 100/100/100/100, 0 axe-Verstöße (29.10.2026). Behoben: Touch-Ziele in Kategorie-Kacheln, Kontrast Kartenplatzhalter, Überschriften-Reihenfolge der Alttexte, fehlende Meta-Beschreibungen. Läuft als Job `audit` in `web.yml`, lokal: `web/scripts/audit.mjs` + `web/scripts/serve-prod.mjs`
- [ ] 🤖 Karte in `Map.astro`: selbst gehostetes Leaflet mit OSM-Tiles (aktuell nur Adresse + OSM-Link)
- [x] Schrift: Arial (Entscheidung Felix 30.10.2026), keine Webfonts nötig

- [x] 🤖 Tracking mit Umami vorbereitet: Einstellungen im CMS (Script-URL, Website-ID, Domains, Web Vitals, Do Not Track), 17 Ereignisse auf allen Seiten und Komponenten, Konzept in `docs/05-tracking.md`
- [ ] 👤 Umami auf v3 aktualisieren (nur noch PostgreSQL – ggf. MySQL-Migration), Website anlegen, Website-ID im CMS eintragen
- [ ] 👤 Ziele und Trichter in Umami anlegen (Vorschlag in `docs/05-tracking.md`)

## Phase 4 – Go-Live

- [x] 🤖 `deploy/`: `docker-compose.yml`, `nginx/grabnar.conf`, `rebuild-hook.py` + systemd-Unit, `build-web.sh`, `deploy.sh`, Backup-Skript
- [x] 🤖 CMS-Image wird von GitHub Actions gebaut und nach `ghcr.io/fmbecker/grabnar-cms` gepusht; `deploy.sh` lädt es nur noch (kein Build auf dem 2-GB-VPS)
- [ ] 👤 Paket `grabnar-cms` auf GitHub einmalig auf „Public“ stellen (oder Server per Token anmelden, siehe `deploy/README.md`)
- [ ] 🤝 Docker, Node/pnpm (fnm) auf dem Linode installieren, CMS parallel zur Altseite hochfahren
- [ ] 🤝 Staging-Server-Block (Port 8443, Basic-Auth) für Abnahme
- [ ] 🤝 Vorschau-Dienst einrichten: `grabnar-preview.service`, sudoers-Eintrag, `FRONTEND_URL` in `cms.env` (siehe `deploy/README.md`)
- [ ] 🤝 Backup nach `/srv/backup/` + Offsite-Ziel einrichten und Restore einmal testen
- [x] Redirect-Tabelle `docs/redirects.csv` erstellt; Import erfolgt über `import_legacy`
- [ ] 👤 Mailversand (SMTP-Zugang) für Formulare
- [ ] 👤 Nginx auf neue Struktur umschalten, TLS prüfen (kein DNS-Wechsel nötig)
- [ ] 🤖 Nach Go-Live: 404-Check, Search Console Sitemap
- [ ] 👤 Vor dem Abschalten: Mediathek der Altseite (`/home/mbgsite/media/`, 135 Bilder) und einen MySQL-Dump offline sichern
- [ ] 👤 Altserver nach 4 Wochen abschalten

## Später / Ideen

- Referenzen-Seite mit Logos
- News/Blog (`ArticlePage`)
- Stellenanzeigen automatisch an Google for Jobs via JSON-LD (bereits in Phase 2 angelegt) – Indexierung prüfen
