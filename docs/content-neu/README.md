# Neutexte (Vorschläge)

Überarbeitete Fließtexte für die 22 Leistungsseiten, die Startseite und „Unternehmen“.
Eine Datei pro Seite; `manage.py import_legacy` (und damit `seed_dev`) übernimmt den Teil
unter `---` als Fließtext der Seite. Kurztext, Einleitung und SEO kommen weiterhin aus
`../content-overrides.csv`.

## Regeln für die Texte

- Nur Aussagen, die schon auf der Altseite standen (`../content-export/`). Nichts Neues über
  die Firma ohne Freigabe – offene Fragen stehen in der Zeile „Hinweise“ jeder Datei.
- Sie-Form, kurze Absätze, Nutzen vor Begriffserklärung, Leistungen als Liste.
- Überschriften beginnen mit `##` (h2); der Seitentitel ist die h1.
- Interne Links nur auf neue Pfade (`/gebaeudereinigung/…/`), siehe `../redirects.csv`.
- Der Kurztext aus `content-overrides.csv` darf nicht wörtlich im Fließtext stehen.

## Freigabe

1. Datei mit der Firma durchgehen, Text direkt hier ändern.
2. Zeile `- Status: Vorschlag` auf `- Status: freigegeben` setzen.
3. Vor dem Go-Live: Dateien, die die Firma ablehnt, löschen – dann gilt wieder der Alttext.

Lokal vergleichen: `uv run manage.py seed_dev` zeigt die Neutexte,
`uv run manage.py import_legacy --originaltexte` die Alttexte.

| Datei | Seite |
|---|---|
| [startseite.md](startseite.md) | Startseite (`/`) |
| [unternehmen.md](unternehmen.md) | Unternehmen (`/unternehmen/`) |
| [gebaeudereinigung__baureinigung.md](gebaeudereinigung__baureinigung.md) | Baureinigung (`/gebaeudereinigung/baureinigung/`) |
| [gebaeudereinigung__containerreinigung.md](gebaeudereinigung__containerreinigung.md) | Containerreinigung (`/gebaeudereinigung/containerreinigung/`) |
| [gebaeudereinigung__desinfektion.md](gebaeudereinigung__desinfektion.md) | Desinfektion nach IfSG §17/3 (`/gebaeudereinigung/desinfektion/`) |
| [gebaeudereinigung__glasreinigung.md](gebaeudereinigung__glasreinigung.md) | Glas- und Fassadenreinigung (`/gebaeudereinigung/glasreinigung/`) |
| [gebaeudereinigung__grundreinigung.md](gebaeudereinigung__grundreinigung.md) | Grundreinigung (`/gebaeudereinigung/grundreinigung/`) |
| [gebaeudereinigung__industriereinigung.md](gebaeudereinigung__industriereinigung.md) | Hallen- und Industriereinigung (`/gebaeudereinigung/industriereinigung/`) |
| [gebaeudereinigung__polsterreinigung.md](gebaeudereinigung__polsterreinigung.md) | Teppich- und Polsterreinigung (`/gebaeudereinigung/polsterreinigung/`) |
| [gebaeudereinigung__sonderreinigung.md](gebaeudereinigung__sonderreinigung.md) | Sonderreinigung (`/gebaeudereinigung/sonderreinigung/`) |
| [gebaeudereinigung__unterhaltsreinigung.md](gebaeudereinigung__unterhaltsreinigung.md) | Unterhaltsreinigung (`/gebaeudereinigung/unterhaltsreinigung/`) |
| [gebaeudedienste__gruenanlagenpflege.md](gebaeudedienste__gruenanlagenpflege.md) | Grau- und Grünanlagenpflege (`/gebaeudedienste/gruenanlagenpflege/`) |
| [gebaeudedienste__hausmeisterdienste.md](gebaeudedienste__hausmeisterdienste.md) | Hausmeisterdienste (`/gebaeudedienste/hausmeisterdienste/`) |
| [gebaeudedienste__winterdienst.md](gebaeudedienste__winterdienst.md) | Winterdienst (`/gebaeudedienste/winterdienst/`) |
| [handwerkerdienste__bauhilfsarbeiten.md](handwerkerdienste__bauhilfsarbeiten.md) | Bauhilfsarbeiten (`/handwerkerdienste/bauhilfsarbeiten/`) |
| [handwerkerdienste__bodenverlegerarbeiten.md](handwerkerdienste__bodenverlegerarbeiten.md) | Bodenverlegerarbeiten (`/handwerkerdienste/bodenverlegerarbeiten/`) |
| [handwerkerdienste__bodenversiegelung.md](handwerkerdienste__bodenversiegelung.md) | Bodenversiegelung (`/handwerkerdienste/bodenversiegelung/`) |
| [handwerkerdienste__fliesenlegerarbeiten.md](handwerkerdienste__fliesenlegerarbeiten.md) | Fliesenlegerarbeiten (`/handwerkerdienste/fliesenlegerarbeiten/`) |
| [handwerkerdienste__malerarbeiten.md](handwerkerdienste__malerarbeiten.md) | Maler- und Maurerarbeiten (`/handwerkerdienste/malerarbeiten/`) |
| [handwerkerdienste__trockenbau.md](handwerkerdienste__trockenbau.md) | Trockenbau (`/handwerkerdienste/trockenbau/`) |
| [services__arbeitnehmerueberlassung.md](services__arbeitnehmerueberlassung.md) | Arbeitnehmerüberlassung (`/services/arbeitnehmerueberlassung/`) |
| [services__entruempelung.md](services__entruempelung.md) | Entrümpelung (`/services/entruempelung/`) |
| [services__transportarbeiten.md](services__transportarbeiten.md) | Transportarbeiten (`/services/transportarbeiten/`) |
| [services__wachdienste.md](services__wachdienste.md) | Wach- und Schließdienste (`/services/wachdienste/`) |
