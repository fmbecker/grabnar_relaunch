# 01 – Ist-Analyse der bestehenden Seite (grabnar.de)

Stand: 2026-10-26. Quelle: Datenbank-Export der Live-Instanz (`manage.py shell`, nur Seiten und Bildmetadaten), `pip freeze` und Prozessliste auf dem Linode. Texte aller Seiten liegen in `docs/content-export/`.

## Unternehmen (aus den strukturierten Daten der Startseite und dem Impressum)

- **M. B. Grabnar Gebäudereinigungs- und Handwerker-Service GmbH** (kurz: M. B. Grabnar GmbH)
- Julius-Hölder-Straße 4, 70597 Stuttgart, Baden-Württemberg
- Telefon +49 (0) 711 2 36 33 30, Fax +49 (0) 711 2 36 33 31, E-Mail info@grabnar.de
- Öffnungszeiten: Mo–Fr 08:00–17:00
- Meisterbetrieb (Meister des Gebäudereinigungshandwerks), zertifiziertes Qualitätsmanagement lt. Leistungstexten
- Leitgedanke auf der Startseite: „Zusammenkommen ist der Anfang – Zusammenarbeiten ist der Erfolg“

## Technik der Altseite

| Punkt | Befund |
|---|---|
| CMS | Wagtail **2.14.2** + coderedcms **0.22.3** (Stand 2021) |
| Framework | Django **3.2.25**, Python **3.8** (beide End-of-Life) |
| Datenbank | **MySQL** (`django.db.backends.mysql`). Die Datei `/home/mbgsite/db.sqlite3` ist ein Überbleibsel und wird nicht genutzt. |
| Weitere Pakete | wagtail-cache, wagtail-seo, wagtail-import-export, django-bootstrap4, wagtailfontawesome, django-sendmail-backend |
| Projektpfad | `/home/mbgsite/` (Django-Projekt `mbgsite`, Settings `mbgsite.settings.prod`) |
| Virtualenv | `/home/env/` (weitere: `/home/env25/`, `/home/envcrx/`) |
| App-Server | gunicorn, 3 Worker, als **root**, Unix-Socket `/home/mbgsite/app.sock` |
| Webserver | Nginx (`/etc/nginx/sites-available/`), liefert `robots.txt` nicht selbst aus (kommt aus Django) |
| Weitere Dienste in `/home` | `umami/` (⬜ läuft dort Umami-Analytics?), `csite/`, `bak.coderedcms.conf` |
| Kanonische Domain | **`grabnar.de` ohne www** (Wagtail-Site-Hostname, alle Seiten-URLs) |
| robots.txt | erlaubt alles außer `/admin/` und `/django-admin/`; drei doppelte `User-agent: *`-Gruppen ohne Leerzeilen, relative Sitemap-URL (`/sitemap.xml`). Funktioniert für Google, ist aber formal unsauber. |

**Sicherheitsrelevant:** gunicorn läuft als root, Python 3.8 und Django 3.2 bekommen keine Sicherheitsupdates mehr. Ein weiterer Grund, den Relaunch nicht zu verschleppen.

## Formulare

| Seite | Felder | Empfänger | Speichern |
|---|---|---|---|
| `/kontakt/` (FormPage) | Ihr Name*, Ihre Email*, Ihre Nachricht* | **`mail@aivii.de`** | ja |
| `/kontaktformular/form/` (FormPage, Duplikat) | dieselben | **`mail@aivii.de`** | ja |

⚠️ **Anfragen gehen an `mail@aivii.de`, nicht an eine Grabnar-Adresse.** ⬜ Felix: klären, ob diese Adresse gewollt ist und tatsächlich gelesen wird. Im neuen CMS ist der Empfänger `FORMS_NOTIFY_EMAIL` in `cms.env`.

Danach Weiterleitung auf `/danke/`. Es gibt **kein Bewerbungsformular**; die Seite `/stellenangebote/` ist leer (nur Hero). Stellen werden aktuell nur extern (StepStone u. a.) ausgeschrieben.

## Seitenbaum (live, unter Seite 37 „Home“)

