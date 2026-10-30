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
| `lead` | **Jeder Kontakt** – ein Ziel für „Kontakte gesamt“ | `channel` (form, application, phone, email, phone-copy, email-copy), `service`, `placement` | `Analytics.astro`, `islands/ContactForm.tsx` |
| `cta-click` | Klick auf einen Aktions-Button | `block` (hero, cta, text-image), `label`, `target`, `service` (auf Leistungsseiten) | `ui/LinkButton.astro` |
| `phone-click` | Klick auf eine Telefonnummer | `placement` (header, mobile-menu, footer, job-sidebar, content) | automatisch, `Analytics.astro` |
| `email-click` | Klick auf eine E-Mail-Adresse | `placement` | automatisch |
| `contact-copy` | Telefonnummer oder E-Mail-Adresse der Firma kopiert (am Desktop wird oft abgetippt statt geklickt); je Typ einmal pro Seitenaufruf | `type` (phone, email), `placement` | automatisch |
| `category-click` | Kachel einer Leistungskategorie | `category`, `target` (overview, service), `service` | `blocks/ServiceGrid.astro` |
| `service-click` | Karte einer Leistung | `service`, `list` (category, related, manual) | `blocks/ServiceGrid.astro` |
| `nav-click` | Menüpunkt | `item`, `parent`, `level`, `menu` (desktop, mobile, footer, header) | `Header.astro`, `Footer.astro` |
| `mobile-menu-open` | Mobiles Menü geöffnet | – | `Header.astro` |
| `faq-open` | FAQ-Frage aufgeklappt | `question` | `blocks/Faq.astro` |
| `gallery-open` | Galeriebild geöffnet | `image` | `blocks/Gallery.astro` |
| `outbound-click` | Link auf eine andere Website (auch im Fließtext) | `url` (ohne Parameter), `placement` | automatisch |
| `download-click` | Dokument-Download (PDF, Word, Excel …) | `file`, `placement` | automatisch |
| `form-start` | Erste Eingabe in ein Formular | `form` (contact, application), `job` | `islands/ContactForm.tsx` |
| `inquiry-sent` | Kontaktanfrage erfolgreich gesendet | `service` (nur aus dem Link `?leistung=`, nie getippter Text) | `islands/ContactForm.tsx` |
| `application-sent` | Bewerbung erfolgreich gesendet | `job` | `islands/ContactForm.tsx` |
| `form-error` | Senden fehlgeschlagen | `form`, `job`, `reason` (invalid, error), `fields` (nur Namen fehlerhafter Felder) | `islands/ContactForm.tsx` |
| `job-filter` | Filter in der Stellenliste | `field`, `value` | `islands/JobFilter.tsx` |
| `job-open` | Stelle aus der Liste geöffnet | `job` | `blocks/JobList.astro`, `islands/JobFilter.tsx` |
| `job-apply-click` | „Jetzt bewerben“ auf einer Stellenseite | `job` | `PageContent.astro` |
| `page-not-found` | 404-Seite angezeigt | `path`, `referrer` (nur Hostname) | `pages/404.astro` |

**Leistung bis ins Formular:** Aktions-Buttons auf Leistungsseiten, die auf `/kontakt/` zeigen,
hängen `?leistung=<Leistung>` an (`withService()` in `lib/analytics.ts`, gesetzt in
`ui/LinkButton.astro`). Das Kontaktformular füllt damit „Gewünschte Leistung“ vor, und
`inquiry-sent`/`lead` tragen die Leistung. Gespeichert wird dafür nichts im Browser (kein
localStorage/sessionStorage – das bräuchte nach § 25 TDDDG eine Einwilligung).

Neue interaktive Elemente: Ereignis in `EVENT` ergänzen, an Links/Buttons `{...umami(EVENT.x, {...})}`
setzen, in Islands `track(EVENT.x, {...})` aufrufen, Tabelle oben ergänzen.

