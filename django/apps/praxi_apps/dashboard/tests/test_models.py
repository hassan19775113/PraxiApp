from __future__ import annotations

from django.test import TestCase


class DashboardModelsTest(TestCase):
    """Dashboard app currently has no dedicated models; keep a placeholder test.

    This file exists to match the structured test layout used across apps.
    """

    databases = {"default"}

    def test_dashboard_app_imports(self):
        import praxi_backend.dashboard  # noqa: F401
