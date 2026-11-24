# 07 – Web-Standards: Prüfung und Plan

Prüfung des Frontends (`web/`) auf veraltete Muster und auf heutige Web-Standards,
Stand **24.11.2026**, Branch `modern-web-guidance`.

Grundlage: der Skill `modern-web-guidance` (Guides `forms`, `accessible-error-announcement`,
`navbar`, `performance`, `optimize-image-priority`) und ein Durchlauf von `legacy-scan`.

Legende wie in `docs/04-aufgaben.md`: 🤖 = Claude, 👤 = Felix, 🤝 = gemeinsam.

## Ergebnis in einem Satz

Keine Altlasten – aber vier echte Mängel, von denen zwei (Anker hinter dem Header,
Formularfehler ohne ARIA-Bezug) direkt den Weg zur Anfrage bzw. Bewerbung treffen.

## Was geprüft wurde

- `legacy-scan` über `web/src`: 43 Dateien, 38 Guides, 52 Regeln → **0 Treffer**.
- Grep nach `innerHTML`, `document.write`, `XMLHttpRequest`, `var`, `float:`,
  Vendor-Prefixes, Clearfix, `!important` → nichts außer dem Reduced-Motion-Reset
  (siehe Kleinigkeit 4).
- Versionsstand: Astro 7, Tailwind 4 (`@theme`, kein Config-File), React 19, Node 22,
  Wagtail 7.4 LTS, Django 5.2 – alles aktuell.

Was bereits dem heutigen Stand entspricht und so bleiben soll:

- CSP als `<meta>` mit Hashes für eigene Inline-Skripte (`astro.config.ts`, `src/lib/csp.ts`),
  Sicherheits-Header in `deploy/nginx/security-headers.conf`.
- Zwei-Klick-Lösung für das Bewerberportal über `<template>` (`blocks/JobEmbed.astro`).
- Leaflet erst beim Hereinscrollen per `IntersectionObserver`, Tiles über den eigenen
  Proxy (`blocks/Map.astro`).
- WebP-Renditions mit `srcset`/`sizes`/`fetchpriority`/`decoding` (`ui/Picture.astro`,
  `cms/blocks/images.py`).
- Flüssige Typo über `clamp()`, sichtbare `:focus-visible`-Ringe, `prefers-reduced-motion`.
- Lighthouse- und axe-Prüfung als Skript (`web/scripts/audit.mjs`).

## Befunde

### 1. Anker landen hinter dem Sticky-Header 🤖

`src/styles/global.css` setzt `scroll-behavior: smooth`, aber kein `scroll-padding-top`.
Der Header ist auf allen Breiten `sticky top-0` und `h-20` (5rem) hoch.

Folge: Der Button „Jetzt bewerben" auf den Stellenseiten
(`src/components/PageContent.astro:112`, `href="#formular"`) scrollt die Überschrift des
Formulars unter den Header. Betrifft jeden künftigen Anker in redaktionellen Texten
genauso.

Lösung: `html { scroll-padding-top: 5.5rem; }`. Eine Zeile.

**Status: erledigt (siehe unten).**

### 2. Formularfehler ohne programmatischen Bezug 🤖

`src/components/islands/ContactForm.tsx` rendert die Fehler des Servers als freie
Absätze (Zeilen 90, 124, 133). Es fehlen:

- `aria-invalid` auf dem betroffenen Feld,
- `aria-describedby` vom Feld auf die Fehlermeldung,
- Fokus auf das erste fehlerhafte Feld nach einem abgelehnten Absenden,
- Fokus auf die Erfolgsmeldung (`role="status"`, Zeile 75), die das Formular ersetzt –
  der Fokus landet derzeit im Nichts.

Folge: Wer mit Screenreader bedient, erfährt nicht, welches Feld beanstandet wurde.
WCAG 2.1 AA, Kriterien 3.3.1 (Fehlererkennung) und 3.3.3 (Fehlerempfehlung).
Betrifft Kontaktanfrage **und** Initiativbewerbung.

