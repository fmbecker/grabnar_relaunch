# 07 · Bildmaterial – Bedarf, Briefing, Prompts, Stock

Stand: 13.11.2026 · gehört zu Richtung D (`docs/06-design.md`, Branch `feat/design-modern`).

Grundsatz aus `docs/02-konzept.md`: **echte Fotos von Team und Objekten statt Stock**. Stock und
generierte Bilder sind hier nur als Überbrückung gedacht, bis eigene Fotos vorliegen, und nur für
Motive ohne erkennbare Personen. Kein Bild darf etwas behaupten, das die Firma nicht bestätigt hat
(keine erfundenen Mitarbeitenden, Fahrzeuge, Kundenobjekte, Zertifikate).

Die Stockliste in Abschnitt 5 ist nach Titel und Beschreibung der Anbieter zusammengestellt –
**die Bilder selbst wurden nicht gesichtet**. Vor der Verwendung jedes Motiv ansehen und die Lizenz
auf der Seite des Anbieters prüfen.

## 1 · Technische Vorgaben

Das Frontend bekommt Bilder ausschließlich als Wagtail-Renditions (`cms/blocks/images.py`):

| Rendition | Zuschnitt | Verwendet in |
|---|---|---|
| `hero` | 2000 × 1000 (2:1) | `web/src/components/blocks/Hero.astro` |
| `wide` | 1600 × 900 (16:9) | Bereichskarten in `web/src/components/blocks/ServiceGrid.astro`, Kopf der Leistungsseite in `web/src/components/PageContent.astro` |
| `card` | 800 × 600 (4:3) | Leistungskarten, `TextImage.astro`, Galerie |
| `thumb` | 400 × 300 | kleine Vorschauen, `srcset` |

Daraus folgt für jede Lieferung:

- **Querformat, mindestens 2400 px breit** (besser 3000 px), JPEG in hoher Qualität oder TIFF. WebP und
  Größen erzeugt Wagtail selbst.
- **Motiv in der Bildmitte mit Rand ringsum.** Die Zuschnitte schneiden mittig; auf dem Handy wird der
  Hero zum Hochformat, die Bereichskarten werden auf dem Desktop zu einem schmalen Hochformat. Wichtiges
  darf nicht am Rand liegen. Der Ausschnitt lässt sich pro Bild über den Fokuspunkt in der
  Wagtail-Mediathek nachstellen.
- **Hero:** Der Text steht unten links auf einem dunklen Verlauf von links. Das linke Drittel des Bildes
  soll ruhig sein (Boden, Fassade, Himmel), das Hauptmotiv rechts der Mitte.
- **Farbwelt:** kühl und hell, Blau- und Grautöne, keine starken Rot- oder Gelbflächen außer
  Arbeitsmitteln. Passt zu Tiefblau `#0F2A44` und Logo-Blau `#2D78BC`.
- **Alt-Text** für jedes Bild in der Mediathek: was zu sehen ist, ein Satz, ohne „Bild von“.
- **Video (optional, Hero):** 8–15 s, ohne Ton, als Schleife schneidbar, 1920 × 1080, ruhige Kamera.
  Auslieferung als MP4 (H.264) plus WebM, zusammen unter ca. 3 MB, dazu ein Standbild. Braucht ein
  neues Feld im Hero-Block (`cms/blocks/blocks.py`, `web/src/lib/types.ts`,
  `web/src/components/blocks/Hero.astro`) und muss `prefers-reduced-motion` beachten.

## 2 · Bedarfsliste

Priorität A = ohne diese Bilder wirkt die Seite unfertig. B = jede Leistungsseite. C = Kür.

### A · Startseite und Rahmen (9 Bilder)

