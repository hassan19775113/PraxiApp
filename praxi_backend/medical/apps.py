"""Deprecated app config for the legacy `medical` app.

Kept for backwards compatibility only. The app is not installed.
"""

from django.apps import AppConfig


class MedicalConfig(AppConfig):  # pragma: no cover
	default_auto_field = "django.db.models.BigAutoField"
	name = "praxi_backend.medical"
	verbose_name = "DEPRECATED: medical (legacy)"
