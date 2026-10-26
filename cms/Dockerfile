FROM python:3.13-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 UV_SYSTEM_CERTS=1
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 libjpeg62-turbo libwebp7 zlib1g && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
ENV PATH="/app/.venv/bin:$PATH" DJANGO_SETTINGS_MODULE=grabnar.settings.production
RUN SECRET_KEY=build python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn grabnar.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60"]