Geprüft am 30.10.2026 mit einem Test-Tracker im Browser (Playwright): alle Ereignisse oben außer
`faq-open`, `gallery-open` und `download-click` (auf der Seite derzeit kein FAQ, keine Galerie,
kein Dokument), `job-apply-click` (gleiche Technik wie `job-open`) und `application-sent`
(gleicher Code wie `inquiry-sent`).

## Auswertung in Umami (Vorschlag)

- **Ziele (Goal-Report):** `lead` (Kontakte gesamt), `inquiry-sent` (Anfragen), `application-sent` (Bewerbungen).
- **Funnel „Anfrage“:** Leistungsseite → `cta-click` → `/kontakt/` → `form-start` → `inquiry-sent`.
- **Funnel „Bewerbung“:** `/karriere/` → `job-open` → `job-apply-click` → `application-sent`.
- **Journey-Report:** Ende = `lead` – welche Wege führen tatsächlich zu einem Kontakt.
- **Breakdown:** `lead` nach `channel` und `service`; `inquiry-sent` nach `service` (welche Leistung bringt Anfragen).
- **Filter:** Für Kundenkennzahlen `/karriere/` ausschließen, sonst zählen Bewerber mit.
- **Weiterleitungen prüfen (monatlich):** `page-not-found` nach `path` gruppieren und fehlende Redirects nachtragen.

Grenzen: Ohne Cookie gilt ein Weg nur innerhalb eines Besuchs (wer am nächsten Tag anfragt, erscheint
als neuer Besuch). Anrufe selbst sind nicht messbar, nur Klick oder Kopieren der Nummer. Suchbegriffe
liefert nur die Google Search Console.

## Ziele, Funnels und Segmente per Skript einspielen

Die Definitionen liegen versioniert in **`deploy/umami/reports.json`** und werden mit
**`deploy/umami/setup-reports.mjs`** über die Umami-API (ab 3.4) angelegt. Abgleich über den Namen:
Fehlendes wird angelegt, Vorhandenes aktualisiert, nichts gelöscht – in der Oberfläche ergänzte
Einträge bleiben erhalten. Nach Änderungen an `reports.json` einfach erneut ausführen.

Inhalt:
- **5 Ziele:** Kontakte gesamt (`lead`), Anfragen (`inquiry-sent`), Bewerbungen (`application-sent`),
  Anrufe (`phone-click`), Kontaktseite besucht (`/kontakt/`)
- **7 Funnels** (Zeitfenster 60 Minuten): Anfrage (Button → `/kontakt/` → `form-start` → `inquiry-sent`),
  Bewerbung (`/karriere/` → `job-open` → `job-apply-click` → `application-sent`),
  Startseite → Kategorie → Kontakt, und je Leistungskategorie `/<kategorie>/*` → `lead`
- **4 Segmente:** Kunden (ohne Karriere), Bewerber (Karriere), Mobil, Desktop

Ausführen (auf dem Server, Umami lauscht auf `127.0.0.1:3000`):

1. Umami → Einstellungen → **API-Schlüssel** → neuen Schlüssel anlegen (beginnt mit `umami_`).
2. Website-ID: Umami → Einstellungen → Websites → www.grabnar.de.
3. Probelauf, dann echt:

       cd /srv/grabnar/repo
       export UMAMI_URL=http://127.0.0.1:3000 UMAMI_API_KEY=umami_… UMAMI_WEBSITE_ID=<uuid>
       node deploy/umami/setup-reports.mjs --dry-run
       node deploy/umami/setup-reports.mjs

Nicht per API möglich (Umami 3.4 hat dafür keine Definitions-Endpunkte), daher einmal in der
Oberfläche: **Journey** (Website → Journey, 5 Schritte, Ende = Ereignis `lead`) sowie bei Bedarf
**Retention**, **Attribution** und **UTM** – diese Berichte brauchen keine Definition, nur den Zeitraum.

`pnpm check:tracking` (in CI und im Pre-Push-Hook) prüft, dass jedes in `reports.json` verwendete
Ereignis in `web/src/lib/analytics.ts` existiert. Wer ein Ereignis umbenennt, muss also beide Stellen
anpassen.

