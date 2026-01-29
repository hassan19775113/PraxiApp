"""Shared helpers for appointments API view modules.

Phase 2B: `praxi_backend.appointments.views` is split into thematic modules.
This module holds small, non-view helpers that are used in more than one module.

Important: no behavior changes; helpers are copied verbatim from the former
monolithic `views.py`.
"""

from __future__ import annotations

from datetime import date, datetime

from rest_framework import status
from rest_framework.response import Response


def parse_required_date(request) -> tuple[date | None, Response | None]:
    date_str = request.query_params.get("date")
    if not date_str:
        return None, Response(
            {"detail": "Provide ?date=YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return d, None
    except ValueError:
        return None, Response(
            {"detail": "Date must be in format YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST
        )


def iso_z(dt: datetime) -> str:
    # Consistent ISO output; prefer Z when in UTC.
    value = dt.isoformat()
    return value.replace("+00:00", "Z")