| Nr. | Platz | Feld im CMS | Motiv | Quelle |
|---|---|---|---|---|
| A1 | Hero Startseite | Startseite → Block „Hero“ → Bild | Team bei der Arbeit in einem Objekt in Stuttgart: Glasfront oder Foyer, zwei bis drei Mitarbeitende in Arbeitskleidung, Tätigkeit erkennbar | nur echtes Foto |
| A2 | Bereichskarte 01 Gebäudereinigung | Seite „Gebäudereinigung“ → Titelbild | Glasreinigung oder Bodenreinigung mit Maschine im Büro- oder Verwaltungsgebäude | echt, Stock möglich |
| A3 | Bereichskarte 02 Gebäudedienste | Seite „Gebäudedienste“ → Titelbild | Außenanlage eines Gewerbeobjekts: Grünpflege oder Winterdienst | echt, Stock möglich |
| A4 | Bereichskarte 03 Handwerkerdienste | Seite „Handwerkerdienste“ → Titelbild | Innenausbau: Trockenbau, Spachteln oder Malerarbeiten in einem Gewerberaum | echt, Stock möglich |
| A5 | Bereichskarte 04 Services | Seite „Services“ → Titelbild | Transport oder Räumung: beladenes Fahrzeug, Möbel, leerer Raum danach | echt, Stock möglich |
| A6 | Unternehmen, oben | Seite „Unternehmen“ → Block „Text + Bild“ | Firmensitz oder Team vor dem Gebäude, alternativ Fahrzeuge mit Logo | nur echtes Foto |
| A7 | Unternehmen, Qualität | Seite „Unternehmen“ → Block „Text + Bild“ | Objektleitung bei der Kontrolle im Objekt (Klemmbrett, Tablet) | nur echtes Foto |
| A8 | Karriere | Seite „Karriere“ → Block „Text + Bild“ | Zwei bis drei Mitarbeitende im Gespräch, Arbeitskleidung mit Logo, freundlich, nicht gestellt | nur echtes Foto |
| A9 | Vorschaubild für soziale Netzwerke | Einstellungen → „Standard-Social-Media-Bild“ | Variante von A1 oder Stuttgart-Ansicht mit Logo, 1200 × 630 | echt, Stock möglich |

### B · Leistungsseiten (22 Bilder, Feld „Titelbild“ der jeweiligen Seite)

| Nr. | Leistung | Motiv |
|---|---|---|
| B1 | Baureinigung | Feinreinigung in einem frisch fertiggestellten, leeren Raum; Folienreste, Sauger |
| B2 | Containerreinigung | Baustellen- oder Bürocontainer von außen, Reinigung der Innenräume |
| B3 | Desinfektion | Hand mit Tuch an Türgriff oder Handlauf, Detailaufnahme |
| B4 | Glas- und Fassadenreinigung | Abzieher auf großer Glasfläche, Hebebühne oder Teleskopstange |
| B5 | Grundreinigung | Einscheibenmaschine auf Hartboden, sichtbarer Unterschied vorher/nachher |
| B6 | Hallen- und Industriereinigung | Aufsitz-Scheuersaugmaschine in einer Halle |
| B7 | Sonderreinigung | Hochdruck- oder Spezialgerät im Einsatz, Schutzkleidung |
| B8 | Teppich- und Polsterreinigung | Sprühextraktionsgerät auf Teppichboden im Büro |
| B9 | Unterhaltsreinigung | Reinigungswagen im Büroflur, Wischen oder Staubsaugen |
| B10 | Grau- und Grünanlagenpflege | Heckenschnitt oder Rasenpflege an einem Gewerbeobjekt, Kehrmaschine auf Pflaster |
| B11 | Hausmeisterdienste | Kleine Reparatur: Leuchtmittel, Türschließer, Kontrollgang mit Schlüsselbund |
| B12 | Winterdienst | Räumfahrzeug oder Schneeschieber auf Gehweg vor Gewerbeobjekt, Streugut |
| B13 | Bauhilfsarbeiten | Schuttabtransport, Schubkarre, aufgeräumte Baustelle |
| B14 | Bodenverlegearbeiten | Verlegen von Designbelag oder Teppichfliesen, Hände und Werkzeug |
| B15 | Fliesenlegerarbeiten | Fliese wird ins Kleberbett gesetzt, Fliesenkreuze, Wasserwaage |
| B16 | Maler- und Maurerarbeiten | Farbrolle an Wand in einem Gewerberaum, abgeklebte Kanten |
| B17 | Trockenbau | Ständerwerk mit Gipskartonplatte, Akkuschrauber |
| B18 | Bodenversiegelung | Auftragen einer Beschichtung auf Hallen- oder Garagenboden, glänzende Fläche |
| B19 | Entrümpelung | Voller und leerer Raum, Container vor dem Gebäude |
| B20 | Arbeitnehmerüberlassung | Übergabe im Betrieb: zwei Personen in Arbeitskleidung, Handschlag oder Einweisung |
| B21 | Transportarbeiten | Transporter mit geöffneter Ladefläche, Sackkarre, Möbeldecken |
| B22 | Wach- und Schließdienste | Schließrunde: Hand am Türschloss, Schlüsselbund, Taschenlampe am Abend. Keine polizeiähnliche Uniform, keine Ausrüstung |

