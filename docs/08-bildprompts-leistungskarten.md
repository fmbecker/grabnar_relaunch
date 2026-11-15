# 08 · Bildprompts für die Leistungskarten

Stand: 15.11.2026 · ergänzt `docs/07-bildmaterial.md` (Bedarf, Briefing, Stock) · gehört zu Richtung D
(`docs/06-design.md`, Branch `feat/design-modern`).

Dieses Dokument enthält für **alle 4 Bereichskarten und alle 22 Leistungskarten** je zwei Prompts:

- **Prompt A – Tätigkeit:** die Arbeit im Gang, Gerät im Einsatz, Mensch höchstens von hinten oder als Hände.
- **Prompt B – Alternative:** ein anderes Motiv derselben Leistung, meist Ergebnis, Detail oder Arbeitsplatz
  ohne Person. B ist kein Ersatz in gleicher Einstellung, sondern eine zweite Bildidee – falls A im Generator
  misslingt oder neben den Nachbarkarten zu ähnlich wirkt.

Die Motive sind aus den Kurztexten in `docs/content-overrides.csv` abgeleitet, damit kein Bild etwas zeigt,
das die Seite nicht anbietet. Die Nummern (A2–A5, B1–B22) sind dieselben wie in `docs/07-bildmaterial.md`.

Es gilt weiter der Grundsatz aus `docs/02-konzept.md`: echte Fotos statt generierter Bilder. Diese Prompts
überbrücken die Zeit bis zum Fototermin.

## 1 · Wo das Bild erscheint und was das für den Bildaufbau heißt

Jede Seite hat **ein** Bildfeld („Titelbild“). Dieses eine Bild wird an mehreren Stellen unterschiedlich
beschnitten:

| Stelle | Datei | Rendition | Sichtbarer Ausschnitt |
|---|---|---|---|
| Leistungskarte auf der Bereichsseite (z. B. `/gebaeudereinigung/`) | `web/src/components/blocks/ServiceGrid.astro` | `card` 800 × 600 | Querformat 3:2, fast das ganze Bild; oben links liegt ein weißer Kreis mit Symbol (48 px) |
| Kopf der Leistungsseite (z. B. `/gebaeudereinigung/baureinigung/`) und, seit Commit `b31f204`, Kopf der Bereichsseite (z. B. `/gebaeudereinigung/`) | `web/src/components/PageContent.astro` | `hero` 2000 × 1000 | Desktop: Feld rechts neben dem Text, etwa 4:3; Handy: flacher Streifen, etwa 16:9 – oben und unten fällt Bild weg |
| Bereichskarte auf der Startseite (nur A2–A5) | `web/src/components/blocks/ServiceGrid.astro` | `wide` 1600 × 900 | Handy: 16:10; Desktop: **schmales Hochformat** in der linken Kartenspalte – links und rechts fällt viel weg; oben links liegt die Nummer (48 px) |

Daraus folgen vier Regeln, die in jedem Prompt schon berücksichtigt sind:

1. **Format 3:2 quer**, höchste Auflösung des Generators, mindestens 2400 px breit (sonst hochskalieren).
2. **Hauptmotiv im mittleren Drittel**, vollständig sichtbar, mit Luft nach allen Seiten.
3. **Obere linke Ecke ruhig** (Wand, Decke, Himmel), weil dort Symbol oder Nummer liegen.
4. Für die vier Bereichsbilder (A2–A5) muss das Motiv auch als **schmaler senkrechter Streifen** aus der
   Bildmitte funktionieren – deshalb stehen dort aufrechte Motive (Person von hinten, Gerät, Tür).

Passt ein Ausschnitt trotzdem nicht: Fokuspunkt des Bildes in der Wagtail-Mediathek setzen.

## 2 · Aufbau eines Prompts

**Motiv-Prompt (aus den Tabellen) + Stilblock + Formatzeile.** Die Prompts sind auf Englisch, weil die
Generatoren damit genauer arbeiten.

**Stilblock – an jeden Prompt anhängen**

```
Documentary commercial photograph, natural daylight, cool neutral colour palette with blue and grey
tones, modern German commercial building, realistic materials and reflections, shallow depth of field,
full-frame camera, 35mm lens, main subject in the central third of the frame with generous empty space
around it, calm uncluttered upper left corner, no visible faces, no text, no logos, no brand names,
no watermarks.
```

