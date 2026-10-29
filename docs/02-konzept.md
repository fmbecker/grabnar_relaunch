# 02 – Konzept: Ziele, Zielgruppen, Seitenbaum, Inhaltsmodell

## Ziele des Relaunchs

1. **Anfragen von Gewerbekunden** erzeugen – klare Leistungsdarstellung, sichtbarer Kontakt-CTA auf jeder Seite.
2. **Bewerbungen** erleichtern – eigene Karriereseite mit Stellen aus dem CMS, kurzes Bewerbungsformular (Name, Kontakt, Wunschstelle, optional Lebenslauf-Upload).
3. **Wartbarkeit** – Redakteure pflegen Inhalte in Wagtail, Felix wartet zwei klar getrennte Systeme ohne Framework-Lock-in.
4. **Performance & SEO** – statische Seiten, Lighthouse ≥ 95, saubere Meta-Daten, strukturierte Daten (`LocalBusiness`, `JobPosting`).

## Zielgruppen und Kernbotschaften

| Zielgruppe | Braucht | Botschaft |
|---|---|---|
| Hausverwaltungen, Facility-Verantwortliche, Geschäftsführer KMU | Zuverlässigkeit, Referenzen, schnelle Angebotsanfrage | Ein Ansprechpartner für Reinigung, Hausmeister, Handwerk, Winterdienst – regional, seit Jahren etabliert |
| Bewerber (Reinigungskräfte, Vorarbeiter, Objektleitung) | Offene Stellen, einfache Bewerbung, ehrliche Infos zu Arbeitsort/Zeiten | Sicherer Arbeitsplatz in der Region, faire Bedingungen, unkomplizierte Bewerbung |
| Privatkunden (optional) | Preisorientierung, Terminanfrage | Einzelne Leistungen auch für Privathaushalte |

## Seitenbaum (Soll)

**Vorschlag v2 (nach Export der Altseite, ⬜ Freigabe durch Felix):** Die Altseite hat 4 Leistungskategorien mit 22 Leistungen (siehe `docs/01-ist-analyse.md`). Diese Struktur bleibt erhalten, die Kategorien bleiben auf oberster Ebene. Dadurch ändern sich die URLs nur in Schreibweise (klein, ohne Umlaute), was für Rankings am verträglichsten ist.

```
/                                              HomePage
/gebaeudereinigung/                            ServiceIndexPage (Kategorie)
  baureinigung/  containerreinigung/  desinfektion/  glasreinigung/  grundreinigung/
  industriereinigung/  sonderreinigung/  polsterreinigung/  unterhaltsreinigung/   ServicePage
/gebaeudedienste/                              ServiceIndexPage (Kategorie)
  gruenanlagenpflege/  hausmeisterdienste/  winterdienst/                           ServicePage
/handwerkerdienste/                            ServiceIndexPage (Kategorie)
  bauhilfsarbeiten/  bodenverlegerarbeiten/  fliesenlegerarbeiten/  malerarbeiten/
  trockenbau/  bodenversiegelung/                                                  ServicePage
/services/                                     ServiceIndexPage (Kategorie)
  entruempelung/  arbeitnehmerueberlassung/  transportarbeiten/  wachdienste/       ServicePage
/unternehmen/                                  StandardPage (neu: Über uns, Meisterbetrieb, QM)
/karriere/                                     JobIndexPage (ersetzt die leere /stellenangebote/)
/karriere/<slug>/                              JobPage
/kontakt/                                      StandardPage mit ContactFormBlock + Karte
/impressum/  /datenschutz/  /agb/              StandardPage
```

Entfällt: `/kontaktformular/` und `/kontaktformular/form/` (Duplikat), `/danke/` (Erfolgsmeldung erscheint direkt im Formular). Alle drei werden auf `/kontakt/` umgeleitet.

Code-Anpassung dafür (klein): `ServiceIndexPage.max_count = 1` entfernen und `verbose_name` auf „Leistungskategorie“ ändern; `seed_dev` und `grabnar/tests/test_api.py` auf die vier Kategorien umstellen; Hauptnavigation zeigt die vier Kategorien mit ihren Leistungen als Untermenü (der Navigations-Endpunkt liefert bereits zwei Ebenen).

Alte URLs → neue URLs: `docs/redirects.csv` (28 Weiterleitungen, automatisch aus dem Export erzeugt). Import beim Go-Live über `wagtail.contrib.redirects`.

## Inhaltsmodell (Wagtail-Seitentypen)

Alle Seitentypen erben von `BasePage` (abstract) mit SEO-Feldern (`seo_title`, `search_description`, `og_image`) und `body = StreamField(...)`.

