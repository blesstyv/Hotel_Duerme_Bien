"""Configuración común; secretos locales o variables de la plataforma."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=False)


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in {"true", "1", "yes"}


PRODUCTION = os.getenv("DJANGO_ENV", "development") == "production"

SECRET_KEY = os.getenv("SECRET_KEY", "")

if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured(
        "Configure SECRET_KEY con al menos 50 caracteres en .env o en el entorno."
    )

DEBUG = env_bool("DEBUG", not PRODUCTION)

if PRODUCTION and DEBUG:
    raise ImproperlyConfigured(
        "DEBUG debe estar desactivado en producción."
    )


ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost,testserver",
    ).split(",")
    if host.strip()
]

if PRODUCTION and (
    not ALLOWED_HOSTS
    or "*" in ALLOWED_HOSTS
    or "testserver" in ALLOWED_HOSTS
):
    raise ImproperlyConfigured(
        "Configure ALLOWED_HOSTS con los dominios concretos de producción."
    )


CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "hotel.apps.HotelConfig",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "hotel.middleware.SessionSecurityMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]


WSGI_APPLICATION = "config.wsgi.application"

ASGI_APPLICATION = "config.asgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv(
            "DB_PATH",
            str(BASE_DIR / "db.sqlite3"),
        ),
        "OPTIONS": {
            "timeout": 20,
            "transaction_mode": "IMMEDIATE",
        },
    }
}


AUTH_USER_MODEL = "hotel.Usuario"


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
    },
    {
        "NAME":
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 10,
        },
    },
    {
        "NAME":
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
    },
    {
        "NAME":
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
    },
]


LANGUAGE_CODE = "es-cl"

TIME_ZONE = "America/Santiago"

USE_I18N = True

USE_TZ = True


STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"


STORAGES = {
    "default": {
        "BACKEND":
            "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedManifestStaticFilesStorage"
            if PRODUCTION
            else
            "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


LOGIN_URL = "hotel:login"

CSRF_FAILURE_VIEW = "hotel.views.csrf_failure"

LOGIN_REDIRECT_URL = "hotel:inicio"

LOGOUT_REDIRECT_URL = "hotel:login"


SESSION_COOKIE_AGE = int(
    os.getenv(
        "SESSION_COOKIE_AGE",
        "1800",
    )
)

SESSION_SAVE_EVERY_REQUEST = True

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SAMESITE = "Lax"

SESSION_COOKIE_SECURE = PRODUCTION

CSRF_COOKIE_SECURE = PRODUCTION


SECURE_SSL_REDIRECT = PRODUCTION

SECURE_HSTS_SECONDS = (
    31536000
    if PRODUCTION
    else 0
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = PRODUCTION

SECURE_HSTS_PRELOAD = PRODUCTION

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_REFERRER_POLICY = "same-origin"

X_FRAME_OPTIONS = "DENY"


# Activar solamente detrás de un proxy confiable
# que elimine correctamente el encabezado entrante.
if env_bool("TRUST_PROXY_HTTPS"):
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class":
                "logging.StreamHandler",
        }
    },
    "root": {
        "handlers": [
            "console",
        ],
        "level":
            "WARNING",
    },
}