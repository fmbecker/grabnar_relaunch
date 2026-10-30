# 05 – Tracking mit Umami

Stand: 30.10.2026. Umami bleibt das Statistik-Werkzeug (selbst gehostet, ohne Cookies). Das
Frontend ist vollständig vorbereitet; Daten fließen erst, wenn im CMS Script-URL und Website-ID
eingetragen sind.

## Einschalten

Wagtail-Admin → Einstellungen → **Website-Einstellungen** → Abschnitt **Statistik (Umami)**:

| Feld | Wert | Hinweis |
|---|---|---|
| Umami-Script-URL | z. B. `https://www.grabnar.de/stats/script.js` | leer = kein Tracking |
| Umami-Website-ID | UUID aus Umami → Einstellungen → Websites | |
| Umami-Host-URL | z. B. `https://www.grabnar.de/stats` | nur, wenn Daten an eine andere Adresse gehen als das Script |
| Nur auf diesen Domains zählen | `www.grabnar.de,grabnar.de` (Vorgabe) | Staging, Vorschau und lokale Builds zählen dadurch nicht mit |
| Ladezeiten (Web Vitals) erfassen | an | `data-performance`, ab Umami 3.1 |
| „Do Not Track“ respektieren | an | `data-do-not-track` |

Nach dem Speichern baut die Seite automatisch neu (Rebuild-Hook). Code: `cms/site_settings/models.py`
(`SiteSettings.analytics_api`), `web/src/components/Analytics.astro`, `web/src/layouts/Base.astro`.

Immer gesetzt: `data-exclude-hash="true"` (Sprungmarken wie `#formular` sind keine eigenen Seiten).
Nie geladen wird das Script in der Redakteurs-Vorschau (`/preview/`).

## Seitenaufrufe

Zählt Umami automatisch für jede Seite, inklusive Herkunft (Referrer) und UTM-Parameter.

## Ereignisse

Zentral definiert in `web/src/lib/analytics.ts` (`EVENT`). Keine personenbezogenen Daten: nie
Namen, E-Mail-Adressen, Telefonnummern oder Formulartexte – nur Seiten-, Leistungs- und Stellentitel.

| Ereignis | Wann | Eigenschaften | Wo im Code |
|---|---|---|---|
| `cta-click` | Klick auf einen Aktions-Button | `block` (hero, cta, text-image), `label`, `target` | `ui/LinkButton.astro` |
| `phone-click` | Klick auf eine Telefonnummer | `placement` (header, mobile-menu, footer, job-sidebar, content) | automatisch, `Analytics.astro` |
| `email-click` | Klick auf eine E-Mail-Adresse | `placement` | automatisch |
| `category-click` | Kachel einer Leistungskategorie | `category`, `target` (overview, service), `service` | `blocks/ServiceGrid.astro` |
| `service-click` | Karte einer Leistung | `service`, `list` (category, related, manual) | `blocks/ServiceGrid.astro` |
| `nav-click` | Menüpunkt | `item`, `parent`, `level`, `menu` (desktop, mobile, footer, header) | `Header.astro`, `Footer.astro` |
| `mobile-menu-open` | Mobiles Menü geöffnet | – | `Header.astro` |
| `faq-open` | FAQ-Frage aufgeklappt | `question` | `blocks/Faq.astro` |
| `gallery-open` | Galeriebild geöffnet | `image` | `blocks/Gallery.astro` |
| `outbound-click` | Link auf eine andere Website (auch im Fließtext) | `url` (ohne Parameter), `placement` | automatisch |
| `download-click` | Dokument-Download (PDF, Word, Excel …) | `file`, `placement` | automatisch |
| `form-start` | Erste Eingabe in ein Formular | `form` (contact, application), `job` | `islands/ContactForm.tsx` |
| `form-submit` | Formular abgeschickt | `form`, `job`, `result` (success, invalid, error), `fields` (nur Namen fehlerhafter Felder) | `islands/ContactForm.tsx` |
| `job-filter` | Filter in der Stellenliste | `field`, `value` | `islands/JobFilter.tsx` |
| `job-open` | Stelle aus der Liste geöffnet | `job` | `blocks/JobList.astro`, `islands/JobFilter.tsx` |
| `job-apply-click` | „Jetzt bewerben“ auf einer Stellenseite | `job` | `PageContent.astro` |
| `page-not-found` | 404-Seite angezeigt | `path`, `referrer` (nur Hostname) | `pages/404.astro` |

Neue interaktive Elemente: Ereignis in `EVENT` ergänzen, an Links/Buttons `{...umami(EVENT.x, {...})}`
setzen, in Islands `track(EVENT.x, {...})` aufrufen, Tabelle oben ergänzen.

Geprüft am 30.10.2026 mit einem Test-Tracker im Browser (Playwright): alle Ereignisse oben außer
`faq-open`, `gallery-open` und `download-click` (auf der Seite derzeit kein FAQ, keine Galerie,
kein Dokument), `job-apply-click` (gleiche Technik wie `job-open`).

## Auswertung in Umami (Vorschlag)

- **Ziele:** `form-submit` mit `result = success` (Anfragen/Bewerbungen), `phone-click`, `email-click`.
- **Trichter Anfrage:** Leistungsseite → `cta-click` → `/kontakt/` → `form-start` → `form-submit` (success).
- **Trichter Bewerbung:** `/karriere/` → `job-open` → `job-apply-click` → `form-submit` (application, success).
- **Weiterleitungen prüfen:** `page-not-found` nach `path` gruppieren und fehlende Redirects nachtragen.

## Umami auf die neueste Version bringen

Neueste Version laut GitHub: **v3.4.0** (17.09.2026). Die Tracker-Attribute oben gibt es alle seit
spätestens 3.1; die Website selbst hängt also nicht an einer bestimmten Unterversion.

Vor dem Update auf v3 beachten:

1. **v3 unterstützt nur noch PostgreSQL.** Läuft die Instanz unter `/home/umami` mit MySQL, zuerst
   nach der offiziellen Anleitung „Migrate MySQL to PostgreSQL“ umziehen. Im Forum wird Postgres 15
   empfohlen (mit 18 schlug `check-db` bei einem Nutzer fehl).
2. **Docker-Tags ohne „v“:** z. B. `ghcr.io/umami-software/umami:3.4.0` bzw. `postgresql-3.4.0` –
   Tag vor dem Update in der Registry prüfen.
3. Vorher Backup der Datenbank; Migrationen laufen beim Start automatisch.
4. Seit 3.4: Der eingebaute `/mcp`-Endpunkt ist standardmäßig aus; Anmeldungen sind an das Passwort
   gebunden (nach dem Update ggf. neu anmelden).
5. Nach dem Update: Website-ID in Umami nachsehen und im CMS eintragen, optional die
   Nginx-Locations `/stats/…` in `deploy/nginx/grabnar.conf` einkommentieren.

## Datenschutz

Umami setzt keine Cookies und speichert keine IP-Adressen. Die Datenschutzerklärung muss Umami
trotzdem nennen (Zweck, selbst gehostet, keine Weitergabe) – Teil der rechtlichen Prüfung in
`docs/04-aufgaben.md`.

Quellen: [Umami Tracker-Konfiguration](https://docs.umami.is/docs/tracker-configuration),
[Ereignisse](https://docs.umami.is/docs/track-events),
[Tracker-Funktionen](https://docs.umami.is/docs/tracker-functions),
[Release v3.4.0](https://github.com/umami-software/umami/releases/tag/v3.4.0),
[v3.0.0 – Umstieg](https://github.com/umami-software/umami/discussions/3685).
