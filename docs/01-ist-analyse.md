# 01 – Ist-Analyse der bestehenden Seite (www.grabnar.de)

Stand: 2026-10-26. **Unvollständig** – die Seite blockt automatisierten Zugriff per `robots.txt`.
Die Lücken unten (⬜) sind von Felix zu füllen oder nach Freigabe der robots.txt per Crawl zu ergänzen.

## Unternehmen

- M.B. Grabnar Gebäudereinigungs- und Handwerker-Service GmbH
- Region: Stuttgart und Umland (Standorte/Einsatzorte u. a. Affalterbach, Pleidelsheim)
- Telefon lt. Branchenverzeichnis: 0711 2 36 33 30 (⬜ gegen Impressum prüfen)

## Leistungen (aus Branchenverzeichnissen, ⬜ gegen Seite abgleichen)

- Unterhaltsreinigung
- Glasreinigung
- Fassadenreinigung (inkl. Umkehr-Osmose-Verfahren)
- Teppichreinigung
- Desinfektion
- Winterdienst
- Hausmeisterdienst / Gebäudemanagement
- Entrümpelung
- Kleintransporte
- Arbeitnehmerüberlassung
- Handwerker-Service (im Firmennamen; ⬜ Umfang klären)

## Zielgruppen (abgeleitet)

1. **Gewerbekunden** (Hausverwaltungen, Büros, Produktion, öffentliche Hand) – Anfrage/Angebot
2. **Bewerber** – es laufen aktiv Stellenanzeigen (Vorarbeiter, Reinigungskraft, Objektleitung) auf StepStone u. a.
3. Privatkunden (Glas-, Teppichreinigung, Entrümpelung) – ⬜ Relevanz klären

## Technik der Altseite

- Wagtail + CodeRed CMS (coderedcms), Bootstrap-Frontend aus CodeRed
- Alter > 2 Jahre, keine Updates seit Relaunch ~2023
- ⬜ Exakte Versionen: `pip freeze` auf dem Server (`wagtail`, `coderedcms`, `django`, Python)
- ⬜ Hosting: Server, OS, Datenbank (SQLite/Postgres?), Mailversand
- ⬜ DNS/Domain-Verwaltung, TLS

## Seitenbaum der Altseite

⬜ Aus dem Wagtail-Admin exportieren (Seiten → Baum) oder per Crawl nach robots.txt-Freigabe.
Ziel: vollständige Liste aller öffentlichen URLs für das Redirect-Konzept (`docs/03-technik.md`).

```
/                      Startseite
/leistungen/…          (vermutet)
/karriere/… | /jobs/…  (vermutet)
/kontakt/
/impressum/
/datenschutz/
```

## Inhalte, die übernommen werden müssen

- ⬜ Texte Leistungsseiten (als Markdown exportieren → `docs/content-export/`)
- ⬜ Bilder (Originaldateien aus `media/original_images/`)
- ⬜ Impressum, Datenschutzerklärung (rechtlich prüfen, ob aktuell)
- ⬜ Stellenanzeigen (laufen aktuell extern – ggf. Quelle für JobPage-Inhalte)
- ⬜ Formulare: Welche gibt es, wohin gehen die Mails?

## Bekannte Schwächen / Anlass des Relaunchs

- Veralteter Stack, kein Upgrade-Pfad ohne Neuaufbau
- ⬜ Design/UX-Mängel, Performance (Lighthouse-Werte erfassen), Mobile-Darstellung
- ⬜ SEO-Status: Google Search Console vorhanden? Rankings für „Gebäudereinigung Stuttgart“ etc.