### C · Kür

| Nr. | Platz | Motiv |
|---|---|---|
| C1 | Hero-Video | 3–4 kurze Einstellungen aus A1, A2, B6: Abzieher auf Glas, Maschine fährt durchs Bild, Team geht durch ein Foyer |
| C2 | Galerie „Unternehmen“ | 6–8 Bilder: Fahrzeuge, Lager, Maschinen, Schulung |
| C3 | Merkmale-Block „Warum M. B. Grabnar“ | Ein Bild links neben der Liste; braucht ein neues Feld im Block |

## 3 · Briefing für Fotografin oder Fotograf

**Auftraggeber:** M. B. Grabnar Gebäudereinigungs- und Handwerker-Service GmbH, Stuttgart.
**Anlass:** Relaunch von www.grabnar.de. Die Seite richtet sich an gewerbliche und öffentliche
Auftraggeber sowie an Bewerberinnen und Bewerber, nicht an Privatkunden.

**Ziel der Bilder:** zeigen, dass hier ein Meisterbetrieb mit eigenen Leuten, eigener Technik und
Ordnung arbeitet. Die Bilder sollen nach der Firma aussehen, nicht nach Bilddatenbank.

**Bildsprache**

- Menschen bei der Arbeit, konzentriert und freundlich, nicht in die Kamera posierend. Ein bis zwei
  Porträts pro Person zusätzlich.
- Arbeitskleidung sauber und einheitlich, Logo sichtbar, wo vorhanden. Schutzausrüstung korrekt getragen
  (Handschuhe, Sicherheitsschuhe, Absturzsicherung) – Fehler darin fallen Fachkunden sofort auf.
- Helles, natürliches Licht, kühle Farbstimmung, wenig Bearbeitung. Keine starken Filter, kein
  Weitwinkel-Verzug.
- Aufgeräumte Bildränder: keine fremden Firmenlogos, Kennzeichen, Namensschilder, Bildschirme mit
  Inhalten, keine erkennbaren Dritten.
- Jedes Motiv dreifach: Totale (Raum und Person), Halbnah (Person und Gerät), Detail (Hände, Werkzeug,
  Oberfläche).
- Immer Querformat mit Luft um das Motiv. Für A1 zusätzlich eine Fassung, in der das linke Bilddrittel
  ruhig bleibt (dort steht später Text).

**Shotlist für einen Tag** (Reihenfolge nach Licht und Wegen anpassen)

| Zeit | Ort | Motive | Deckt ab |
|---|---|---|---|
| 07:30–09:30 | Büro- oder Verwaltungsobjekt eines Kunden, vor Betriebsbeginn | Reinigungswagen im Flur, Wischen, Staubsaugen, Desinfektion Türgriff, Teppichreinigung, Objektleitung bei der Kontrolle | A1, A2, A7, B3, B8, B9 |
| 09:30–11:00 | Dasselbe Objekt, außen | Glasreinigung mit Abzieher und Teleskopstange oder Hebebühne, Eingangsbereich, Außenanlage | A1 (Variante), A3, B4, B10 |
| 11:30–13:00 | Halle oder Lager | Aufsitz-Scheuersaugmaschine, Einscheibenmaschine, Hochdruckgerät | B5, B6, B7 |
| 14:00–15:30 | Laufende Ausbau-Baustelle | Trockenbau, Spachteln, Malerarbeiten, Bodenbelag, Fliesen, Schuttabtransport, Endreinigung | A4, B1, B13–B17 |
| 16:00–17:30 | Firmensitz Julius-Hölder-Straße 4 | Team vor dem Gebäude, Fahrzeuge, Lager, beladener Transporter, Porträts, Schlüsselübergabe | A5, A6, A8, B11, B20–B22, C2 |

