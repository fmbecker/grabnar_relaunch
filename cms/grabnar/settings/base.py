"""Shared Django/Wagtail settings. Environment specifics live in dev.py / production.py."""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # -> cms/

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-only-insecure-key")
DEBUG = False
ALLOWED_HOSTS: list[str] = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS: list[str] = env.list("CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    # project apps
    "grabnar",
    "home",
    "services",
    "jobs",
    "blocks",
    "site_settings",
    "forms_api",
    # wagtail
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.settings",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail.api.v2",
    "wagtail",
    "wagtail_headless_preview",
    "modelcluster",
    "taggit",
    "rest_framework",
    "corsheaders",
    # django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "grabnar.urls"
WSGI_APPLICATION = "grabnar.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "grabnar" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
            ],
        },
    },
]

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Editors work in German; code stays English.
LANGUAGE_CODE = "de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

STATIC_ROOT = BASE_DIR / "collected-static"
STATIC_URL = "/django-static/"
MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "media"))
MEDIA_URL = "/media/"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Wagtail -------------------------------------------------------------

WAGTAIL_SITE_NAME = "Grabnar Gebäudereinigung"
WAGTAILADMIN_BASE_URL = env("WAGTAILADMIN_BASE_URL", default="http://localhost:8000")
WAGTAIL_I18N_ENABLED = False
WAGTAILIMAGES_EXTENSIONS = ["gif", "jpg", "jpeg", "png", "webp", "svg"]
WAGTAILDOCS_EXTENSIONS = ["pdf", "docx", "doc", "odt"]
WAGTAILIMAGES_FORMAT_CONVERSIONS = {"webp": "webp", "jpeg": "webp", "png": "webp"}

# The frontend renders; Wagtail never serves public pages.
WAGTAIL_SERVE_PAGES = False  # custom flag read in urls.py
WAGTAILAPI_LIMIT_MAX = 200
WAGTAILAPI_BASE_URL = WAGTAILADMIN_BASE_URL

WAGTAILSEARCH_BACKENDS = {
    "default": {"BACKEND": "wagtail.search.backends.database"},
}

# --- Headless frontend ----------------------------------------------------

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:4321")

HEADLESS_PREVIEW = {
    "CLIENT_URLS": {"default": f"{FRONTEND_URL}/preview/"},
    "SERVE_BASE_URL": FRONTEND_URL,
    "REDIRECT_ON_PREVIEW": False,
    "ENFORCE_TRAILING_SLASH": True,
}

FRONTEND_BUILD_HOOK_URL = env("FRONTEND_BUILD_HOOK_URL", default="")
FRONTEND_BUILD_HOOK_SECRET = env("FRONTEND_BUILD_HOOK_SECRET", default="")
FRONTEND_BUILD_DEBOUNCE_SECONDS = 60

CORS_ALLOWED_ORIGINS: list[str] = env.list("CORS_ALLOWED_ORIGINS", default=[FRONTEND_URL])
CORS_URLS_REGEX = r"^/api/.*$"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
}

# --- Forms / mail ---------------------------------------------------------

EMAIL_CONFIG = env.email("EMAIL_URL", default="consolemail://")
vars().update(EMAIL_CONFIG)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="website@localhost")
FORMS_NOTIFY_EMAIL = env("FORMS_NOTIFY_EMAIL", default="")
FORMS_MAX_UPLOAD_BYTES = 10 * 1024 * 1024
FORMS_ALLOWED_UPLOAD_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
# Applications are personal data: purge after this many days (management command).
FORMS_APPLICATION_RETENTION_DAYS = 180
