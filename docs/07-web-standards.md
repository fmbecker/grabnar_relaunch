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

Lösung nach Guide `accessible-error-announcement`: `aria-invalid="false"` als
Ausgangszustand (nicht weglassen – Firefox und Safari melden ein leeres Pflichtfeld
sonst schon beim Laden als ungültig), `aria-describedby` nur solange der Fehler steht,
`:user-invalid` statt `:invalid` für die Optik, und eine höfliche Live-Region für die
Ansage. Dazu Fokusführung beim Absenden.

Aufwand: ca. 45 Minuten mit Test.

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

Lösung: zwei getrennte Rendition-Sätze im CMS mit je einheitlichem Seitenverhältnis
(4:3 für Karten, 2:1 für Bühnen) und `Picture.astro` baut das `srcset` nur noch aus
dem passenden Satz.

Aufwand: ca. 30 Minuten, betrifft `cms/blocks/images.py` und alle `<Picture>`-Aufrufe.

## Kleinigkeiten

1. **`<meta charset>` nicht an erster Stelle** – `src/layouts/Base.astro:47-48`: der
   `<link rel="preload">` für die Schrift steht davor. Innerhalb der ersten 1024 Byte
   und damit nicht kaputt, aber die Zeichensatzangabe gehört an den Anfang des `<head>`.
2. **Stellenfilter nicht verlinkbar** – `src/components/islands/JobFilter.tsx`: der
   Filterstand steht nicht in der URL, also kein Zurück-Button und kein teilbarer Link
   auf eine Auswahl. Dazu empfiehlt der Guide `forms` ein `<search>`-Element um
   Filtersteuerungen und sichtbare Labels statt `aria-label` an den beiden `<select>`.
3. **FAQ als Exklusiv-Akkordeon** – `src/components/blocks/Faq.astro:11`: `<details
   name="faq">` lässt den Browser immer nur einen Punkt offen halten, ohne JavaScript.
   Hier ist `<details>` richtig (Inhalt aufklappen, keine Navigation), anders als in
   Befund 3.
4. **Reduced-Motion-Reset mit `*` und `!important`** – `src/styles/global.css:81-85`:
   die harte alte Variante. Moderner wäre `motion-reduce:`-Utilities dort, wo tatsächlich
   animiert wird; `src/components/blocks/ServiceGrid.astro:33` macht es schon so.
   Kosmetisch, kein Fehler.

## Reihenfolge

- [x] 🤖 Befund 1 – `scroll-padding-top`
- [x] 🤖 Befund 3 – mobiles Menü als Popover + Polyfill
- [ ] 🤖 Befund 2 – Formularfehler barrierefrei melden
- [ ] 🤖 Befund 4 – Renditions nach Seitenverhältnis trennen
- [ ] 🤖 Kleinigkeiten 1–4
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

**Nicht abgedeckt:** Escape, Klick-daneben und das Aufklappen der Kategorien. axe
prüft die Seite im Ruhezustand und öffnet das Menü nicht. Escape und Klick-daneben sind
bei `popover="auto"` Browserverhalten nach Spezifikation; das Aufklappen hängt am Skript
in `Header.astro`. Ein Interaktionstest dafür fehlt dem Projekt noch.

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
