"""Configuración común; secretos locales o variables de la plataforma."""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(
    BASE_DIR / ".env",
    override=False,
)


def env_bool(
    name,
    default=False,
):
    return (
        os.getenv(
            name,
            str(default),
        ).lower()
        in {
            "true",
            "1",
            "yes",
        }
    )


PRODUCTION = (
    os.getenv(
        "DJANGO_ENV",
        "development",
    )
    ==
    "production"
)


SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "",
)

if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured(
        "Configure SECRET_KEY con al menos "
        "50 caracteres en .env o en el entorno."
    )


DEBUG = env_bool(
    "DEBUG",
    not PRODUCTION,
)

if PRODUCTION and DEBUG:
    raise ImproperlyConfigured(
        "DEBUG debe estar desactivado "
        "en producción."
    )


# ============================================================
# HOSTS / RENDER
# ============================================================

raw_allowed_hosts = os.getenv(
    "ALLOWED_HOSTS",
    "",
)

ALLOWED_HOSTS = [
    host.strip()
    for host
    in raw_allowed_hosts.split(",")
    if host.strip()
]


if not PRODUCTION:
    for host in (
        "127.0.0.1",
        "localhost",
        "testserver",
    ):
        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(
                host
            )


# Render define automáticamente esta variable
# en el servicio desplegado.
RENDER_EXTERNAL_HOSTNAME = (
    os.getenv(
        "RENDER_EXTERNAL_HOSTNAME",
        "",
    ).strip()
)

if (
    RENDER_EXTERNAL_HOSTNAME
    and
    RENDER_EXTERNAL_HOSTNAME
    not in ALLOWED_HOSTS
):
    ALLOWED_HOSTS.append(
        RENDER_EXTERNAL_HOSTNAME
    )


if PRODUCTION and not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "Configure ALLOWED_HOSTS "
        "con los dominios concretos "
        "de producción."
    )


CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin
    in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]


if RENDER_EXTERNAL_HOSTNAME:
    render_origin = (
        "https://"
        +
        RENDER_EXTERNAL_HOSTNAME
    )

    if (
        render_origin
        not in CSRF_TRUSTED_ORIGINS
    ):
        CSRF_TRUSTED_ORIGINS.append(
            render_origin
        )


# ============================================================
# APLICACIONES
# ============================================================

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
        "BACKEND":
            "django.template.backends.django.DjangoTemplates",

        "DIRS": [],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]


WSGI_APPLICATION = (
    "config.wsgi.application"
)

ASGI_APPLICATION = (
    "config.asgi.application"
)


# ============================================================
# BASE DE DATOS
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "",
).strip()


if DATABASE_URL:

    # Render PostgreSQL u otra base definida
    # mediante URL.
    DATABASES = {
        "default":
            dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=600,
            )
    }

else:

    # Desarrollo local:
    # conserva SQLite.
    DATABASES = {
        "default": {
            "ENGINE":
                "django.db.backends.sqlite3",

            "NAME":
                os.getenv(
                    "DB_PATH",
                    str(
                        BASE_DIR
                        /
                        "db.sqlite3"
                    ),
                ),

            "OPTIONS": {
                "timeout": 20,
                "transaction_mode":
                    "IMMEDIATE",
            },
        }
    }


AUTH_USER_MODEL = (
    "hotel.Usuario"
)


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


# ============================================================
# INTERNACIONALIZACIÓN
# ============================================================

LANGUAGE_CODE = "es-cl"

TIME_ZONE = (
    "America/Santiago"
)

USE_I18N = True

USE_TZ = True


# ============================================================
# ARCHIVOS ESTÁTICOS
# ============================================================

STATIC_URL = "/static/"

STATIC_ROOT = (
    BASE_DIR
    /
    "staticfiles"
)


STORAGES = {
    "default": {
        "BACKEND":
            "django.core.files.storage."
            "FileSystemStorage",
    },

    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedManifestStaticFilesStorage"
            if PRODUCTION
            else
            "django.contrib.staticfiles.storage."
            "StaticFilesStorage"
        ),
    },
}


DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)


# ============================================================
# LOGIN / SESIÓN
# ============================================================

LOGIN_URL = (
    "hotel:login"
)

CSRF_FAILURE_VIEW = (
    "hotel.views.csrf_failure"
)

LOGIN_REDIRECT_URL = (
    "hotel:inicio"
)

LOGOUT_REDIRECT_URL = (
    "hotel:login"
)


SESSION_COOKIE_AGE = int(
    os.getenv(
        "SESSION_COOKIE_AGE",
        "1800",
    )
)


SESSION_SAVE_EVERY_REQUEST = (
    True
)

SESSION_EXPIRE_AT_BROWSER_CLOSE = (
    True
)

SESSION_COOKIE_HTTPONLY = (
    True
)

SESSION_COOKIE_SAMESITE = (
    "Lax"
)

CSRF_COOKIE_SAMESITE = (
    "Lax"
)

SESSION_COOKIE_SECURE = (
    PRODUCTION
)

CSRF_COOKIE_SECURE = (
    PRODUCTION
)


# ============================================================
# SEGURIDAD PRODUCCIÓN
# ============================================================

SECURE_SSL_REDIRECT = (
    PRODUCTION
)

SECURE_HSTS_SECONDS = (
    31536000
    if PRODUCTION
    else 0
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    PRODUCTION
)

SECURE_HSTS_PRELOAD = (
    PRODUCTION
)

SECURE_CONTENT_TYPE_NOSNIFF = (
    True
)

SECURE_REFERRER_POLICY = (
    "same-origin"
)

X_FRAME_OPTIONS = (
    "DENY"
)


# Render termina HTTPS delante de la aplicación
# y envía X-Forwarded-Proto=https.
#
# Solo habilitar esto detrás de un proxy
# confiable.
if env_bool(
    "TRUST_PROXY_HTTPS"
):
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )


# ============================================================
# LOGGING
# ============================================================

LOGGING = {
    "version": 1,

    "disable_existing_loggers":
        False,

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