Nicht an einem Tag zu schaffen und saisonal: Winterdienst (B12), Bodenversiegelung (B18), Entrümpelung
(B19), Containerreinigung (B2). Diese bei Gelegenheit vom Team mit dem Smartphone nach den Vorgaben
in Abschnitt 1 aufnehmen lassen oder vorerst aus Abschnitt 5 überbrücken.

**Vorab von der Firma zu klären**

- Welche Kundenobjekte dürfen gezeigt werden? Schriftliche Zustimmung des Kunden für Innen- und
  Außenaufnahmen einholen.
- Schriftliche Einwilligung aller abgebildeten Mitarbeitenden für Website, Stellenanzeigen und soziale
  Netzwerke; wer nicht möchte, wird nicht fotografiert. Regelung für den Fall des Ausscheidens treffen.
- Einheitliche, saubere Arbeitskleidung und gereinigte Fahrzeuge am Drehtag.

**Lieferung und Rechte**

- 60–80 ausgewählte, bearbeitete Bilder, JPEG in voller Auflösung, sRGB, Dateiname nach Motivnummer
  (zum Beispiel `A1-hero-foyer-01.jpg`).
- Zeitlich und räumlich unbeschränkte Nutzungsrechte für Website, Druck, Stellenanzeigen und soziale
  Netzwerke, inklusive Bearbeitung und Zuschnitt. Namensnennung nach Vereinbarung (ein Platz dafür ist
  im Impressum möglich).
- Optional: 6–8 Videoeinstellungen je 10–15 s nach C1, vom Stativ oder Gimbal, 25 fps, ohne Ton.

## 4 · Prompts für Bild- und Videogeneratoren

Nur für Motive **ohne erkennbare Personen**; Hände, Rückenansichten und Geräte sind in Ordnung.
A1, A6, A7, A8 und B20 werden nicht generiert. Generierte Bilder in der Mediathek im Titel mit
`[KI]` kennzeichnen, damit sie später gezielt durch echte Fotos ersetzt werden können.

Die Prompts sind auf Englisch, weil die meisten Generatoren damit genauer arbeiten. Aufbau:
**Stilblock + Motiv + Formatangabe.**

**Stilblock (an jeden Prompt anhängen)**

```
Documentary commercial photograph, natural daylight, cool neutral colour palette with blue and grey
tones, clean modern German commercial building, realistic materials and reflections, shallow depth of
field, shot on a full-frame camera with a 35mm lens, subject centred with generous empty space around
it, no visible faces, no text, no logos, no brand names, no watermarks.
```

**Ausschlüsse (als Negativ-Prompt, falls der Generator das Feld anbietet)**

```
faces, portraits, text, letters, logos, brand names, watermark, distorted hands, extra fingers,
cartoon, illustration, 3d render, oversaturated colours, lens flare, private home, living room,
kitchen, American street signs, yellow school bus
```

**Format:** Querformat 16:9, höchste verfügbare Auflösung; für den Hero-Ersatz 2:1.

