# 06 – Design-Überarbeitung (Briefing)

Stand: 31.10.2026. Grundlage für die visuelle Überarbeitung des Frontends (`web/`). Inhalte und
Strukturen sind fertig und freigegeben; es geht nur um Gestaltung.

## Ausgangslage

Felix' Eindruck der aktuellen Seite: „spießig, bieder, visuell noch nicht raffiniert“. Ursachen:

1. Keine echten Fotos (Platzhalter, Hero ohne Bild) – größter Einzelfaktor, kommt mit den Fotos der Firma.
2. Schematisches Layout: jede Seite Kopfband → Text → Kacheln → CTA, kaum Rhythmus und Kontrast.
3. Flache Typografie: Arial in allen Größen.
4. Eintönige Farbe: fast nur Markenblau auf Weiß, kein Hell-Dunkel-Wechsel der Abschnitte.

**Brief für die Rework-Sitzung (Design-Skill im Terminal): `docs/design/brief-rework.md`.**

## Ausgangspunkt: das bestehende einfache Design

Das aktuell umgesetzte Frontend ist der Startpunkt der Überarbeitung (sauberer, funktionierender Code,
Lighthouse/axe 100). Es ist gesichert:

- **Branch `design/ausgangsstand`** (Commit `c9dce5d`) – der Code-Stand vor der Überarbeitung; wird nicht
  weiterentwickelt. Vergleichen oder zurückholen:
  `git diff origin/design/ausgangsstand -- web/` · `git checkout origin/design/ausgangsstand -- web/src/components/Header.astro`
  (Optional zusätzlich als Tag: `git tag design-ausgangsstand c9dce5d && git push origin design-ausgangsstand`.)
- **Screenshots** in `docs/design/ausgangsstand/` (Seed-Daten mit Platzhalterbildern, 31.10.2026):
  Startseite, Kategorie (Gebäudereinigung), Leistung (Unterhaltsreinigung), Unternehmen, Karriere,
  Kontakt – jeweils `-desktop.jpg` (1440 px) und `-mobil.jpg` (390 px).
- Design-Tokens: `web/src/styles/global.css` (`@theme`: Markenskala `brand-50…950`, `accent`, `ink`; Schrift Arial).

Die Entwürfe A/B/C unten sind Ideensammlung, kein Pflichtenheft.

## Entwürfe

Drei Richtungen als Design-Artefakt „Grabnar Gestaltungsrichtungen“ auf claude.ai (privat, von Felix
teilbar). Quellen hier in `docs/design/entwuerfe/` (`*.dc.html`, Format des Design-Artefakts – die
Dateien brauchen dessen Laufzeit zum Rendern, lesbar sind sie als HTML mit Inline-Styles):

| Richtung | Dateien | Kurz |
|---|---|---|
| A · Klar & hochwertig | `A-Start.dc.html`, `A-Leistung.dc.html` | Weißraum, große Headlines, Foto mit überlappender Karte, Fakten-Leiste |
| **B · Handwerk & Präsenz** | `B-Start.dc.html`, `B-Leistung.dc.html` | **gewählt** – vollflächige Markenblau-Abschnitte, große Versal-Headlines, schräg angeschnittenes Hero-Foto, Bereiche als Bild-Text-Wechsel, Karriere-Block |
| C · Modern-regional | `C-Start.dc.html`, `C-Leistung.dc.html` | helle Bento-Kacheln, Pillen-Navigation, Chips |

## Entscheidung (Felix, 31.10.2026)

**Aufbau von Richtung B, Farben aus den Markenvorgaben** (nicht Marineblau/Gelb des ersten Entwurfs):

- Dunkle Abschnitte (Header, Hero, Merkmale, „Wo wir reinigen“, Footer): Logo-Blau `#2D78BC` (`brand-500`).
- Akzent: im Entwurf zuletzt von Felix auf **`#005A96`** gestellt, Schrift darauf `#DDE9F4` – vorher
  Logo-Hellblau `#8BC1E5`. ⬜ Mit Felix klären, welcher Akzent gilt (`#005A96` ist nicht in `global.css`).