```
/                                         Home
/Gebäudereinigung/                        Kategorie (9 Leistungen)
  Baureinigung, Containerreinigung, Desinfektion (nach IfSG §17/3), Glasreinigung
  (Glas- und Fassadenreinigung), Grundreinigung, Industriereinigung (Hallen- und
  Industriereinigung), Sonderreinigung, Polsterreinigung (Teppich- und Polsterreinigung),
  Unterhaltsreinigung
/gebäudedienste/                          Kategorie (3)
  Grünanlagenpflege (Grau- und Grünanlagenpflege), Hausmeisterdienste, Winterdienst
/handwerkerdienste/                       Kategorie (6)
  Bauhilfsarbeiten, Bodenverlegerarbeiten, Fliesenlegerarbeiten, Malerarbeiten
  (Maler- und Maurerarbeiten), Trockenbau, Bodenversiegelung
/services/                                Kategorie (4)
  Entrümpelung, Arbeitnehmerüberlassung, Transportarbeiten, Wachdienste (Wach- und Schließdienste)
/kontakt/                                 Kontaktformular
/kontaktformular/  + /form/               doppeltes Kontaktformular (Altlast)
/impressum/  /datenschutz/  /agb/         Rechtliches (AGB: ~940 Wörter, Datenschutz: ~3.000 Wörter)
/danke/                                   Danke-Seite nach Formularversand
/stellenangebote/                         leer
```

Zusätzlich im CMS, aber nicht erreichbar: ein vollständiger alter Baum unter „Home -alt“ (Seiten 3–35, 92) und eine Seite „cards“. Nicht migrieren.

Auffällig: URLs mischen Groß-/Kleinschreibung und Umlaute (`/Gebäudereinigung/Baureinigung/`, `/gebäudedienste/`). Neue URLs werden durchgängig klein und ohne Umlaute geschrieben; alle 28 betroffenen URLs bekommen 301-Redirects → `docs/redirects.csv`.

## Inhalte

- 36 Seiten exportiert, Texte als Markdown in `docs/content-export/` (Übersicht: `docs/content-export/README.md`).
- Leistungsseiten haben jeweils 60–170 Wörter Einleitung plus eine Aufzählung „Unsere Dienstleistungen im Einzelnen“. Kategorieseiten haben nur 30–80 Wörter.
- Inhalt liegt fast komplett in rohen HTML-Blöcken des CodeRed-Layouts (274 HTML-Blöcke, 195 Rows), `<h4>` wird als Fließtext missbraucht.
- Jede Seite enthält einen „Reusable Content“-Block (vermutlich Header/Logo-Leiste), der nicht im Export ist.
- 135 Bilder in der Mediathek, überwiegend **Unsplash-Stockfotos** (Dateinamen wie `priscilla-du-preez-…-unsplash.jpg`). Für den Relaunch eigene Fotos von Team und Objekten bevorzugen. ⬜ Logo: Bild-ID 118 (Dateiname siehe Export) vom Server holen.

## SEO

- Startseite: Titel „M.B. Grabnar GmbH Gebäudereinigungs und Handwerkerservice“, Description vorhanden.
- Unterseiten: **keine** eigenen SEO-Titel oder Descriptions (Ausnahme Kontakt). Im Relaunch für alle Leistungsseiten ergänzen.
- ⬜ Google Search Console: Property für `grabnar.de` vorhanden? Zugang klären.

## Noch offen (👤 Felix)

- ⬜ Empfängeradresse `mail@aivii.de` klären
- ⬜ Läuft Umami unter `/home/umami`? Wenn ja: Script-URL und Site-ID für die Website-Einstellungen im neuen CMS
- ⬜ Linode: OS-Version, RAM/Disk, Docker installiert?, certbot-Status (`cat /etc/os-release; free -h; df -h /; docker --version; certbot certificates`)
- ⬜ Mailversand: Welcher SMTP-Weg wird heute genutzt (`django-sendmail-backend` → lokales sendmail/Postfix?)
- ⬜ Logo-Datei und Firmenfarben
