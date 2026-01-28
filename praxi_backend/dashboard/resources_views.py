"""
Views für Ressourcen- und Raumverwaltung.

Enthält:
- ResourcesDashboardView: Übersicht aller Ressourcen (Räume, Geräte)
"""
from __future__ import annotations

import json

from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from .permissions import dashboard_access_required
from .services import build_resources_dashboard_context


class ResourcesDashboardView(TemplateView):
    """
    Hauptansicht für Ressourcen- und Raumverwaltung.
    
    Zeigt:
    - Übersicht aller Räume
    - Übersicht aller Geräte
    - Status und Auslastung
    - Farbcodierung pro Ressource
    """
    template_name = 'dashboard/resources.html'

    @method_decorator(dashboard_access_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_resources_dashboard_context())
        return context

