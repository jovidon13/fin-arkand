"""Production settings — Docker container behind a TLS-terminating proxy
(Railway, Coolify, Nginx, …). Always online."""
from .base import *  # noqa: F401,F403
from .base import CSRF_TRUSTED_ORIGINS, env

DEBUG = False
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", default=["*"])

# Railway (and most PaaS) inject the app's public domain. Trust it automatically
# so ALLOWED_HOSTS / CSRF work out of the box without extra manual config.
_railway_domain = env("RAILWAY_PUBLIC_DOMAIN", default="")
if _railway_domain:
    if "*" not in ALLOWED_HOSTS and _railway_domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_railway_domain)
    _railway_origin = f"https://{_railway_domain}"
    if _railway_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_railway_origin)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("DJANGO_HSTS_SECONDS", default=2592000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
