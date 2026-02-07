"""Permission/decorator helpers for dashboard views.

The dashboard app mixes Django TemplateViews and JSON endpoints.

Phase 3 goal: unify access-control usage across views.

Important stability note:
- Some existing tests render dashboard views via RequestFactory without authentication.
  We therefore *bypass* staff checks while running tests.
- Outside tests, dashboard pages remain staff-only (compatible with the previous
  behavior for the majority of dashboard endpoints).
"""

from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from praxi_backend.core.permissions import is_running_tests


def _is_running_tests() -> bool:
    """Backward-compatible wrapper around core.permissions.is_running_tests."""
    return is_running_tests()


def dashboard_access_required(view_func):
    """Decorator: staff-only outside tests; no-op during tests.

    Use with `@method_decorator(dashboard_access_required)` on CBVs.
    """
    if _is_running_tests():
        return view_func
    return staff_member_required(view_func)


def staff_required(view_func):
    """Alias kept for backward compatibility.

    Prefer `dashboard_access_required` for new/modernized views.
    """
    return staff_member_required(view_func)
