# grabnar_relaunch – Projektkontext für Claude Code

Relaunch der Firmenwebseite **www.grabnar.de** der
M.B. Grabnar Gebäudereinigungs- und Handwerker-Service GmbH (Raum Stuttgart / Affalterbach / Pleidelsheim).
Betreut von Felix (Administrator der Seite, Full-Stack-Entwickler, GitHub `fmbecker`).

## Ausgangslage

- Bestehende Seite: Wagtail + CodeRed CMS (coderedcms), Stand ca. 2023/2024, über zwei Jahre nicht aktualisiert.
- Ein Versionssprung von Wagtail und coderedcms wäre ohnehin ein Neuaufbau → Entscheidung für einen sauberen Neustart.
- Kein bestehendes Repo; alles entsteht neu in `fmbecker/grabnar_relaunch`.

## Zielarchitektur (entschieden)

**Headless Wagtail + Astro + Tailwind + React nur wo nötig.**

| Teil | Technik | Ordner |
|---|---|---|
| CMS / Backend | Wagtail (aktuelle LTS), Django, Postgres, `wagtail.api.v2`, ohne coderedcms | `cms/` |
| Frontend | Astro (statisch, SSG), Tailwind CSS, React-Islands nur für Interaktion (Formulare, Filter, Slider) | `web/` |
| Hosting | bestehender Linode-VPS: Nginx liefert `web/dist/` statisch aus und proxyt `/admin/`, `/api/` an Wagtail (Docker Compose); `/admin/` per IP-Allowlist/Basic-Auth | `deploy/` |
| Build-Trigger | Wagtail `page_published`-Signal → lokaler Webhook (:9000) → `pnpm build` auf dem Server | `cms/grabnar/signals.py`, `deploy/rebuild-hook.py` |

Begründung und Alternativen: `docs/03-technik.md`.

## Monorepo-Layout (Soll)

```
grabnar_relaunch/
├── CLAUDE.md                 ← diese Datei
├── docs/                     ← Konzept, Analyse, Aufgaben (zuerst lesen!)
├── cms/                      ← Wagtail-Projekt (Python, uv oder pip-tools)
│   ├── grabnar/              ← Django-Projekt (settings/, urls.py, api.py, signals.py, tests/)
│   ├── home/                 ← HomePage, StandardPage
│   ├── services/             ← ServiceIndexPage, ServicePage
│   ├── jobs/                 ← JobIndexPage, JobPage
│   ├── blocks/               ← gemeinsame StreamField-Blocks
│   ├── site_settings/        ← wagtail.contrib.settings (Kontakt, Footer, Social)
│   ├── forms_api/            ← Kontakt-/Bewerbungs-Endpunkte, Submissions im Admin
│   └── Dockerfile
├── web/                      ← Astro-Projekt
│   ├── src/lib/wagtail.ts    ← typisierter API-Client
│   ├── src/lib/types.ts      ← Typen zu den StreamField-Blocks (Vertrag mit cms/blocks)
│   ├── src/components/blocks/← ein .astro pro Block
│   ├── src/components/islands/ ← React-Islands (ContactForm.tsx, JobFilter.tsx …)
│   ├── src/components/PageContent.astro ← rendert alle Seitentypen (auch für Preview)
│   ├── src/layouts/Base.astro
│   ├── src/pages/[...slug].astro
│   └── scripts/redirects.mjs ← Nginx-map aus /api/v2/redirects/
├── deploy/                   ← docker-compose.yml, nginx/, rebuild-hook.py, build-web.sh, deploy.sh
└── README.md
```

## Lokal starten

```
cd cms && uv sync && uv run manage.py migrate && uv run manage.py seed_dev --superuser && uv run manage.py runserver
cd web && pnpm install && cp .env.example .env && pnpm dev     # http://localhost:4321
```

Prüfen vor jedem Commit: `cd cms && uv run ruff check . && uv run pytest -q` · `cd web && pnpm lint && pnpm check && pnpm build`.

## Arbeitsweise

- Reihenfolge: `docs/01-ist-analyse.md` → `docs/02-konzept.md` → `docs/03-technik.md` → `docs/04-aufgaben.md`. Die Aufgabenliste ist die Quelle der Wahrheit für den Fortschritt; erledigte Punkte dort abhaken.
- **Block-Vertrag zuerst**: Jeder StreamField-Block in `cms/blocks/` hat genau einen Typ in `web/src/lib/types.ts` und genau eine Komponente in `web/src/components/blocks/`. Keine Komponente ohne Block, kein Block ohne Komponente.
- Sprache: Inhalte und Redakteurs-Oberfläche auf Deutsch (`LANGUAGE_CODE = "de"`), Code und Kommentare auf Englisch, Doku auf Deutsch.
- Keine coderedcms-Abhängigkeit, kein Bootstrap. Tailwind ausschließlich.
- Formulare (Kontakt, Bewerbung) senden an einen eigenen Endpunkt im CMS (`cms/forms_api/`), nicht an Drittanbieter, wegen Datenschutz (Bewerbungsdaten!).
- Bilder: ausschließlich über Wagtail-Renditions aus der API, nie Originaldateien im Frontend.
- `grabnar/urls.py` registriert `wagtail_urls` immer (auch in Produktion): `page.url` braucht `reverse("wagtail_serve")`. Nicht entfernen.
- Vor größeren Entscheidungen (Hosting, Domainumzug, Löschen alter Inhalte) Felix fragen.

## Konventionen

- Python: `ruff` (format + lint), Typannotationen, Django-Settings aufgeteilt in `base.py` / `dev.py` / `production.py`.
- TypeScript: `strict: true`, Komponenten in PascalCase, Astro-Komponenten für Statisches, `.tsx` nur für Islands mit `client:visible` oder `client:idle`.
- Commits: Conventional Commits, Deutsch oder Englisch, Präfix `cms:` / `web:` / `docs:`.
- Branch-Modell: `main` = deploybar, Feature-Branches `feat/<thema>`.

## Offene Punkte (siehe docs/04-aufgaben.md)

- Inhalte der alten Seite noch nicht vollständig erfasst (robots.txt blockt automatisierten Zugriff).
- Headless-Preview-Route im Frontend ist ein Platzhalter (siehe docs/04-aufgaben.md, Phase 2).
- Zustand des Linode-VPS (OS, Nginx-Config, Docker, certbot) noch nicht erfasst.
- Redirect-Konzept von alten URLs noch offen (Mapping in `docs/redirects.csv`).
