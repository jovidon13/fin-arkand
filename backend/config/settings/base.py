"""
Base settings for ARKAND Finance CRM.

Single modular monolith: one backend, one set of API contracts for the whole
holding. Domain modules are separate Django apps under ``apps/``.
"""
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["*"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:5173"]),
)

# Read .env if present (local dev). In prod env vars come from the environment.
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-change-me")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# --------------------------------------------------------------------------- #
# Applications
# --------------------------------------------------------------------------- #
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
]

# Order matters: core & accounts first (foundation), then domains.
LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.audit",
    "apps.finance",
    "apps.cash",
    "apps.settlements",
    "apps.payroll",
    "apps.approvals",
    "apps.reports",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
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
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --------------------------------------------------------------------------- #
# Database — PostgreSQL 16 (transactions, money, audit)
# --------------------------------------------------------------------------- #
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://arkand:arkand@localhost:5432/arkand",
    )
}
DATABASES["default"].setdefault("ATOMIC_REQUESTS", False)

# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------------------------------- #
# Internationalization — interface RU (default) + TJ (i18n from day one)
# --------------------------------------------------------------------------- #
LANGUAGE_CODE = "ru"
LANGUAGES = [("ru", "Русский"), ("tg", "Тоҷикӣ")]
TIME_ZONE = "Asia/Dushanbe"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------- #
# Django REST Framework
# --------------------------------------------------------------------------- #
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.DefaultPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ),
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Money in JSON is a string, never a float — this is the DRF default for
    # DecimalField (coerce_to_string=True); kept explicit for clarity.
    "COERCE_DECIMAL_TO_STRING": True,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ARKAND Finance API",
    "DESCRIPTION": "Финансовая CRM холдинга ARKAND — приходы/расходы, кассы, "
    "взаиморасчёты, зарплата, согласования, отчёты.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# --------------------------------------------------------------------------- #
# CORS
# --------------------------------------------------------------------------- #
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")

# --------------------------------------------------------------------------- #
# Celery — payroll, reports, exports
# --------------------------------------------------------------------------- #
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE

# --------------------------------------------------------------------------- #
# Domain constants
# --------------------------------------------------------------------------- #
# Number of holding owners that must approve a large expense (ХОЛ-22…23).
OWNER_APPROVALS_REQUIRED = env.int("OWNER_APPROVALS_REQUIRED", default=3)
