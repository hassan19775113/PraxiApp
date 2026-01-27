"""
Views für Ressourcen- und Raumverwaltung.

Enthält:
- ResourcesDashboardView: Übersicht aller Ressourcen (Räume, Geräte)
"""
from __future__ import annotations

import json

from django.views.generic import TemplateView

from praxi_backend.appointments.models import Resource
from praxi_backend.appointments.serializers import ResourceSerializer


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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Alle aktiven Ressourcen laden
        resources = Resource.objects.using('default').filter(active=True).order_by('type', 'name')
        
        # Räume und Geräte trennen
        rooms = [r for r in resources if r.type == Resource.TYPE_ROOM]
        devices = [r for r in resources if r.type == Resource.TYPE_DEVICE]
        
        # Serialisieren für Template
        context['title'] = 'Ressourcen & Räume'
        context['rooms'] = [ResourceSerializer(r).data for r in rooms]
        context['devices'] = [ResourceSerializer(r).data for r in devices]
        context['rooms_json'] = json.dumps([ResourceSerializer(r).data for r in rooms])
        context['devices_json'] = json.dumps([ResourceSerializer(r).data for r in devices])
        
        return context