`axe-core` meldet das nicht: der Fehlertext ist gültiges HTML, er ist nur mit keinem
Feld verknüpft.

Umgesetzt nach Guide `accessible-error-announcement` am 24.11.2026:

- `aria-invalid` steht immer am Feld, `"false"` als Ausgangszustand. Weglassen wäre
  falsch in beide Richtungen: Firefox und Safari melden ein leeres Pflichtfeld schon beim
  Laden als ungültig, Chromium umgekehrt auch nach der Eingabe nicht, solange das
  Attribut fehlt.
- `aria-describedby` zeigt nur auf die Meldung, solange sie sichtbar ist. Text, auf den
  `aria-describedby` zeigt, wird auch im versteckten Zustand vorgelesen – deshalb steht
  der Bezug nicht fest im Markup.
- Der Browser-Zustand `:user-invalid` wird auf `blur`, `input` und `invalid` nach
  `aria-invalid` gespiegelt. Fehlt die Pseudoklasse (vor Nov 2023), entfällt nur diese
  Spiegelung; die Server-Fehler bleiben vollständig verknüpft.
- Nach einer Ablehnung springt der Fokus ins erste abgelehnte Feld, damit der Screenreader
  Feldname und Meldung liest. Das ersetzt eine Live-Region für die Feldfehler. Schlüssel
  ohne eigenes Feld (`source_path`, `job_page_id`, `non_field_errors` aus
  `cms/forms_api/views.py`) landen auf der allgemeinen Meldung, die dafür nie `hidden`
  sein darf – ein verstecktes Element kann keinen Fokus bekommen.
- Nach dem Senden bekommt die Erfolgsmeldung den Fokus. Vorher verschwand der
  Absende-Button mit dem Formular und der Fokus fiel aufs Dokument (WCAG 2.4.3).
- Tippen löscht die Server-Meldung des Feldes sofort; während des Tippens wird nichts
  geprüft.
- `global.css`: `.field:is(:user-invalid, [aria-invalid="true"])` bekommt einen roten
  Rand. Beide Selektoren in einem `:is()`, sonst verwirft ein Browser ohne
  `:user-invalid` die ganze Regel. Die Farbe ist nie der einzige Hinweis.

Nebenbei sind die zwei `FormEvent`-Hinweise aus `pnpm check` verschwunden: der Typ ist in
den React-19-Typen als „doesn't actually exist" abgekündigt, jetzt `SyntheticEvent`.

**Status: erledigt (siehe unten).**

### 3. Mobiles Menü ohne Escape und ohne Klick daneben 🤖

`src/components/Header.astro:51-71` baut das mobile Menü aus `<details>`/`<summary>`,
die Unterpunkte aus verschachtelten `<details>`. Daraus folgt:

- Escape schließt nicht, ein Klick daneben schließt nicht – `<details>` kennt beides nicht.
- `max-h-[75vh]` (Zeile 53) rechnet mit der statischen Viewporthöhe; auf Mobilgeräten
  verdeckt die Browserleiste den unteren Rand. Richtig ist `dvh`.
- Der Guide `navbar` sagt ausdrücklich, `<summary>` nicht als Auslöser für Navigation
  zu verwenden: die Rollenzuordnung ist in den Browsern uneinheitlich umgesetzt,
  Screenreader sagen „Summary" oder „Aufklappdreieck" statt „Schaltfläche".

Lösung nach Guide `navbar`: die Liste als `popover="auto"`, der Auslöser als
`<button popovertarget>`. Light-Dismiss, Escape und Fokusrückgabe kommen dann vom
Browser, ohne eigene Handler. Positionierung mit `anchor()` und einer davor
geschriebenen Absolut-Angabe als Rückfall. Unterpunkte als `<button aria-expanded>`
plus `hidden`-Liste.

