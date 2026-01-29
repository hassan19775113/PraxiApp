"""Views for the dashboard patients pages.

Phase 3 goal:
- Keep views thin (validate request -> call service -> return response)
- Keep response formats and template context keys stable
- Do not move files / do not add folders
"""

from __future__ import annotations

from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView

from .permissions import dashboard_access_required
from .services import (
    build_patient_document_detail_context,
    build_patient_prescription_detail_context,
    build_patients_api_payload,
    build_patients_dashboard_context,
    build_patients_nav_payload,
    build_patients_overview_context,
    create_patient_document,
    create_patient_note,
    parse_patient_id,
    search_patients_payload,
)


class PatientOverviewView(TemplateView):
    """Overview page with patient list and quick stats."""

    template_name = "dashboard/patients_overview.html"

    @method_decorator(dashboard_access_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        base = super().get_context_data(**kwargs)
        base.update(build_patients_overview_context())
        return base


class PatientDashboardView(TemplateView):
    """Detail dashboard for a single patient."""

    template_name = "dashboard/patients.html"

    @method_decorator(dashboard_access_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        base = super().get_context_data(**kwargs)
        patient_id = parse_patient_id(query_params=self.request.GET, kwargs=self.kwargs)
        base.update(build_patients_dashboard_context(patient_id=patient_id))
        base["selected_patient_id"] = patient_id

        patients_payload = build_patients_nav_payload(limit=50)
        base["patients"] = patients_payload
        base["patient_list"] = [
            {"id": p["patient_id"], "name": p["display_name"]} for p in patients_payload
        ]
        return base


class PatientDocumentDetailView(TemplateView):
    """Legacy/demo detail view for a patient document."""

    template_name = "dashboard/patient_document_detail.html"

    @method_decorator(dashboard_access_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        base = super().get_context_data(**kwargs)
        patient_id = int(self.kwargs.get("patient_id"))
        doc_id = int(self.kwargs.get("doc_id"))
        base.update(build_patient_document_detail_context(patient_id=patient_id, doc_id=doc_id))
        return base


class PatientPrescriptionDetailView(TemplateView):
    """Legacy/demo detail view for a patient prescription."""

    template_name = "dashboard/patient_prescription_detail.html"

    @method_decorator(dashboard_access_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        base = super().get_context_data(**kwargs)
        patient_id = int(self.kwargs.get("patient_id"))
        prescription_id = int(self.kwargs.get("prescription_id"))
        base.update(
            build_patient_prescription_detail_context(
                patient_id=patient_id,
                prescription_id=prescription_id,
            )
        )
        return base


class PatientDocumentUploadView(View):
    """Create/upload a patient document."""

    @method_decorator(dashboard_access_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, patient_id: int):
        title = (request.POST.get("title") or "").strip()
        doc_type = (request.POST.get("doc_type") or "").strip()
        note = (request.POST.get("note") or "").strip()
        file = request.FILES.get("file")

        try:
            create_patient_document(
                patient_id=patient_id,
                title=title,
                doc_type=doc_type,
                note=note,
                file=file,
            )
        except Exception:
            # Best-effort; keep UX stable.
            pass

        return redirect("dashboard:patient_detail", patient_id=patient_id)


class PatientNoteCreateView(View):
    """Create a patient note."""

    @method_decorator(dashboard_access_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, patient_id: int):
        content = (request.POST.get("content") or "").strip()
        if not content:
            return redirect("dashboard:patient_detail", patient_id=patient_id)

        user = getattr(request, "user", None)
        author_name = ""
        author_role = ""
        if user and getattr(user, "is_authenticated", False):
            try:
                author_name = (user.get_full_name() or "").strip()
            except Exception:
                author_name = ""

            author_name = (author_name or getattr(user, "username", "") or "").strip()
            role = getattr(user, "role", None)
            author_role = (getattr(role, "name", "") or "").strip()
            if not author_role:
                if getattr(user, "is_superuser", False):
                    author_role = "Admin"
                elif getattr(user, "is_staff", False):
                    author_role = "Staff"

        try:
            create_patient_note(
                patient_id=patient_id,
                author_name=author_name,
                author_role=author_role,
                content=content,
            )
        except Exception:
            pass

        return redirect("dashboard:patient_detail", patient_id=patient_id)


class PatientAPIView(View):
    """JSON API for patient dashboard data."""

    @method_decorator(dashboard_access_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, patient_id: int | None = None):
        return JsonResponse(build_patients_api_payload(patient_id=patient_id))


class PatientSearchView(View):
    """Simple JSON endpoint for patient search."""

    @method_decorator(dashboard_access_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        query = request.GET.get("q", "")
        return JsonResponse(search_patients_payload(query=query, limit=10))
