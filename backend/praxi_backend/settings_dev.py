"""Legacy dev settings module (compatibility shim).

This project uses the modular settings package under ``praxi_backend.settings``.

Prefer:
    DJANGO_SETTINGS_MODULE=praxi_backend.settings.dev

This shim is kept to avoid breaking older scripts, but it intentionally contains
no SQLite configuration.
"""

from praxi_backend.settings.dev import *  # noqa