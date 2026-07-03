"""Development settings. Loaded by manage.py by default."""
from .base import *  # noqa: F401,F403
from .base import BASE_DIR, env

DEBUG = env("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = ["*"]

# Allow running management checks / migrations without a live Postgres by
# setting USE_SQLITE=1. Real dev & prod use Postgres via DATABASE_URL.
if env.bool("USE_SQLITE", default=False):
    DATABASES = {  # noqa: F811
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

CORS_ALLOW_ALL_ORIGINS = True
