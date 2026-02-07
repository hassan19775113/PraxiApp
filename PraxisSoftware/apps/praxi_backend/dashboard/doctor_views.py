"""
Views für das Ärzte-Dashboard.

Enthält:
- DoctorDashboardView: Übersicht aller Ärzte
- DoctorDetailView: Detail-Dashboard für einen Arzt
- DoctorAPIView: JSON-API für AJAX-Anfragen
"""

from __future__ import annotations

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView

from .permissions import dashboard_access_required
from .services import (
    build_doctors_api_payload,
    build_doctors_compare_context,
    build_doctors_dashboard_context,
    parse_doctors_dashboard_request,
)
from .validators import parse_int, parse_optional_int


class DoctorDashboardView(TemplateView):
    """
    Übersichts-Dashboard für alle Ärzte.
    """

    template_name = "dashboard/doctors.html"

    @method_decorator(dashboard_access_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        base = super().get_context_data(**kwargs)
        selected_doctor_id, period, days, period_label = parse_doctors_dashboard_request(
            query_params=self.request.GET,
            kwargs=self.kwargs,
        )
        ctx = build_doctors_dashboard_context(
            selected_doctor_id=selected_doctor_id,
            days=days,
            period=period,
            period_label=period_label,
        )
        base.update(ctx)
        return base


class DoctorAPIView(View):
    """
    JSON-API für Ärzte-Dashboard-Daten.
    """

    def get(self, request, doctor_id: int | None = None):
        days = parse_int(request.GET.get("days"), default=30, min_value=1, max_value=366)
        payload = build_doctors_api_payload(doctor_id=doctor_id, days=days)
        return JsonResponse(payload)


class DoctorCompareView(TemplateView):
    """
    Vergleichsansicht für zwei Ärzte.
    """

    template_name = "dashboard/doctors_compare.html"

    @method_decorator(dashboard_access_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        base = super().get_context_data(**kwargs)
        doctor1_id = parse_optional_int(self.request.GET.get("doctor1"))
        doctor2_id = parse_optional_int(self.request.GET.get("doctor2"))
        days = parse_int(self.request.GET.get("days"), default=30, min_value=1, max_value=366)
        base.update(
            build_doctors_compare_context(doctor1_id=doctor1_id, doctor2_id=doctor2_id, days=days)
        )
        return base