- Überschriften-Schrift: im Entwurf zuletzt **Manrope** gewählt. ⬜ Mit Felix bestätigen
  (bisherige Entscheidung: Arial überall, `docs/02-konzept.md`). Fließtext bleibt Arial. Eine
  Zusatzschrift selbst hosten (`web/public/fonts/`, nur benötigte Schnitte, `font-display: swap`),
  nie Google Fonts per Link (Datenschutz).

### Kontraste (WCAG AA, Text 4,5:1)

| Vordergrund | Hintergrund | Verhältnis | Verwendung |
|---|---|---|---|
| `#FFFFFF` | `#2D78BC` | 4,64 | Text auf Logo-Blau – nur Weiß, keine hellen Grautöne |
| `#DDE9F4` | `#2D78BC` | 3,77 | **nicht** für Fließtext; nur ≥ 24 px oder fett ≥ 18,7 px |
| `#DDE9F4` | `#005A96` | 5,87 | Text auf Akzent `#005A96` |
| `#FFFFFF` | `#005A96` | 7,23 | Text auf Akzent `#005A96` |
| `#005A96` | `#2D78BC` | 1,56 | Akzent direkt auf Logo-Blau nur als Fläche mit Abstand, nicht als Linie/Text |

Achtung im Entwurf: Bei Akzent `#005A96` stehen auf Akzentflächen noch dunkle Schriften
(`#153859`, `#1f2328`: Buttons „Angebot anfragen“, Abschlussband) – das wäre unlesbar; dort Weiß bzw. `#DDE9F4` verwenden.

## Aufbau Startseite (Richtung B → Astro-Komponenten)

| Abschnitt | Inhalt | Komponente heute |
|---|---|---|
| Header | weißes Logo (`docs/assets/logo-mbgrabnar-weiss.png`), Navigation, Telefon-Button | `web/src/components/Header.astro` |
| Hero | Motto als Zitat, Versal-Headline, Subline, 2 Buttons, schräg angeschnittenes Foto rechts | `blocks/Hero.astro` |
| Fakten-Leiste | Meisterbetrieb · ISO 9001 · ISO 14001 · 22 Leistungen · Stuttgart & Region | neu (aus Settings/fest) |
| Leistungsbereiche | 4 Bereiche als große Bild-Text-Reihen, abwechselnd links/rechts, Leistungen als Liste | `blocks/ServiceGrid.astro` (Variante `categories`) |
| Merkmale | 6 Merkmale auf Blau, Raster mit feinen Trennlinien | `blocks/FeatureList.astro` |
| Karriere | Foto + Teaser + Button „Offene Stellen“ | neu (oder `TextImage` mit Variante) |
| Abschluss | Band mit Headline und großer Telefonnummer | `blocks/Cta.astro` |
| Footer | weißes Logo, Kontakt, Rechtliches, ISO-Siegel | `Footer.astro` |

Leistungsseite: Kopf auf Blau mit Kategorie-Marke, Versal-Titel, Kurztext, Button und Foto;
Fakten-Leiste; Einleitung zweispaltig; Objektliste als Raster auf Blau; „Passt auch dazu“; Abschlussband.

## Leitplanken (gelten unverändert)

- Block-Vertrag (`CLAUDE.md`): neue Blöcke/Varianten immer in `cms/blocks/`, `web/src/lib/types.ts`
  und `web/src/components/blocks/` zugleich.
- Lighthouse/axe müssen bei 100 / 0 Verstößen bleiben (`web/scripts/audit.mjs`, CI-Job `audit`).
- Tracking-Attribute (`umami()`/`track()`, `docs/05-tracking.md`) an Buttons/Links erhalten.
- Keine neuen Firmenaussagen; Platzhalter statt erfundener Zahlen; keine Privatkunden ansprechen.
- Bilder nur über Wagtail-Renditions; Foto-Platzhalter, bis die Firma liefert.
- Mobil zuerst prüfen (390 px), keine horizontale Scrollleiste.

## Prüfen

    cd cms && uv run manage.py seed_dev --superuser && uv run manage.py runserver
    cd web && pnpm dev                       # http://localhost:4321
    # produktionsnah + Audit: siehe docs/03-technik.md „Qualitätsprüfung“