Popover ist erst seit 27.01.2025 Baseline („newly available", iOS Safari ab 18.3).
**Entscheidung Felix, 24.11.2026: Popover mit Polyfill.** `@oddbird/popover-polyfill`
(0.7.3, MIT) wird per `import()` nur dort nachgeladen, wo `HTMLElement.prototype` die
Eigenschaft `popover` nicht kennt – als eigener Chunk unter `_astro/`, also weiterhin
`script-src 'self'`, keine CSP-Änderung.

Keine Anker-Positionierung: der Header ist auf allen Breiten `sticky` und `h-20` (5rem),
damit ist ein fester Versatz exakt und `anchor()` (Baseline erst 13.01.2026) unnötig.

Nebenwirkung, mit erledigt: das Ereignis `mobile-menu-open` wurde in
`src/components/Analytics.astro` über `toggle` + `instanceof HTMLDetailsElement` gezählt.
Der Listener nimmt jetzt auch den `ToggleEvent` eines Popovers (`newState === "open"`),
sonst wäre die Zählung still ausgefallen.

**Status: erledigt (siehe unten).**

### 4. Ein `srcset` mit drei Seitenverhältnissen 🤖

`src/components/ui/Picture.astro:14` baut das `srcset` aus allen vier Renditions,
die `cms/blocks/images.py` liefert – die haben aber verschiedene Seitenverhältnisse:
`thumb` 400×300 und `card` 800×600 sind 4:3, `wide` 1600×900 ist 16:9, `hero` 2000×1000
ist 2:1. `width`/`height` am `<img>` kommen immer nur von der gewählten `variant`.

Folge: Welchen Bildausschnitt man sieht, hängt von Pixeldichte und Viewport ab –
dasselbe Bild ist auf einem Retina-Display anders beschnitten als auf einem normalen.
Kein Layoutsprung, weil überall eine `aspect-[…]`-Klasse mit `object-cover` daneben
steht; die Klasse verdeckt den Fehler nur.

Umgesetzt am 24.11.2026: zwei Sätze in `cms/blocks/images.py` (`RENDITION_SETS`), jeder mit
genau einem Seitenverhältnis, dazu `full` außerhalb beider Sätze.

| Satz | Verhältnis | Breiten | Wofür |
|---|---|---|---|
| `card` | 4:3 | 400, 800, 1200, 1600 | Bilder in einer Box im Fluss |
| `stage` | 2:1 | 800, 1200, 1600, 2000 | Flächen, die ein Bild bedeckt |
| `full` | Original | 1600 | Galeriebild einzeln öffnen, nie im `srcset` |

`Picture.astro` nimmt statt `variant` jetzt `shape` (`card`/`stage`) und baut das `srcset`
nur aus dem gewählten Satz; alle sieben Aufrufstellen sind umgestellt. Das CSS-Verhältnis
der Box darf abweichen – `object-cover` beschneidet dann jeden Kandidaten gleich.

Eine gewollte Sichtänderung: `blocks/ServiceGrid.astro:33` zog das 16:9-Bild in eine
`aspect-[4/3]`-Box und bekommt jetzt den 4:3-Satz. Dort ist mehr Bildhöhe zu sehen.

`Seo.astro` nahm `renditions.wide` für `og:image` und holt es jetzt aus dem `stage`-Satz,
nach Breite ausgewählt (≥ 1200) statt nach Index – ein Umsortieren des Satzes kann das
OG-Bild so nicht still verändern.

Zwei Dinge, die erst der Build gezeigt hat:

1. **Wagtail skaliert nicht hoch.** Beim 1408 px breiten Platzhalter liefern
   `fill-1600x800` und `fill-2000x1000` dieselben Pixelmaße, also stand zweimal `1408w`
   im `srcset` und der Browser hätte zwischen zwei identischen Dateien gewählt.
   `Picture.astro` behält darum den ersten Kandidaten je Breite.
2. **Der Zuschnitt übersteht das Begrenzen** – nachgemessen, nicht angenommen: `fill`
   beschneidet zuerst auf das Verhältnis und verkleinert dann, also halten auch die
   begrenzten Varianten ihr Verhältnis (1334×1000 = 1,334, Rundung auf ganze Pixel).
   Deshalb prüft der Test mit `round(..., 2)`.

Zwei neue Tests halten den Vertrag fest:
`test_rendition_sets_have_one_aspect_ratio_each` direkt an `RENDITION_SETS`,
`test_image_api_serialises_both_sets` an der echten API-Antwort.

Kosten: 9 Renditions je Bild statt 5. Wagtail speichert sie nach dem ersten Build, nur
neu hochgeladene Bilder kosten etwas.

**Status: erledigt. Geprüft:** 27 pytest-Tests, `pnpm lint`/`check` sauber (0 Hinweise),
Audit unverändert 100/100/100/100 und 0 axe-Verstöße auf allen sieben Seiten, CLS 0.

## Kleinigkeiten

Alle vier am 24.11.2026 umgesetzt.

1. **`<meta charset>` nicht an erster Stelle** – `src/layouts/Base.astro`: der
   `<link rel="preload">` für die Schrift stand davor. Innerhalb der ersten 1024 Byte und
   damit nicht kaputt, aber die Zeichensatzangabe gehört an den Anfang des `<head>`.
   Jetzt `charset`, `viewport`, dann der Preload.
2. **Stellenfilter nicht verlinkbar** – `src/components/islands/JobFilter.tsx`: der
   Filterstand stand nicht in der URL. Jetzt in `?ort=`/`?art=` per `pushState`, dazu
   `popstate` für den Zurück-Button. Die Seite ist statisch, die URL also erst im Browser
   bekannt: der erste Render ist ungefiltert, danach übernimmt ein Effekt die Auswahl.
   Ein Wert, den keine Stelle hat, wird verworfen, damit ein alter Link nicht eine leere
   Liste zeigt. Dazu nach Guide `forms` ein `<search>`-Element um die Steuerung, sichtbare
   `<label>` statt `aria-label`, und eine `role="status"`-Region mit der Trefferzahl, die
   bis zur ersten Auswahl leer bleibt, damit die Hydration nichts ansagt.
3. **FAQ als Exklusiv-Akkordeon** – `src/components/blocks/Faq.astro`: `<details name>`
   lässt den Browser ohne JavaScript nur einen Punkt offen halten. Der Name muss pro Seite
   eindeutig sein, sonst schließen zwei faq-Blöcke gegenseitig ihre Antworten; er wird
   darum aus dem Inhalt abgeleitet und bleibt über Builds gleich. Browser ohne
   Unterstützung lassen einfach mehrere Antworten offen. Hier ist `<details>` richtig
   (Inhalt aufklappen, keine Navigation), anders als in Befund 3.
4. **Reduced-Motion-Reset mit `*` und `!important`** – `src/styles/global.css`. Beim ersten
   Durchgang hatte ich das als kosmetisch eingeschätzt und vermutet, der globale Reset sei
   die schützendere Variante. Der Guide `motion` sagt das Gegenteil:

   > **DO NOT** globally apply `animation-duration: 0.01ms;` as it can cause certain
   > animations to become _more_ jarring. […] Keep non-motion transitions (such as `color`
   > or `background-color` changes on links and buttons) enabled; only dampen or disable
   > spatial movement, scaling, rotation, or persistent animations.

   Der Reset hat genau diese Farbübergänge mitabgeschaltet. Jetzt wird nur echte
   räumliche Bewegung abgeschaltet: `scroll-behavior: auto` unter
   `prefers-reduced-motion: reduce`, `motion-reduce:transition-none` am FAQ-Plus und am
   Menü-Plus (beide rotieren), und in `blocks/Map.astro` **Leaflet** per
   `matchMedia` (`zoomAnimation`, `fadeAnimation`, `markerZoomAnimation`). Letzteres ist
   der Grund, warum das Entfernen des Resets ohne diesen Schritt eine Verschlechterung
   gewesen wäre: Leaflet baut seine Animationen zur Laufzeit, kein Stylesheet erreicht
   sie. `blocks/ServiceGrid.astro:33` hatte sein `motion-reduce:` schon.
   Farbübergänge an Buttons und das Ein-/Ausblenden der Desktop-Dropdowns bleiben an –
   Opazität ist keine Bewegung.

### Geprüft nach den Kleinigkeiten

`pnpm lint` sauber, `pnpm check` 0/0/0, `pnpm check:tracking` sauber, Audit unverändert
100/100/100/100 und 0 axe-Verstöße auf allen sieben Seiten.

Weder `job_list` noch `faq` kommt im Seed vor – die Stellen liegen bei Europersonal, das
FAQ nutzt bisher keine Seite –, der Build konnte die Kleinigkeiten 2 und 3 also nicht
zeigen. Dafür eine Wegwerf-Seite mit Beispieldaten gerendert, elf Prüfungen im Browser,
alle bestanden, danach Seite gelöscht und neu gebaut:

1. Ohne Auswahl beide Stellen, keine Query, Live-Region leer
2. Auswahl landet als `?ort=…` in der URL, Liste gefiltert, Live-Region meldet „1 von 2"
3. Zweiter Filter kommt als `&art=…` dazu
4. Zurück nimmt den letzten Schritt zurück, und der Select folgt
5. Geteilter Link `?ort=…&art=…` stellt die Auswahl wieder her
6. `?ort=Nirgendwo` wird verworfen statt eine leere Liste zu zeigen
7. FAQ hält nur eine Antwort offen

Das Skript liegt wie das zu Befund 2 noch nicht im Repo.

## Reihenfolge

- [x] 🤖 Befund 1 – `scroll-padding-top`
- [x] 🤖 Befund 3 – mobiles Menü als Popover + Polyfill
- [x] 🤖 Befund 2 – Formularfehler barrierefrei melden
- [x] 🤖 Befund 4 – Renditions nach Seitenverhältnis trennen
- [x] 🤖 Kleinigkeiten 1–4
- [ ] 👤 Entscheiden, ob die zwei Prüfskripte nach `e2e/` kommen (siehe unten)
- [x] 🤖 Lighthouse + axe gegen den Build gelaufen (24.11.2026)

### Geprüft nach Befund 1 und 3

Vollständig, in dieser Reihenfolge, gegen das lokal laufende CMS (sqlite, Port 8000):

| Prüfung | Ergebnis |
|---|---|
| `cms`: `ruff check .` | sauber |
| `cms`: `ruff format --check .` | 47 Dateien formatiert |
| `cms`: `pytest -q` | 25 passed |
| `web`: `pnpm lint` | sauber |
| `web`: `pnpm check` | 0 Fehler, 0 Warnungen, 2 Hinweise |
| `web`: `pnpm check:tracking` | 16 Ereignis-Bezüge, alle in `EVENT` |
| `web`: `pnpm build` | 33 Seiten, `noindex` korrekt gesetzt |
| `scripts/audit.mjs`, 7 Seiten | alle bestanden |

Die zwei Hinweise aus `pnpm check` betreffen das veraltete `FormEvent` in
`islands/ContactForm.tsx` und gehören zu Befund 2.

Audit je Seite: Performance 100, Barrierefreiheit 100, Best Practices 100, SEO 100,
0 axe-Verstöße (WCAG 2.1/2.2 AA, mobil **und** Desktop), CLS 0, LCP mobil 0,9–1,8 s.

Im Build belegt: `scroll-padding-top:5.5rem`, `max-block-size:calc(100dvh - 7rem)`,
`popover="auto"` samt `popovertarget`, der `@supports`-Rückfall mit `.\:popover-open`,
der Polyfill als eigener Chunk, und die Unterlisten ohne `hidden`/`aria-expanded` im
Markup (also ohne JavaScript vollständig lesbar).

### Geprüft nach Befund 2

Der Audit bleibt unverändert bei 100/100/100/100 und 0 axe-Verstößen, auch auf
`/kontakt/`. `pnpm check` meldet jetzt 0 Fehler, 0 Warnungen und **0 Hinweise**.

Weil axe die Seite nur im Ruhezustand prüft und kein Formular abschickt, zusätzlich zehn
Prüfungen im echten Browser (Playwright, Antwort des CMS gestubbt, also nur die Island
im Test) – alle bestanden:

1. Vor der Eingabe `aria-invalid="false"` und kein `aria-describedby`
2. Pflichtfeld angefasst und leer gelassen → `aria-invalid="true"`
3. Nachgetragen → wieder `"false"`
4. Server lehnt ein Feld ab → `aria-invalid="true"`
5. … und `aria-describedby` wird gesetzt
6. … und zeigt auf den tatsächlichen Meldungstext
7. Fokus steht im ersten abgelehnten Feld
8. Tippen löscht die Server-Meldung
9. Nach dem Senden steht der Fokus auf der Erfolgsmeldung (`role="status"`)
10. Vor der Eingabe kein `aria-describedby` am E-Mail-Feld

Das Skript liegt noch nicht im Repo. Es passt nach `e2e/` neben `preview_admin.py`, nur
in Node statt Python, weil `playwright` seit Befund 1/3 als devDependency in `web/`
steht. Beim Übernehmen: der Import muss dann `from "playwright"` lauten, im Scratchpad
bekommt er den Pfad über die Umgebungsvariable `PLAYWRIGHT`.

**Nicht abgedeckt:** Escape, Klick-daneben und das Aufklappen der Kategorien im mobilen
Menü. axe öffnet das Menü nicht. Escape und Klick-daneben sind bei `popover="auto"`
Browserverhalten nach Spezifikation; das Aufklappen hängt am Skript in `Header.astro`.
Diese drei Fälle gehören in dasselbe `e2e/`-Skript.

### Zwei Stolpersteine beim Audit, für den nächsten Durchlauf

1. **SEO fällt scheinbar durch.** Mit der normalen `.env` trägt jede Seite
   `<meta name="robots" content="noindex,nofollow">`, weil `PUBLIC_ALLOW_INDEXING`
   nicht gesetzt ist – Lighthouse gibt dann SEO 69 (`is-crawlable` = 0). Der Audit
   braucht also einen eigenen Build:
   `WAGTAIL_MEDIA_URL= PUBLIC_FORMS_API_URL=/api/forms PUBLIC_ALLOW_INDEXING=true pnpm build`,
   dann `node scripts/serve-prod.mjs --port 8080` und
   `node scripts/audit.mjs --base http://127.0.0.1:8080`.
2. **`ECONNREFUSED 127.0.0.1:8000` heißt nicht, dass das CMS weg ist.**
   Djangos `runserver` hat einen Listen-Backlog von 10; die parallelen API-Abrufe des
   Builds überfahren ihn gelegentlich. Einfach wiederholen.

Lighthouse nennt außerdem vier Punkte unterhalb der Schwelle, die die Kategoriewertung
nicht drücken: `render-blocking-insight` (290 ms, das gebündelte CSS im `<head>`),
`unused-javascript` (37 KiB, nur `/kontakt/`, die React-Island des Formulars),
`cache-insight` (6 KiB, Header von `serve-prod.mjs`, nicht von Nginx) und
`image-delivery-insight` (7 KiB, WebP-Qualität 70). Nichts davon ist zu tun.

## Browser-Unterstützung: offene Festlegung

Für das Projekt ist nirgends festgehalten, welche Browser getragen werden. Der Skill
`modern-web-guidance` nimmt ohne solche Angabe „Baseline widely available" an und
verlangt für alles Neuere einen Rückfall – deshalb die Frage in Befund 3. Eine Zeile in
`CLAUDE.md` würde das künftig entscheiden, zum Beispiel:

> **Browser-Unterstützung:** „newly available"-Funktionen sind erlaubt, wenn der
> Rückfall ohne zusätzliche Abhängigkeit und mit höchstens 20 Zeilen auskommt.
