from __future__ import annotations

import os
from urllib.parse import urlparse

from .base import *  # noqa: F403,F405

# ------------------------------------------------------------
# Production overrides
# ------------------------------------------------------------

DEBUG = os.getenv("DJANGO_DEBUG", "False").strip().lower() == "true"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1],praxis-server,.local").split(",")
    if h.strip()
]

# Enforce secret key in production deployments
if not os.getenv("DJANGO_SECRET_KEY"):
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production")

# Database: Use DATABASE_URL for production
if os.getenv("DATABASE_URL"):
    db_url = urlparse(os.getenv("DATABASE_URL"))
    sslmode = os.getenv("DB_SSLMODE")  # optional; omit for local/on-prem
    db_options = {"connect_timeout": 10}
    if sslmode:
        db_options["sslmode"] = sslmode

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_url.path.lstrip("/"),
            "USER": db_url.username,
            "PASSWORD": db_url.password,
            "HOST": db_url.hostname,
            "PORT": db_url.port or 5432,
            "CONN_MAX_AGE": 600,
            "OPTIONS": db_options,
        }
    }

# Security
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False").strip().lower() == "true"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if SECURE_SSL_REDIRECT else None

SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").strip().lower() == "true"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "False").strip().lower() == "true"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# WhiteNoise
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    try:
        security_idx = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
    except ValueError:
        security_idx = 0
    # WhiteNoise should come right after SecurityMiddleware.
    MIDDLEWARE.insert(security_idx + 1, "whitenoise.middleware.WhiteNoiseMiddleware")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_ROOT = BASE_DIR / "staticfiles"

# REST: JSON only
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_PARSER_CLASSES": ("rest_framework.parsers.JSONParser",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("DRF_THROTTLE_ANON", "100/hour"),
        "user": os.getenv("DRF_THROTTLE_USER", "1000/hour"),
    },
}

# JWT shorter lifetimes
SIMPLE_JWT = {
    **SIMPLE_JWT,
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "1"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# Celery enabled in prod by default (disabled for Vercel serverless)
# For Vercel: Use Vercel Cron Jobs or external worker services
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_ENABLED", "False").strip().lower() == "true"

# Cache (Redis if configured; otherwise fall back to local memory)
if os.getenv("REDIS_HOST"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
        }
    }

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").strip().lower() == "true"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@praxiapp.com")
