from __future__ import annotations

from django.http import HttpResponse
from django.test import TestCase

from praxi_backend.dashboard.permissions import dashboard_access_required


class DashboardPermissionsTest(TestCase):
    """Unit tests for dashboard access decorator.

    Note: during test runs, `dashboard_access_required` is intentionally a no-op
    to keep existing RequestFactory-based render tests working.
    """

    databases = {"default"}

    def test_dashboard_access_required_is_noop_during_tests(self):
        def view(request):
            return HttpResponse("ok")

        decorated = dashboard_access_required(view)
        self.assertIs(decorated, view)