| Nr. | Motiv-Prompt (vor den Stilblock setzen) |
|---|---|
| A2 / B4 | `Close view of a professional squeegee being pulled across a large floor-to-ceiling office window, water film and clean stripe clearly visible, a gloved hand and forearm in dark blue workwear entering from the right, blurred city buildings behind the glass.` |
| A3 / B10 | `Neatly trimmed hedges and a freshly swept paved forecourt in front of a modern office building, a battery hedge trimmer and a broom resting against a low wall, early morning light.` |
| A4 / B17 | `Interior fit-out of an empty commercial unit, metal stud wall half covered with plasterboard, a cordless screwdriver and a spirit level on a work platform, fine dust in the light from a window.` |
| A5 / B21 | `Open rear doors of a clean white panel van parked at a loading entrance of an office building, moving blankets, a hand truck and stacked boxes inside, no licence plate visible.` |
| B1 | `Freshly finished empty office room after construction, protective film being peeled from a window frame by a gloved hand, an industrial vacuum cleaner on the clean floor.` |
| B2 | `Row of stacked grey site office containers on a building site, one door open showing a freshly mopped interior with a mop bucket at the entrance.` |
| B3 | `Extreme close view of a gloved hand wiping a stainless-steel door handle with a blue microfibre cloth in an office corridor.` |
| B5 | `Single-disc floor machine with a red pad on a hard floor in a corridor, clear line between the dull uncleaned area and the glossy cleaned area, seen from a low angle.` |
| B6 | `Ride-on scrubber-dryer driving through a large bright warehouse, wet glossy track behind it on the concrete floor, operator seen from behind, high shelves blurred in the background.` |
| B7 | `Worker in protective overalls seen from behind using a pressure washer on a stained concrete ramp, clean stripe clearly visible, fine spray mist.` |
| B8 | `Spray extraction machine nozzle being drawn across a grey office carpet, visibly cleaner stripe behind it, only the worker's boots and the tool in frame.` |
| B9 | `Professional cleaning trolley with colour-coded cloths and a flat mop standing in a bright modern office corridor early in the morning, glass meeting rooms on one side.` |
| B11 | `Hands of a caretaker in dark workwear adjusting a door closer at the top of a glass entrance door, a small tool bag on the floor.` |
| B12 | `Compact municipal-style tractor with a snow plough blade clearing a snow-covered pavement in front of an office building at dawn, grit visible on the cleared path, driver not recognisable.` |
| B13 | `Tidy construction site interior, a wheelbarrow filled with rubble and a stack of filled rubble sacks next to a swept concrete floor.` |
| B14 | `Hands pressing a vinyl plank into place on a levelled floor in an empty office room, rubber mallet and spacers beside it.` |
| B15 | `Hands setting a large grey floor tile into fresh adhesive, tile spacers and a notched trowel beside it, spirit level lying across the tiles.` |
| B16 | `Paint roller applying white paint to a wall in an empty commercial room, crisp masking tape along the edge, a covered floor and a ladder in the background.` |
| B18 | `Glossy grey epoxy coating being rolled onto a garage floor, sharp edge between coated and uncoated concrete, roller on a long pole entering the frame.` |
| B19 | `Empty swept storage room with a single skip container visible through the open door outside, afternoon light on the bare floor.` |
| B22 | `Hand turning a key in the lock of a glass office door at dusk, a small torch in the other hand, warm interior light and blue evening light outside, plain dark jacket sleeve.` |
| A9 | `Wide view over a German city in a valley with wooded hills around it, modern office buildings in the foreground, soft morning haze, calm sky in the upper half.` |

**Video-Prompts (C1, je 8–10 s, 16:9, ohne Ton)**

```
1. Slow static shot: a squeegee is drawn across a large office window from top to bottom, the water
   film clears and blurred city buildings appear behind the glass. Natural daylight, cool colours,
   no faces, no text.
2. Slow tracking shot at floor level: a ride-on scrubber-dryer passes through a bright warehouse and
   leaves a wet glossy track on the concrete floor. Operator only from behind.
3. Static shot of a bright office corridor early in the morning: a cleaning trolley is pushed slowly
   through the frame from left to right by a person seen from behind in dark blue workwear.
```

Bei generierten Videos jede Einstellung auf Bildfehler prüfen (Hände, Spiegelungen, Geräte, die ihre
Form ändern); nur fehlerfreie Abschnitte verwenden.

## 5 · Stockmaterial zur Überbrückung

Quellen: Pexels, Unsplash und Pixabay. Lizenzen (Stand 13.11.2026, auf den verlinkten Seiten prüfen):

- Pexels: <https://www.pexels.com/license/> – kostenlos, auch gewerblich, ohne Pflicht zur Namensnennung.
- Unsplash: <https://unsplash.com/license> – kostenlos, auch gewerblich, ohne Pflicht zur Namensnennung.
  Bilder mit dem Hinweis „Unsplash+“ gehören nicht dazu; sie brauchen ein kostenpflichtiges Abo.
