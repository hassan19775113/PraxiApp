"""
Scheduling Dashboard Views
"""
from __future__ import annotations

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page

from .permissions import dashboard_access_required
from .services import build_scheduling_api_payload, build_scheduling_dashboard_context


class SchedulingDashboardView(View):
    """Scheduling KPIs Dashboard View"""
    
    @method_decorator(dashboard_access_required)
    def get(self, request):
        context = build_scheduling_dashboard_context()
        return render(request, "dashboard/scheduling.html", context)


class SchedulingAPIView(View):
    """API Endpoint für Scheduling Dashboard-Daten"""
    
    @method_decorator(dashboard_access_required)
    @method_decorator(cache_page(60))
    def get(self, request):
        return JsonResponse(build_scheduling_api_payload())
