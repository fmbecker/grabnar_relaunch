# Design-Brief: visuelles Rework www.grabnar.de

Für eine Claude-Code-Sitzung mit Design-Skill (z. B. Taste, impeccable). Hintergrund und Entwürfe:
`docs/06-design.md`. Projektregeln: `CLAUDE.md` (gelten vollständig).

## 1. Auftrag

Das Frontend in `web/` visuell überarbeiten: von „sauber, aber bieder“ zu **selbstbewusst, hochwertig,
handwerklich-präsent**. Inhalte, Seitenbaum, CMS-Modelle und Texte bleiben unverändert – es geht
nur um Gestaltung (Layout, Typografie, Farbe, Rhythmus, Details, Interaktionszustände).

## 2. Absender und Publikum

- **M. B. Grabnar GmbH**, Meisterbetrieb für Gebäudereinigung, Gebäudedienste und Handwerkerleistungen,
  Stuttgart. Zertifiziert nach ISO 9001 und ISO 14001.
- **Zielgruppen:** Hausverwaltungen, Facility-Verantwortliche, Geschäftsführer von KMU (Anfrage, Anruf);
  Bewerber (Karriere). **Keine Privatkunden** ansprechen.
- **Wirkung:** zuverlässig, kompetent, zupackend, regional verwurzelt. Nicht: Start-up-verspielt,
  Luxus-kühl, Baumarkt-laut.
- **Wichtigste Handlungen:** Anrufen (0711 2 36 33 30), Anfrage über `/kontakt/`, Bewerbung.

## 3. Ausgangspunkt

- Aktueller Code auf `main` = Startpunkt. Referenzstand vor dem Rework: Branch `design/ausgangsstand`.
- Screenshots vorher: `docs/design/ausgangsstand/*-desktop.jpg` und `*-mobil.jpg`.
- Tokens: `web/src/styles/global.css` (`@theme`: `brand-50…950`, `accent-*`, `ink-*`).
- Diagnose: kein Fotomaterial (Platzhalter = flache Blauflächen), jede Seite folgt demselben Schema
  (Kopfband → Text → Kacheln → CTA), Arial ohne Spannung, fast nur Blau auf Weiß.

## 4. Richtung (Felix' Wahl: Aufbau von Entwurf B)

Vorlage: `docs/design/entwuerfe/B-Start.dc.html`, `B-Leistung.dc.html` (HTML mit Inline-Styles; die
Optik im Design-Artefakt „Grabnar Gestaltungsrichtungen“). Übernehmen:

- Vollflächige Abschnitte in Markenblau im Wechsel mit Weiß – klarer Hell-Dunkel-Rhythmus.
- Großer Hero: Motto als Zitat, kräftige Headline, Subline, zwei Buttons, angeschnittenes Foto.
- **Fakten-Leiste** unter dem Hero: Meisterbetrieb · ISO 9001 · ISO 14001 · 22 Leistungen · Stuttgart & Region.
- Leistungsbereiche als große **Bild-Text-Reihen, abwechselnd links/rechts**, Leistungen als Liste.
- Merkmale auf Blau als Raster mit feinen Trennlinien.
- Karriere-Teaser auf der Startseite.
- Abschlussband mit sehr großer Telefonnummer.
- Leistungsseite: Kopf auf Blau mit Kategorie-Marke, Fakten-Leiste, Objektliste als Raster, „Passt auch dazu“.

Nicht übernehmen: die Marineblau/Gelb-Farben des ersten Entwurfs; Versalien nur dosiert (Headlines
ja, Fließtext und lange Labels nie).

## 5. Feste Vorgaben

| Thema | Vorgabe |
|---|---|
| Farben | Logo-Blau `#2D78BC` (`brand-500`) für dunkle Flächen, Logo-Hellblau `#8BC1E5` (`brand-300`) als Akzent, Markenskala `brand-50…950`, Neutrale `ink-*`. Text auf `#2D78BC` nur Weiß (4,64:1). Hellblau nie als Schrift auf Blau. |
| Schrift | Fließtext Arial (Entscheidung Felix). Überschriften: **offen** – siehe 9. |
| Logo | `docs/assets/logo-mbgrabnar.png` (hell), `docs/assets/logo-mbgrabnar-weiss.png` (auf Blau) – im CMS als Website-Einstellung |
| Siegel | ISO-Siegel kommt über Website-Einstellungen → Zertifizierung (Footer + Block „Zertifikat“) |
| Fotos | Noch keine. Design muss **ohne Fotos** würdig aussehen (gestaltete Platzhalter statt flacher Farbflächen, z. B. Markenmuster aus den Logo-Türmen) und **mit Fotos** stark (Renditions `thumb/card/wide/hero/full`). |

