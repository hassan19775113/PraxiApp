"""Legacy settings module (compatibility shim).

New modular settings live in the package ``praxi_backend.settings``.

Prefer:
    DJANGO_SETTINGS_MODULE=praxi_backend.settings.dev
    DJANGO_SETTINGS_MODULE=praxi_backend.settings.prod
    DJANGO_SETTINGS_MODULE=praxi_backend.settings.local
"""

from praxi_backend.settings.base import *  # noqa