| Seitentyp | Zusatzfelder | Erlaubte Kinder |
|---|---|---|
| `HomePage` | `hero` (HeroBlock, Pflicht), `body` | Service/Job/Standard-Index |
| `StandardPage` | `intro`, `body` | StandardPage |
| `ServiceIndexPage` | `intro`, `body` | ServicePage |
| `ServicePage` | `icon`, `teaser` (für Kacheln), `hero_image`, `body`, `related_services` | – |
| `JobIndexPage` | `intro`, `benefits` (ListBlock), `body` | JobPage |
| `JobPage` | `location`, `employment_type`, `start_date`, `description` (StreamField), `valid_through`, `show_apply_form` | – |

Site-weite Einstellungen (`wagtail.contrib.settings`): `ContactSettings` (Adresse, Telefon, E-Mail, Öffnungszeiten, Geo-Koordinaten), `FooterSettings` (Linkspalten, Social), `TrackingSettings` (Consent-pflichtige Scripte, standardmäßig leer).

## StreamField-Blocks (Block-Vertrag, siehe CLAUDE.md)

| Block (`cms/blocks/`) | Astro-Komponente (`web/src/components/blocks/`) | Inhalt |
|---|---|---|
| `HeroBlock` | `Hero.astro` | Headline, Subline, Bild, 1–2 CTAs |
| `RichTextBlock` | `RichText.astro` | Fließtext (eingeschränkte Features) |
| `TextImageBlock` | `TextImage.astro` | Text + Bild, Ausrichtung links/rechts |
| `ServiceGridBlock` | `ServiceGrid.astro` | automatisch alle ServicePages oder manuelle Auswahl |
| `FeatureListBlock` | `FeatureList.astro` | Icon + Titel + Text, 3–6 Stück |
| `StatsBlock` | `Stats.astro` | Kennzahlen („seit 19xx“, „x Mitarbeiter“) |
| `TestimonialBlock` | `Testimonial.astro` | Zitat, Name, Firma |
| `FaqBlock` | `Faq.astro` | Frage/Antwort-Liste (Accordion, kein JS nötig: `<details>`) |
| `CtaBlock` | `Cta.astro` | Flächiger Call-to-Action mit Button |
| `ContactFormBlock` | `islands/ContactForm.tsx` | React-Island, POST an `cms/forms_api` |
| `JobListBlock` | `JobList.astro` + optional `islands/JobFilter.tsx` | Liste aller gültigen JobPages |
| `MapBlock` | `Map.astro` | statische Karte/Leaflet ohne Google-Tracking |
| `GalleryBlock` | `Gallery.astro` | Bildergalerie, Lightbox optional als Island |

## Design-Richtung

**Markenfarben (aus Logo und `custom.css` der Altseite, per Pixelanalyse bestätigt):**

| Token | Hex | Verwendung |
|---|---|---|
| `brand-500` | `#2D78BC` | Logo-Blau „M B GRABNAR“: Buttons, Links, Icons. Weiß darauf = 4,64:1 (WCAG AA) |
| `brand-300` / `accent-400` | `#8BC1E5` | Logo-Hellblau (Türme, Unterzeile): Akzente, Flächen, Vorschau-Banner |
| `brand-600`…`950` | `#2768A3` … `#102C48` | Abdunklungen: Hover, Hero- und Footer-Flächen |
| `ink-900` / `ink-700` | `#1F2328` / `#39424C` | Text (Anthrazit aus der Altseite) |
| `ink-300` | `#D4D4D5` | Linien, Rahmen (Altseite) |

Die Skala steht in `web/src/styles/global.css` (`@theme`). Das Bootstrap-Blau `#007BFF` der Altseite war nur der Framework-Standard, nicht die Markenfarbe.

**Logo:** `docs/assets/logo-mbgrabnar.png` (917 × 539, transparent, Original vom Server). `import_legacy` übernimmt es in die Mediathek und setzt es in den Website-Einstellungen; das Frontend nutzt unbeschnittene Renditions (`height-80`/`height-160`, 1x/2x). Favicon und Touch-Icon (`web/public/`) zeigen die drei Gebäude-Türme aus dem Logo. ⬜ Vektorversion (SVG) bei der Firma anfragen bzw. nachbauen und abnehmen lassen.

**Typografie:** Die Altseite nutzt nur Arial, es gibt keine Hausschrift. Vorschlag: Inter (selbst gehostet), weil sie der Logo-Schrift (Grotesk) nahekommt und am Bildschirm besser lesbar ist.

**Weiteres:**
- Bildsprache: echte Fotos von Team und Objekten statt Stock (die Altseite nutzt fast nur Unsplash).
- Mobile first – Bewerber kommen überwiegend vom Smartphone.
- Barrierefreiheit: WCAG 2.1 AA als Mindestziel (Kontraste, Fokus-Stile, Formular-Labels).

## Nicht im Scope (Phase 1)

- Kundenportal / Login
- Mehrsprachigkeit (vorbereitet über `wagtail-localize`-kompatible Struktur, aber nicht aktiviert)
- Blog/News (kann später als `ArticlePage` ergänzt werden)
