# cms/ – Headless Wagtail

```
uv sync                              # install
uv run manage.py migrate
uv run manage.py seed_dev --superuser  # example site, admin/admin (dev only)
uv run manage.py runserver           # http://localhost:8000/admin/
```

API: `/api/v2/pages/`, `/api/v2/images/`, `/api/v2/settings/`, `/api/v2/navigation/`, `/api/v2/redirects/`
Forms: `POST /api/forms/contact/`, `POST /api/forms/application/`
Config via `.env` (see `.env.example`). Production uses `grabnar.settings.production` + Postgres.
