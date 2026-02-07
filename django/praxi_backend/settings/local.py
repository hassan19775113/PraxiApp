"""Local production-like settings.

Goal:
- behave like production (WhiteNoise, JSON-only, DEBUG=False)
- but remain easy to run locally (no forced HTTPS redirect, no hard requirement for
  DJANGO_SECRET_KEY)
"""

from __future__ import annotations

from .base import *  # noqa: F403,F405

DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

# WhiteNoise
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    try:
        security_idx = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
    except ValueError:
        security_idx = 0
    MIDDLEWARE.insert(security_idx + 1, "whitenoise.middleware.WhiteNoiseMiddleware")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# WhiteNoise: use finders/autorefresh to avoid stale cache locally
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = True

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
}

# Local tests without HTTPS
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Serve media in local prod-like setup
SERVE_MEDIA = True
