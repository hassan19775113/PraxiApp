"""
Views für das Operations-Dashboard.

Enthält:
- OperationsDashboardView: Hauptansicht des Operations-Dashboards
- OperationsAPIView: JSON-API für AJAX-Anfragen
"""
from __future__ import annotations

from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from .services import (
    build_operations_api_payload,
    build_operations_dashboard_context,
    parse_operations_request,
)


class OperationsDashboardView(TemplateView):
    """
    Hauptansicht für das Operations-Dashboard.
    
    Zeigt:
    - KPI-Cards (Auslastung, Durchsatz, No-Show, etc.)
    - Patientenfluss-Visualisierung
    - Ressourcen-Heatmaps
    - Engpass-Analysen
    - Leistungsübersicht
    """
    template_name = 'dashboard/operations.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Zeitraum aus Query-Parameter
        days, view_mode, _include_charts = parse_operations_request(self.request.GET)
        # UI uses overview/realtime/resources; API uses standard/realtime.
        if view_mode == "standard":
            view_mode = "overview"

        payload, _charts = build_operations_dashboard_context(days=days, view_mode=view_mode)
        context.update(payload)
        return context


class OperationsAPIView(View):
    """
    JSON-API für Operations-Dashboard-Daten.
    
    Unterstützt:
    - GET /api/operations-dashboard/?days=30 - Alle KPIs
    - GET /api/operations-dashboard/?mode=realtime - Echtzeit-Daten
    """
    
    def get(self, request):
        days, mode, include_charts = parse_operations_request(request.GET)
        return JsonResponse(build_operations_api_payload(days=days, mode=mode, include_charts=include_charts))


class OperationsResourceView(TemplateView):
    """
    Detailansicht für einzelne Ressourcen.
    """
    template_name = 'dashboard/operations_resource.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        resource_id = self.kwargs.get('resource_id')
        days = int(self.request.GET.get('days', 30))
        
        # TODO: Detaillierte Ressourcen-KPIs implementieren
        context['resource_id'] = resource_id
        context['selected_days'] = days
        context['title'] = 'Ressourcen-Details'
        
        return context