## 6. Leitplanken (nicht verhandelbar)

- **Block-Vertrag:** neue Blöcke/Varianten gleichzeitig in `cms/blocks/blocks.py`, `web/src/lib/types.ts`,
  `web/src/components/blocks/` – dann `uv run pytest -q` und Migrationen.
- **Barrierefreiheit & Performance:** Lighthouse mobil 100/100/100/100, axe 0 Verstöße
  (`web/scripts/audit.mjs`, CI-Job `audit`). Fokuszustände sichtbar, Touch-Ziele ≥ 44 px,
  `prefers-reduced-motion` respektieren.
- **Kein externer Request:** keine Google Fonts per Link, kein CDN. Schriften selbst hosten in `web/public/fonts/`.
- **Tracking erhalten:** `umami()`-Attribute und `track()`-Aufrufe an Buttons, Links, Formularen
  (`docs/05-tracking.md`, `pnpm check:tracking`).
- **Inhalte:** keine neuen Firmenaussagen, keine erfundenen Zahlen, keine Privatkunden, § 34a nie erwähnen.
- **Technik:** Tailwind 4 (`@theme`), Astro-Komponenten für Statisches, React nur in bestehenden Islands.
  Bilder nur über Wagtail-Renditions. Live-Vorschau (`/preview/`) muss weiter funktionieren.
- **Mobil zuerst:** 390 px ohne horizontales Scrollen; Header-Navigation bis 1024 px ohne Überlauf.

## 7. Umfang und Reihenfolge

1. **Tokens:** Typo-Skala, Abstände/Sektionsrhythmus, Radien, Schatten, Linien in `global.css`.
2. **Header + Footer** (`Header.astro`, `Footer.astro`) – Blau-Variante, weißes Logo, Telefon prominent.
3. **Hero** (`blocks/Hero.astro`) inkl. Foto-Fallback.
4. **Fakten-Leiste** (neu; Inhalt fest oder aus Settings – Block-Vertrag beachten).
5. **Leistungsbereiche** (`blocks/ServiceGrid.astro`, Variante `categories` → Bild-Text-Reihen; Variante `services` → Karten).
6. **Merkmale** (`blocks/FeatureList.astro`), **CTA** (`blocks/Cta.astro`), **Zertifikat** (`blocks/Certificate.astro`).
7. **Leistungs- und Kategorieseiten** (Kopf in `PageContent.astro`, `.prose-site`-Listen).
8. **Unternehmen, Karriere (Stellenliste, Stellenseite), Kontakt (Formular-Island-Styling), 404, Vorschau-Banner.**
9. **Details:** Hover/Fokus/Active, Übergänge, Abschnittsübergänge, Druckansicht optional.

## 8. Arbeitsweise und Abnahme

- Auf Branch `feat/design-rework` arbeiten, kleine Commits (`web: …`), nie mit roten Prüfungen pushen.
- Lokal: `cd cms && uv run manage.py seed_dev --superuser && uv run manage.py runserver`, `cd web && pnpm dev`.
- Nach jedem Schritt Screenshots 1440 px und 390 px gegen `docs/design/ausgangsstand/` vergleichen.
- Abnahme je Schritt: `pnpm lint && pnpm check && pnpm build && pnpm check:tracking`, bei CMS-Änderungen
  `uv run ruff check . && uv run pytest -q`; am Ende `node scripts/audit.mjs` (produktionsnah, siehe
  `docs/03-technik.md` „Qualitätsprüfung“) mit 100 / 0.
- Nachher-Screenshots nach `docs/design/nachher/`, Entscheidungen in `docs/06-design.md` nachtragen.

## 9. Offene Entscheidungen (zu Beginn mit Felix klären)

1. **Akzentfarbe:** Logo-Hellblau `#8BC1E5` (Vorgabe) oder das im Entwurf zuletzt gewählte `#005A96`
   (dann Schrift darauf Weiß/`#DDE9F4`; Kontraste in `docs/06-design.md`).
2. **Überschriften-Schrift:** Arial (bisher) oder eine kräftigere, selbst gehostete Groteske nur für
   Überschriften (im Entwurf getestet: Manrope, Archivo). Vorschlag: beide Varianten am Hero zeigen.