Geprüft: `reports.json` gegen die Eingabe-Schemas aus dem Umami-Quellcode v3.4.0 (alle 16 Einträge
gültig), das Skript gegen eine nachgebaute API (Anlegen, Aktualisieren, Probelauf). Gegen eine echte
Umami-Instanz noch nicht ausgeführt.

## Monatsbericht per E-Mail

Am 1. jedes Monats um 07:15 Uhr verschickt der Server einen Bericht über den Vormonat (Vergleich mit
dem Monat davor) – über dieselbe SMTP-Konfiguration wie die Formulare (`EMAIL_URL` in `cms.env`).

Inhalt: automatische Hinweise („Auf einen Blick“: starke Veränderungen bei Kontakten und Besuchern,
größter Absprung im Anfrage-Weg, neue 404-Adressen, häufigste Leistung), Besucherkennzahlen mit
Vormonat, alle Ziele aus `reports.json` mit Anteil und Vormonat, Kontakte nach Weg und nach Leistung,
Anfrage-Funnel Schritt für Schritt, meistbesuchte Seiten, Herkunft, Kanäle, Geräte, UTM-Kampagnen
und nicht gefundene Adressen. Nur Summen, keine Einzelbesuche.

| Datei | Aufgabe |
|---|---|
| `deploy/umami/monthly-report.mjs` | holt die Zahlen über die Umami-API und baut die HTML-Mail (`--month=JJJJ-MM`, `--out=…`, `--demo` für eine Vorschau ohne Umami) |
| `deploy/umami/send-monthly-report.sh` | erzeugt den Bericht und verschickt ihn über `manage.py send_report_mail` im CMS-Container |
| `deploy/umami/umami-report.env.example` | Vorlage für `/srv/grabnar/umami-report.env` (Umami-URL, API-Schlüssel, Website-ID, Empfänger) |
| `deploy/systemd/grabnar-umami-report.{service,timer}` | Zeitplan |

Einrichten (nach dem Umami-Update und `setup-reports.mjs`):

    cp deploy/umami/umami-report.env.example /srv/grabnar/umami-report.env && chmod 600 /srv/grabnar/umami-report.env
    # Werte eintragen, dann einmal von Hand testen:
    deploy/umami/send-monthly-report.sh
    sudo cp deploy/systemd/grabnar-umami-report.* /etc/systemd/system/
    sudo systemctl daemon-reload && sudo systemctl enable --now grabnar-umami-report.timer

Vorschau des Layouts ohne Umami: `node deploy/umami/monthly-report.mjs --demo --out=/tmp/bericht.html`.

Geprüft: Monatsgrenzen in Europe/Berlin (inkl. Sommerzeitwechsel), Abruf aller 13 Endpunkte gegen
eine nachgebaute Umami-API, Versand über `send_report_mail` (Test in `cms/grabnar/tests/test_api.py`).
Gegen eine echte Umami-Instanz noch nicht ausgeführt.

## Kampagnen-Links (UTM)

Für Werbung außerhalb der Website immer diese Links verwenden; der UTM-Report in Umami zeigt dann,
was davon Besucher und Kontakte bringt:

| Wo | Link |
|---|---|
| Google-Unternehmensprofil | `https://www.grabnar.de/?utm_source=google&utm_medium=unternehmensprofil` |
| QR-Code Fahrzeuge | `https://www.grabnar.de/?utm_source=fahrzeug&utm_medium=qr` |
| QR-Code Flyer | `https://www.grabnar.de/?utm_source=flyer&utm_medium=qr&utm_campaign=<Aktion>` |
| E-Mail-Signatur | `https://www.grabnar.de/?utm_source=email&utm_medium=signatur` |
| Rechnungen/Angebote | `https://www.grabnar.de/?utm_source=dokument&utm_medium=qr` |

## Eigene Besuche nicht zählen

Auf Firmenrechnern und eigenen Handys einmal in der Browser-Konsole (F12 → Konsole) auf
www.grabnar.de eingeben: `localStorage.setItem("umami.disabled", 1)`. Rückgängig mit
`localStorage.removeItem("umami.disabled")`. Gilt pro Browser.

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