- Pixabay: <https://pixabay.com/service/license-summary/>

Die freien Lizenzen enthalten **keine Freigabe abgebildeter Personen, Marken oder Gebäude** und keine
Haftungsfreistellung. Deshalb: keine Bilder mit erkennbaren Gesichtern, fremden Firmenlogos oder
Kennzeichen verwenden. Für jedes verwendete Bild Quelle, Urheber und Abrufdatum in der Mediathek
im Feld „Beschreibung“ notieren.

### Einzelne Treffer

| Für | Titel laut Anbieter | Urheber | Link | Hinweis |
|---|---|---|---|---|
| A2, B4 | Window cleaner rappels down a building facade | Pavel Boltov | <https://unsplash.com/photos/window-cleaner-rappels-down-a-building-facade-6I0di73uRdw> | Unsplash-Lizenz; Seilzugang – nur verwenden, wenn die Firma das tatsächlich anbietet |
| A2, B4 | Man Cleaning Windows (große Glasfläche, Abzieher) | – | <https://www.pexels.com/photo/man-cleaning-windows-18885426/> | Person prüfen: erkennbar? |
| B9, C1 | Floor Being Mopped (Video, 3840 × 2160, 19 s) | Tima Miroshnichenko | <https://www.pexels.com/video/floor-being-mopped-6195524/> | als Hero-Schleife denkbar; Umgebung prüfen (kein Privathaushalt) |
| B9, C1 | A Person Mopping Clean A Comfort Room (Video, 1920 × 1080, 12 s) | David Smith | <https://www.pexels.com/video/a-person-mopping-clean-a-comfort-room-2517780/> | öffentlicher Sanitärraum |
| B6 | Warehouse worker mopping floor (neben Gabelstapler) | – | <https://pixabay.com/photos/industrial-security-logistic-1636387/> | älteres Bild, Auflösung prüfen |
| B6 | Warehouse worker cleaning floor | – | <https://pixabay.com/photos/industrial-security-logistic-1636380/> | Person mit Schutzausrüstung, Erkennbarkeit prüfen |
| B6 | Man cleaning hospital hallway with floor scrubber | Yunus Tuğ | <https://unsplash.com/photos/man-cleaning-hospital-hallway-with-floor-scrubber-jNZKolWNrgE> | **Unsplash+**, kostenpflichtig |
| A3, B10 | Man Cutting a Hedge with a Trimmer in the Garden | Aleksander Dumała | <https://www.pexels.com/photo/man-cutting-a-hedge-with-a-trimmer-in-the-garden-24595769/> | wirkt laut Beschreibung wie Privatgarten – Ausschnitt eng wählen |
| B10 | Crop gardener with secateurs working on bush (Detail, Hände) | Anna Shvets | <https://www.pexels.com/photo/crop-gardener-with-secateurs-working-on-bush-5231138/> | ohne Gesicht |
| B12 | Back View of a Snowplow Clearing the Street | – | <https://www.pexels.com/photo/back-view-of-a-snowplow-clearing-the-street-14531981/> | Wohnstraße; Fahrzeugtyp muss zur Leistung passen |
| B12 | A Person Removing Snow from the Sidewalk (Pflaster, Schneeschieber) | – | <https://www.pexels.com/photo/a-person-removing-snow-from-the-sidewalk-6952452/> | passt gut zu Gehwegräumung |
| A4, B17 | A Man Fixing the Wall (Trockenbau, Helm, Handschuhe) | Antoni Shkraba | <https://www.pexels.com/photo/a-man-fixing-the-wall-4981812/> | Person prüfen |
| B16 | A Man in White Shirt Painting a House (Spachteln einer Innenwand) | Tima Miroshnichenko | <https://www.pexels.com/photo/a-man-in-white-shirt-painting-a-house-6473966/> | Person prüfen |
| B16 | Men Painting a Room (zwei Maler, Innenraum) | – | <https://www.pexels.com/photo/men-painting-a-room-5493650/> | Schutzkleidung, Masken |
| B16 | Construction Worker Working on the White Wall of a House (Rückenansicht) | – | <https://www.pexels.com/photo/construction-worker-working-on-the-white-wall-of-a-house-5493669/> | Rückenansicht, gut geeignet |
| A4 | Professional Wall Renovation in Modern Interior | – | <https://www.pexels.com/photo/man-person-people-building-6474127/> | Person prüfen |
| A9, Unternehmen | Stuttgart skyline view with modern architecture | – | <https://www.pexels.com/photo/stuttgart-skyline-view-with-modern-architecture-28500923/> | Ortsangabe Stuttgart laut Anbieter |
| A9, Unternehmen | Blue Sky and White Clouds Over Green Trees Near a City (Stuttgart von oben) | Zhenning Shi | <https://www.pexels.com/photo/blue-sky-and-white-clouds-over-green-trees-near-a-city-12463988/> | Panorama |
| A9 | Aerial view of city during sunset (Stuttgart, Winter) | Bianca Ackermann | <https://unsplash.com/photos/aerial-view-of-city-during-sunset-3onDRIh1KH4> | Unsplash-Lizenz; warme Farben, passt nur bedingt zur kühlen Farbwelt |
| A9 | City skyline under cloudy sky during night time (Stuttgart) | Christian Lue | <https://unsplash.com/photos/city-skyline-under-cloudy-sky-during-night-time-nUlOYquiQLE> | Unsplash-Lizenz; Nachtaufnahme |

