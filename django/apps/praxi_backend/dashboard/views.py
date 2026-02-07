"""Dashboard Views."""

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page

from .permissions import staff_required
from .services import build_main_dashboard_api_payload, build_main_dashboard_context


class DashboardView(View):
    """Haupt-Dashboard View"""

    @method_decorator(staff_required)
    def get(self, request):
        context = build_main_dashboard_context()
        return render(request, "dashboard/index_modern.html", context)


class DashboardAPIView(View):
    """API Endpoint für Dashboard-Daten (für AJAX-Refresh)"""

    @method_decorator(staff_required)
    @method_decorator(cache_page(60))  # 1 Minute Cache
    def get(self, request):
        return JsonResponse(build_main_dashboard_api_payload())
