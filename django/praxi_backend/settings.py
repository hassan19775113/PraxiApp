"""Compatibility shim for modular settings (PostgreSQL only).

Prefer:
    DJANGO_SETTINGS_MODULE=praxi_backend.settings.dev
    DJANGO_SETTINGS_MODULE=praxi_backend.settings.prod
    DJANGO_SETTINGS_MODULE=praxi_backend.settings.local
"""

from praxi_backend.settings.base import *  # noqa