### Suchseiten für die übrigen Motive

| Für | Suchseite | Suchbegriffe für weitere Treffer |
|---|---|---|
| A2, B4 | <https://www.pexels.com/search/window%20cleaning/> · <https://unsplash.com/s/photos/window-cleaner> | squeegee, glass facade, lift platform |
| B9, A2 | <https://unsplash.com/s/photos/office-cleaning> · <https://www.pexels.com/search/commercial%20cleaning/> | janitor cart corridor, vacuum office carpet |
| B5, B6 | <https://unsplash.com/s/photos/floor-scrubber> | scrubber dryer, warehouse floor – viele Treffer sind Produktfotos eines Herstellers, die nicht passen |
| B12 | <https://www.pexels.com/search/snow%20removal/> · <https://unsplash.com/s/photos/snow-removal> | snow plow sidewalk, snowblower footpath |
| A3, B10 | <https://unsplash.com/s/photos/hedge-trimming> · <https://www.pexels.com/search/gardening%20services/> | landscaping commercial, leaf blower park |
| A4, B16, B17 | <https://www.pexels.com/search/professional%20painter/> | drywall installation, plastering wall |
| A9 | <https://www.pexels.com/search/stuttgart/> · <https://pixabay.com/images/search/skyline%20stuttgart/> | Stuttgart Fernsehturm, Stuttgart cityscape |
| C1 | <https://www.pexels.com/search/videos/cleaning%20the%20floor/> | office cleaning video, window cleaning video |

Ohne brauchbaren Einzeltreffer in dieser Recherche: B1, B2, B3, B7, B8, B11, B13–B15, B18–B22.
Dafür entweder die Prompts aus Abschnitt 4 nutzen oder mit diesen Begriffen suchen:
`post construction cleaning`, `site office container`, `disinfecting door handle`,
`pressure washing concrete`, `carpet extraction cleaning`, `caretaker repair door`,
`construction debris wheelbarrow`, `vinyl flooring installation`, `tile installation`,
`epoxy floor coating`, `empty storage room`, `moving van loading`, `locking door key night`.

## 6 · Reihenfolge

1. Firma klärt Objekte, Einwilligungen und Termin (Abschnitt 3).
2. Bis dahin A2–A5 und A9 aus Abschnitt 5 oder 4 überbrücken; A1 bleibt bis zum echten Foto bei den
   gezeichneten Türmen.
3. Nach dem Drehtag: Auswahl, Zuschnitt und Fokuspunkte in der Mediathek, Alt-Texte, dann die
   überbrückten Bilder ersetzen und `[KI]`- sowie Stock-Einträge löschen.