**Formatzeile**

```
Landscape format, aspect ratio 3:2, highest available resolution.
```

**Ausschlüsse – als Negativ-Prompt, falls der Generator ein eigenes Feld dafür hat**

```
faces, portraits, looking at camera, text, letters, signage, logos, brand names, watermark, distorted
hands, extra fingers, cartoon, illustration, 3d render, oversaturated colours, lens flare, private home,
living room, kitchen, children, patients, American street signs, licence plates
```

**Einheitliche Bausteine**, damit die 26 Bilder wie eine Serie wirken – sie stehen wörtlich in den Prompts:

- Kleidung: `plain dark navy workwear without logos`
- Personen: `seen from behind` oder nur `gloved hands and forearms`
- Licht: Tageslicht, früher Morgen; Ausnahmen sind Winterdienst (Morgendämmerung) und Wach- und
  Schließdienste (Abenddämmerung)

## 3 · Die vier Bereichskarten (Startseite)

Feld: Titelbild der Seiten `/gebaeudereinigung/`, `/gebaeudedienste/`, `/handwerkerdienste/`, `/services/`.

| Nr. | Bereich | Prompt A – Tätigkeit | Prompt B – Alternative |
|---|---|---|---|
| A2 | 01 [Gebäudereinigung](http://localhost:4321/gebaeudereinigung/) | `A cleaner in plain dark navy workwear without logos, seen from behind, standing upright in the centre of a bright office foyer and drawing a squeegee down a tall floor-to-ceiling window, a professional cleaning trolley beside them, polished stone floor reflecting the daylight.` | `A professional cleaning trolley with colour-coded cloths and an upright flat mop standing alone in the centre of a spotless modern office foyer, glossy floor reflecting tall windows, early morning light, no people.` |
| A3 | 02 [Gebäudedienste](http://localhost:4321/gebaeudedienste/) | `A caretaker in plain dark navy workwear without logos, seen from behind, walking along the paved path towards the glass entrance of a modern office building, a tool bag in one hand and a bunch of keys in the other, neatly trimmed hedges on both sides, early morning light.` | `The well-kept entrance of a modern office building seen straight on, glass door in the centre, freshly swept paving, trimmed hedges and a young tree in planters on both sides, a broom leaning upright next to the door, no people.` |
| A4 | 03 [Handwerkerdienste](http://localhost:4321/handwerkerdienste/) | `A tradesman in plain dark navy workwear without logos, seen from behind, standing on a low work platform in the centre of an empty commercial room and smoothing fresh filler on a new plasterboard wall with a wide trowel, daylight from a window on the right, covered floor.` | `An upright aluminium stepladder in the centre of a freshly renovated empty commercial room, a paint roller, a spirit level and a bucket standing at its foot, new white walls and a new grey floor, daylight from the side, no people.` |
| A5 | 04 [Services](http://localhost:4321/services/) | `Two workers in plain dark navy workwear without logos, seen from behind, carrying an office desk through the open double door of a commercial building towards a clean white panel van with open rear doors, hand truck standing beside the van, no licence plate visible.` | `Open rear doors of a clean white panel van seen straight on at the loading entrance of an office building, moving blankets, stacked boxes and an upright hand truck neatly secured inside, no people, no licence plate visible.` |

Hinweise zu den Bereichsbildern

- A2–A5 sollen sich klar voneinander unterscheiden: innen/Glas (A2), außen/Grün (A3), Rohbau-Innenraum (A4),
  Fahrzeug (A5). Bei der Auswahl darauf achten, dass nicht zwei Bilder denselben Bildaufbau haben.
- A5: Fahrzeug ohne Beschriftung erzeugen. Ein generiertes Fahrzeug mit Firmenlogo wäre eine Behauptung, die
  nicht stimmt.

## 4 · Bereich 01 – Gebäudereinigung (9 Leistungskarten)

| Nr. | Leistung | Prompt A – Tätigkeit | Prompt B – Alternative |
|---|---|---|---|
| B1 | [Baureinigung](http://localhost:4321/gebaeudereinigung/baureinigung/) | `A cleaner in plain dark navy workwear without logos, seen from behind, vacuuming fine construction dust from the floor of a newly built empty office room with an industrial vacuum cleaner, protective film still on the window frames, a clear line between dusty and clean floor.` | `Gloved hands peeling blue protective film from a new white window frame in a freshly finished empty room, clean glass behind it, a folded cloth and a scraper on the window sill, soft daylight.` |
| B2 | [Containerreinigung](http://localhost:4321/gebaeudereinigung/containerreinigung/) | `A cleaner in plain dark navy workwear without logos, seen from behind, mopping the floor inside a grey site office container with a flat mop, the container door open to a building site with scaffolding blurred in the background, simple desk and chairs pushed aside.` | `A row of stacked grey site office containers on a building site seen from the front, one door in the centre standing open with a mop bucket and a flat mop at the entrance, freshly cleaned steps, overcast daylight, no people.` |
| B3 | [Desinfektion nach IfSG §17/3](http://localhost:4321/gebaeudereinigung/desinfektion/) | `Close view of a gloved hand in a blue nitrile glove wiping a stainless-steel door handle with a white disposable cloth in a bright corridor of a public building, a spray bottle without label held in the other hand, door and wall softly blurred.` | `Gloved hands in blue nitrile gloves wiping the stainless-steel handrail of a staircase in a public building with a white disposable cloth, steps and wall softly blurred, clean clinical daylight, no other people.` |
| B4 | [Glas- und Fassadenreinigung](http://localhost:4321/gebaeudereinigung/glasreinigung/) | `A window cleaner in plain dark navy workwear without logos, seen from behind, cleaning the glass facade of an office building from the outside with a squeegee on a long telescopic pole, a clear clean stripe in the wet glass, sky reflected in the windows.` | `A light-coloured facade panel of a commercial building being cleaned with a soft washing lance, sharp line between the weathered grey area and the freshly cleaned bright area in the centre, only the lance and a gloved hand entering the frame from the right.` |
| B5 | [Grundreinigung](http://localhost:4321/gebaeudereinigung/grundreinigung/) | `A cleaner in plain dark navy workwear without logos, seen from behind, guiding a single-disc floor machine with a red pad across the hard floor of an empty corridor, clear line between the dull uncleaned area and the glossy cleaned area, low camera angle.` | `Gloved hands cleaning between the fins of a white wall radiator with a long narrow brush in an empty office room, a bucket and a cloth on the floor beside it, the freshly cleaned window sill above, soft daylight.` |
| B6 | [Hallen- und Industriereinigung](http://localhost:4321/gebaeudereinigung/industriereinigung/) | `A ride-on scrubber-dryer driving through the centre aisle of a large bright production hall, operator in plain dark navy workwear without logos seen from behind, wet glossy track behind the machine on the grey industrial floor, machinery and yellow floor markings softly blurred.` | `A clean grey industrial floor with yellow lane markings in a large production hall, a walk-behind scrubber-dryer parked upright in the centre of the aisle, machines softly blurred at the sides, light falling from skylights, no people.` |
| B7 | [Sonderreinigung](http://localhost:4321/gebaeudereinigung/sonderreinigung/) | `A cleaner in plain dark navy workwear without logos and disposable gloves, seen from behind, pushing a hospital cleaning trolley with colour-coded buckets and cloths along an empty bright clinic corridor with handrails on the walls, clean reflective floor, no patients.` | `Close view of a hospital cleaning trolley in an empty clinic corridor, four colour-coded buckets, neatly folded colour-coded microfibre cloths and a pre-soaked flat mop system, handrail and closed doors softly blurred, no people.` |
| B8 | [Teppich- und Polsterreinigung](http://localhost:4321/gebaeudereinigung/polsterreinigung/) | `The floor tool of a spray extraction machine being drawn across a grey office carpet, a visibly cleaner and brighter stripe behind it, only the tool, the hose and the boots of a worker in dark navy trousers in frame, desks softly blurred.` | `A gloved hand guiding a small upholstery nozzle of a spray extraction machine across the seat of a grey fabric lounge chair in an office waiting area, a cleaner stripe visible on the fabric, the machine standing beside the chair.` |
| B9 | [Unterhaltsreinigung](http://localhost:4321/gebaeudereinigung/unterhaltsreinigung/) | `A cleaner in plain dark navy workwear without logos, seen from behind, wiping a desk surface with a blue microfibre cloth in a bright open-plan office early in the morning, a cleaning trolley with colour-coded cloths beside them, empty chairs and screens switched off.` | `An empty bright school corridor with a freshly mopped floor, a flat mop and a yellow wet-floor cone without text standing in the centre, coat hooks and closed classroom doors softly blurred, morning light, no people.` |

Hinweise zu Bereich 01

- **B3 Desinfektion:** keine Schutzanzüge, Atemmasken oder Sprühnebel. Das wirkt nach Seuchenfall und passt
  nicht zum Angebot (Vorbeugung durch geschultes Personal).
- **B4 Glas und Fassade:** kein Seilzugang, keine Fassadengondel – es ist nicht bestätigt, dass die Firma so
  arbeitet. Teleskopstange und Lanze sind unverfänglich.
- **B7 Sonderreinigung:** Der Seitentext nennt die Krankenhausreinigung als Beispiel. Keine Patienten, keine
  Betten mit Personen, kein OP-Saal.
- **B9 Unterhaltsreinigung, Prompt B:** Schule ohne Kinder. Der Warnkegel ohne Schrift, sonst erfindet der
  Generator Fantasietext.

## 5 · Bereich 02 – Gebäudedienste (3 Leistungskarten)

| Nr. | Leistung | Prompt A – Tätigkeit | Prompt B – Alternative |
|---|---|---|---|
| B10 | [Grau- und Grünanlagenpflege](http://localhost:4321/gebaeudedienste/gruenanlagenpflege/) | `A groundskeeper in plain dark navy workwear without logos, ear protection and gloves, seen from behind, trimming a long hedge with a battery hedge trimmer in front of a modern office building, freshly cut edge clearly visible, paved path beside the hedge.` | `A surface cleaner attachment of a hot-water pressure washer moving across grey concrete paving in front of a commercial building, a bright clean stripe through the dark stained paving in the centre, only the tool and the boots of a worker in frame.` |
| B11 | [Hausmeisterdienste](http://localhost:4321/gebaeudedienste/hausmeisterdienste/) | `Hands and forearms of a caretaker in plain dark navy workwear without logos adjusting the door closer at the top of a glass entrance door with a screwdriver, a small open tool bag on the floor, bright entrance hall softly blurred.` | `A caretaker in plain dark navy workwear without logos, seen from behind, standing in a tidy plant room and checking the pressure gauges of a heating system, a clipboard in one hand, insulated pipes and valves in neat rows, cool even light.` |
| B12 | [Winterdienst](http://localhost:4321/gebaeudedienste/winterdienst/) | `A compact tractor with a snow plough blade clearing a snow-covered pavement in front of an office building at dawn, headlights on, cleared dark path behind it with grit visible, driver not recognisable, snow on hedges and bollards.` | `A walk-behind grit spreader standing on a freshly cleared paved path leading to the glass entrance of an office building at dawn, a snow shovel leaning upright against a bollard, grit visible on the dark wet paving, snow piled neatly at the sides, no people.` |

Hinweise zu Bereich 02

- **B10:** Der Seitentext nennt ausdrücklich das Entfernen von Öl-, Fett- und Kaugummiflecken – Prompt B zeigt
  genau das (Grauflächen), Prompt A die Grünpflege.
- **B12:** Morgendämmerung, weil der Text die frühen Morgenstunden nennt. Kein Großfahrzeug mit Blaulicht-Optik,
  kein Autobahn-Räumfahrzeug.

## 6 · Bereich 03 – Handwerkerdienste (6 Leistungskarten)

| Nr. | Leistung | Prompt A – Tätigkeit | Prompt B – Alternative |
|---|---|---|---|
| B13 | [Bauhilfsarbeiten](http://localhost:4321/handwerkerdienste/bauhilfsarbeiten/) | `A worker in plain dark navy workwear without logos, safety helmet and gloves, seen from behind, pushing a wheelbarrow filled with rubble through an emptied commercial room during interior demolition, exposed concrete floor, daylight from a large window.` | `A tidy interior demolition site in an empty commercial room, a wheelbarrow with rubble in the centre, filled rubble sacks stacked neatly beside it, a broom and a shovel leaning upright against a bare wall, swept concrete floor, no people.` |
| B14 | [Bodenverlegerarbeiten](http://localhost:4321/handwerkerdienste/bodenverlegerarbeiten/) | `Gloved hands clicking an oak laminate plank into the row of an almost finished floor in an empty office room, a rubber mallet and a tapping block beside it, underlay visible at the unfinished edge, low camera angle.` | `A roll of grey carpet being unrolled across the levelled floor of an empty office room, a carpet knife and a knee kicker lying on the unrolled part, only the hands and knees of a worker in dark navy trousers in frame.` |
| B15 | [Fliesenlegerarbeiten](http://localhost:4321/handwerkerdienste/fliesenlegerarbeiten/) | `Gloved hands setting a large grey porcelain floor tile into fresh adhesive, tile spacers between the laid tiles, a notched trowel and a spirit level lying across the finished row, low camera angle.` | `A half-tiled wall in a new sanitary room of a commercial building, large light grey wall tiles with tile spacers in the centre, bare primed wall above, a notched trowel and a bucket of adhesive on a small work platform, no people.` |
| B16 | [Maler- und Maurerarbeiten](http://localhost:4321/handwerkerdienste/malerarbeiten/) | `A painter in white work trousers and a plain dark navy shirt without logos, seen from behind, rolling white paint onto a wall of an empty commercial room with a paint roller on a short pole, crisp masking tape along the door frame, covered floor.` | `Gloved hands applying fresh plaster to a brick wall with a steel plastering trowel, the plastered smooth area on the right and exposed brickwork on the left meeting in the centre, a hawk with plaster held in the other hand.` |
| B17 | [Trockenbau](http://localhost:4321/handwerkerdienste/trockenbau/) | `A drywall installer in plain dark navy workwear without logos, seen from behind, screwing a plasterboard panel onto a metal stud partition with a cordless screwdriver in an empty commercial unit, open studs visible beside the panel, fine dust in the daylight.` | `A suspended ceiling under construction in an empty commercial room seen from below at an angle, metal grid half filled with white ceiling panels in the centre, open grid and hangers beside it, a platform ladder standing underneath, no people.` |
| B18 | [Bodenversiegelung](http://localhost:4321/handwerkerdienste/bodenversiegelung/) | `A worker in plain dark navy workwear without logos, seen from behind, spreading a clear floor sealer across a cleaned hard floor with a wide flat applicator on a long pole, sharp edge between the matt unsealed area and the glossy sealed area in the centre.` | `Close view of water droplets beading on a freshly sealed grey hard floor, windows reflected in the glossy surface, a wide flat applicator lying at the edge of the frame, shallow depth of field, no people.` |

Hinweise zu Bereich 03

- **B14:** Der Seitentext nennt Parkett, Laminat, Kork, PVC und Teppich. A zeigt Hartbelag, B Teppich – wer
  lieber PVC zeigen will, ersetzt in B `a roll of grey carpet` durch `a roll of grey vinyl flooring`.
- **B16:** A deckt den Maler-, B den Maurerteil ab. Wenn nur ein Bild verwendet wird, A nehmen: Es ist auf der
  kleinen Karte leichter zu erkennen.
- **B18:** Versiegelung, keine farbige Epoxidbeschichtung – der Text beschreibt das Versiegeln nach einer
  Grundreinigung.
- Schutzausrüstung muss stimmen (Helm bei Abbruch, Handschuhe, Sicherheitsschuhe). Bilder mit offensichtlichen
  Verstößen aussortieren.

## 7 · Bereich 04 – Services (4 Leistungskarten)

| Nr. | Leistung | Prompt A – Tätigkeit | Prompt B – Alternative |
|---|---|---|---|
| B19 | [Entrümpelung](http://localhost:4321/services/entruempelung/) | `Two workers in plain dark navy workwear without logos and gloves, seen from behind, carrying an old office cabinet out of a cluttered storage room towards an open door, stacked old chairs and boxes at the sides, daylight from the doorway.` | `An empty, broom-clean storage room in a commercial building, a broom leaning upright against the wall in the centre, bare swept floor, afternoon light from the open door, a skip container visible outside through the doorway, no people.` |
| B20 | [Arbeitnehmerüberlassung](http://localhost:4321/services/arbeitnehmerueberlassung/) | `Close view of a handshake between two people in plain dark navy workwear without logos in a bright workshop, only hands and forearms in frame, work gloves tucked into a belt, workbench and shelves softly blurred.` | `A row of clean work gear hanging ready on hooks in a bright staff room, plain high-visibility vests, safety helmets and work gloves in a neat line, a bench with safety shoes underneath, no people.` |
| B21 | [Transportarbeiten](http://localhost:4321/services/transportarbeiten/) | `A worker in plain dark navy workwear without logos, seen from behind, pushing a hand truck with stacked moving boxes up a ramp into a clean white panel van parked at the entrance of an office building, moving blankets visible inside, no licence plate visible.` | `Interior of a clean panel van seen from the open rear doors, office furniture wrapped in moving blankets and secured with ratchet straps, stacked boxes and an upright hand truck, daylight falling in from behind, no people.` |
| B22 | [Wach- und Schließdienste](http://localhost:4321/services/wachdienste/) | `Close view of a hand turning a key in the lock of a glass office door at dusk, a small torch held in the other hand, plain dark jacket sleeve, warm interior light behind the glass and blue evening light outside.` | `An empty reception desk in the entrance hall of an office building in the evening, a visitor log book, a key cabinet on the wall behind it and a desk lamp switched on, glass entrance door softly blurred, no people.` |

Hinweise zu Bereich 04

- **B20 Arbeitnehmerüberlassung:** `docs/07-bildmaterial.md` empfiehlt hier ein echtes Foto. Die Prompts
  zeigen deshalb nur Hände oder Ausrüstung – keine erfundenen Mitarbeitenden.
- **B22 Wach- und Schließdienste:** keine polizeiähnliche Uniform, keine Abzeichen, keine Ausrüstung am Gürtel,
  keine Überwachungsmonitore mit erkennbaren Personen.
- **B19/B21:** Container und Fahrzeuge ohne Beschriftung und ohne Kennzeichen.

## 8 · Vorgehen beim Erzeugen

1. Pro Karte zuerst **Prompt A** mit vier Ergebnissen erzeugen. Ist keines brauchbar, **Prompt B**.
2. Reihenfolge: erst A2–A5 (Startseite), dann ein ganzer Bereich am Stück – so bleibt der Stil gleich.
3. Wenn der Generator Bezugsbilder erlaubt: ein gelungenes Bild als Stilreferenz für die übrigen desselben
   Bereichs mitgeben.
4. Dateiname: `<Nr>-<kurzname>-<a|b>-<laufende Nummer>.jpg`, zum Beispiel `B04-glasreinigung-a-02.jpg`.
5. In der Wagtail-Mediathek den Titel mit `[KI]` beginnen, damit die Bilder später gezielt ersetzt werden
   können.

**Prüfliste vor dem Hochladen** – ein Bild fällt durch, wenn eine Antwort „nein“ lautet:

- Hände, Finger und Werkzeuge anatomisch und technisch richtig?
- Gerät plausibel (Kabel, Schläuche, Räder enden nicht im Nichts)?
- Keine lesbare oder schriftähnliche Fläche, kein Logo, kein Kennzeichen?
- Kein erkennbares Gesicht, auch nicht in Spiegelungen?
- Hauptmotiv im mittleren Drittel, obere linke Ecke ruhig?
- Farbstimmung kühl und hell, passend zu den Nachbarkarten?
- Zeigt das Bild nur, was der Kurztext der Seite auch nennt?

**Wirkung prüfen:** lokal `http://localhost:4321/` (Bereichskarten), die vier Bereichsseiten (Leistungskarten)
und je eine Leistungsseite öffnen, jeweils auch in Handybreite. Die Karten eines Bereichs müssen nebeneinander
als Serie wirken und sich trotzdem auf einen Blick unterscheiden.
