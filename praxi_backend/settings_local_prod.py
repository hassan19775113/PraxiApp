"""
Lokale Production-ähnliche Settings für Tests.

Verwendung (PowerShell):
    $env:DJANGO_SETTINGS_MODULE = "praxi_backend.settings_local_prod"
    python manage.py collectstatic --noinput
    python manage.py runserver
"""

from .settings_dev import *

DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Lokale Static-Files direkt aus Finders laden (verhindert stale Cache)
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = True

# Media in lokalem Prod-Setup ueber Django serven
SERVE_MEDIA = True

# Lokale Tests ohne HTTPS erzwingen
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
