"""
Views für das Patienten-Dashboard.

Enthält:
- PatientOverviewView: Übersicht aller Patienten
- PatientDashboardView: Detail-Dashboard für einen Patienten
- PatientAPIView: JSON-API für AJAX-Anfragen
"""
from __future__ import annotations

import json

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect
from django.db import OperationalError
from django.views import View
from django.views.generic import TemplateView

from datetime import date

from praxi_backend.appointments.models import Appointment
from praxi_backend.patients.models import Patient
from praxi_backend.patients.models import PatientDocument, PatientNote

from .patient_kpis import (
    get_all_patient_kpis,
    get_patient_overview_stats,
    get_patient_profile,
    calculate_patient_status,
    calculate_patient_risk_score,
)
from .patient_charts import get_all_patient_charts


class PatientOverviewView(TemplateView):
    """
    Übersichtsseite mit Patientenliste und Schnellstatistiken.
    """
    template_name = 'dashboard/patients_overview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiken
        stats = get_patient_overview_stats()
        context['stats'] = stats
        
        # Patientenliste mit Status - mit Fallback-Logik
        from praxi_backend.dashboard.utils import get_patient_display_name
        import logging
        
        logger = logging.getLogger('praxi_backend.dashboard')
        patient_list = []
        error_messages = []
        
        # Single-DB: use managed patients on default.
        try:
            patients = Patient.objects.using('default').all().order_by('last_name', 'first_name')[:100]
            patient_count = patients.count()
            logger.debug(f"PatientOverviewView: Gefunden {patient_count} Patienten in default DB")

            for patient in patients:
                try:
                    display_name = f"{patient.last_name}, {patient.first_name}"
                    if patient.birth_date:
                        display_name += f" ({patient.birth_date.strftime('%d.%m.%Y')})"

                    age = None
                    if patient.birth_date:
                        today = date.today()
                        age = today.year - patient.birth_date.year - (
                            (today.month, today.day) < (patient.birth_date.month, patient.birth_date.day)
                        )

                    try:
                        status = calculate_patient_status(patient.id)
                        status_dict = {
                            'label': status.label,
                            'color': status.color,
                            'icon': status.icon,
                        }
                    except Exception:
                        status_dict = {
                            'label': 'Unbekannt',
                            'color': '#7A8A99',
                            'icon': '○',
                        }

                    try:
                        risk = calculate_patient_risk_score(patient.id)
                        risk_dict = {
                            'score': risk['score'],
                            'level': risk['level'],
                            'color': risk['level_color'],
                        }
                    except Exception:
                        risk_dict = {
                            'score': 0,
                            'level': 'low',
                            'color': '#6FCF97',
                        }

                    try:
                        profile = get_patient_profile(patient.id)
                        if profile and profile.get('age') and not age:
                            age = profile['age']
                    except Exception:
                        profile = None

                    gender_normalized = patient.gender
                    if gender_normalized:
                        gender_normalized = gender_normalized.lower()
                        if gender_normalized in ['female', 'w', 'weiblich']:
                            gender_normalized = 'W'
                        elif gender_normalized in ['male', 'm', 'männlich']:
                            gender_normalized = 'M'
                        else:
                            gender_normalized = 'D'

                    patient_list.append({
                        'id': patient.id,
                        'name': display_name,
                        'birth_date': patient.birth_date,
                        'age': age,
                        'gender': gender_normalized or 'Unbekannt',
                        'status': status_dict,
                        'risk': risk_dict,
                    })
                except Exception as e:
                    error_messages.append(f"Patient {patient.id}: Fehler - {str(e)}")
        except Exception as e:
            error_messages.append(f"Patient DB Fehler: {str(e)}")
        
        # Zweiter Fallback: Patienten aus Appointments
        if not patient_list:
            try:
                patient_ids = (
                    Appointment.objects.using('default')
                    .values_list('patient_id', flat=True)
                    .distinct()[:100]
                )
                
                for patient_id in patient_ids:
                    if not patient_id:
                        continue
                    try:
                        status = calculate_patient_status(patient_id)
                        risk = calculate_patient_risk_score(patient_id)
                        profile = get_patient_profile(patient_id)
                        
                        display_name = get_patient_display_name(patient_id)
                        age = profile['age'] if profile and profile.get('age') else None
                        
                        patient_list.append({
                            'id': patient_id,
                            'name': display_name,
                            'birth_date': profile.get('birth_date') if profile else None,
                            'age': age,
                            'gender': profile.get('gender') if profile else None,
                            'status': {
                                'label': status.label,
                                'color': status.color,
                                'icon': status.icon,
                            },
                            'risk': {
                                'score': risk['score'],
                                'level': risk['level'],
                                'color': risk['level_color'],
                            },
                        })
                    except Exception:
                        continue
            except Exception:
                pass
        
        context['patients'] = patient_list
        context['title'] = 'Patienten-Übersicht'
        
        # Debug-Informationen (nur in Development)
        if error_messages:
            context['debug_errors'] = error_messages[:5]  # Nur erste 5 Fehler anzeigen
            logger.warning(f"PatientOverviewView: {len(error_messages)} Fehler beim Laden der Patienten")
        
        print(f"[INFO] PatientOverviewView: {len(patient_list)} Patienten werden angezeigt")
        logger.info(f"PatientOverviewView: {len(patient_list)} Patienten werden angezeigt")
        
        return context


class PatientDashboardView(TemplateView):
    """
    Detail-Dashboard für einen einzelnen Patienten.
    """
    template_name = 'dashboard/patients.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Support both /patients/<id>/ and /patients/?patient_id=<id>
        patient_id = self.kwargs.get('patient_id')
        patient_id_param = self.request.GET.get('patient_id')
        if patient_id_param not in (None, ''):
            try:
                patient_id = int(patient_id_param)
            except (TypeError, ValueError):
                pass
        
        if patient_id:
            # Einzelpatient-Dashboard
            kpis = get_all_patient_kpis(patient_id)
            charts = get_all_patient_charts(patient_id)
            
            if 'error' in kpis:
                context['error'] = kpis['error']
            else:
                context['patient'] = kpis['profile']
                context['status'] = kpis['status']
                context['risk'] = kpis['risk']
                context['appointments'] = kpis['appointments']
                context['compliance'] = kpis['compliance']
                context['vitals'] = kpis['vitals']
                context['labs'] = kpis['labs']
                context['conditions'] = kpis['conditions']
                try:
                    uploaded_docs = list(
                        PatientDocument.objects.filter(patient_id=patient_id)
                        .only("id", "title", "doc_type", "created_at", "file", "note")
                    )
                except OperationalError:
                    uploaded_docs = []
                uploaded_docs_payload = [
                    {
                        "id": d.id,
                        "title": d.title,
                        "kind": "Bericht" if d.doc_type == PatientDocument.DOC_TYPE_REPORT else "Dokument",
                        "date": d.created_at.date().isoformat(),
                        "source": "Upload",
                        "url": d.file.url if d.file else None,
                        "note": d.note,
                    }
                    for d in uploaded_docs
                ]

                documents = uploaded_docs_payload + (kpis.get("documents", []) or [])
                documents.sort(key=lambda d: d.get("date", ""), reverse=True)
                reports = [d for d in documents if d.get("kind") == "Bericht"]

                context['documents'] = documents
                context['reports'] = reports
                context['prescriptions'] = kpis.get('prescriptions', [])
                context['charts'] = charts
                try:
                    notes = list(
                        PatientNote.objects.filter(patient_id=patient_id)
                        .only("id", "author_name", "author_role", "content", "created_at")
                    )
                except OperationalError:
                    notes = []
                context["notes"] = notes

                # JSON für JavaScript
                context['charts_json'] = json.dumps(charts)
                context['vitals_json'] = json.dumps(kpis['vitals'])
                context['labs_json'] = json.dumps(kpis['labs'])

                # Template compatibility: top KPI strip expects `kpis.*`.
                appt = kpis.get('appointments') or {}
                last_dt = (appt.get('last_appointment') or {}).get('date')
                next_dt = (appt.get('next_appointment') or {}).get('date')
                no_shows = int(appt.get('no_shows') or 0)
                past_done = int(appt.get('total_past') or 0)
                total_for_rate = max(1, past_done + no_shows)
                context['kpis'] = {
                    'total_appointments': int(appt.get('total_past') or 0)
                    + int(appt.get('future') or 0)
                    + int(appt.get('cancelled') or 0),
                    'last_visit': (last_dt or '')[:10] or None,
                    'next_appointment': (next_dt or '')[:10] or None,
                    'no_show_rate': round(no_shows / total_for_rate * 100, 1),
                }

                # Template expects allergies as separate variable.
                profile = kpis.get('profile') or {}
                context['allergies'] = profile.get('allergies') or []

                # Ensure profile has a patient_id key used in template.
                if profile.get('patient_id') is None:
                    profile['patient_id'] = profile.get('id')

                # Provide status fields directly on patient dict for template.
                status = kpis.get('status') or {}
                profile.setdefault('status', status.get('status'))
                profile.setdefault('status_label', status.get('label'))
                profile.setdefault('insurance_type', None)
                
            
            context['title'] = f"Patient: {kpis.get('profile', {}).get('full_name', 'Unbekannt')}"
        else:
            # Keine patient_id: Redirect zur Übersicht oder zeige leere Liste
            # Die Patientenliste sollte über /patients/overview/ aufgerufen werden
            context['title'] = 'Patienten-Dashboard'
            context['error'] = 'Bitte wählen Sie einen Patienten aus der Liste aus oder verwenden Sie /patients/overview/ für die Patientenliste.'
            context['show_redirect_hint'] = True
            # Fallback: Zeige ersten Patienten oder Demo
            try:
                first_patient = Patient.objects.using('default').first()
                if first_patient:
                    patient_id = first_patient.id
                    kpis = get_all_patient_kpis(patient_id)
                    charts = get_all_patient_charts(patient_id)
                    
                    context['patient'] = kpis['profile']
                    context['status'] = kpis['status']
                    context['risk'] = kpis['risk']
                    context['appointments'] = kpis['appointments']
                    context['compliance'] = kpis['compliance']
                    context['vitals'] = kpis['vitals']
                    context['labs'] = kpis['labs']
                    context['conditions'] = kpis['conditions']
                    try:
                        uploaded_docs = list(
                            PatientDocument.objects.filter(patient_id=patient_id)
                            .only("id", "title", "doc_type", "created_at", "file", "note")
                        )
                    except OperationalError:
                        uploaded_docs = []
                    uploaded_docs_payload = [
                        {
                            "id": d.id,
                            "title": d.title,
                            "kind": "Bericht" if d.doc_type == PatientDocument.DOC_TYPE_REPORT else "Dokument",
                            "date": d.created_at.date().isoformat(),
                            "source": "Upload",
                            "url": d.file.url if d.file else None,
                            "note": d.note,
                        }
                        for d in uploaded_docs
                    ]

                    documents = uploaded_docs_payload + (kpis.get("documents", []) or [])
                    documents.sort(key=lambda d: d.get("date", ""), reverse=True)
                    reports = [d for d in documents if d.get("kind") == "Bericht"]

                    context['documents'] = documents
                    context['reports'] = reports
                    context['prescriptions'] = kpis.get('prescriptions', [])
                    context['charts'] = charts
                    try:
                        notes = list(
                            PatientNote.objects.filter(patient_id=patient_id)
                            .only("id", "author_name", "author_role", "content", "created_at")
                        )
                    except OperationalError:
                        notes = []
                    context["notes"] = notes
                    context['charts_json'] = json.dumps(charts)
                    context['vitals_json'] = json.dumps(kpis['vitals'])
                    context['labs_json'] = json.dumps(kpis['labs'])
                    context['title'] = f"Patient: {kpis['profile']['full_name']}"

                    appt = kpis.get('appointments') or {}
                    last_dt = (appt.get('last_appointment') or {}).get('date')
                    next_dt = (appt.get('next_appointment') or {}).get('date')
                    no_shows = int(appt.get('no_shows') or 0)
                    past_done = int(appt.get('total_past') or 0)
                    total_for_rate = max(1, past_done + no_shows)
                    context['kpis'] = {
                        'total_appointments': int(appt.get('total_past') or 0)
                        + int(appt.get('future') or 0)
                        + int(appt.get('cancelled') or 0),
                        'last_visit': (last_dt or '')[:10] or None,
                        'next_appointment': (next_dt or '')[:10] or None,
                        'no_show_rate': round(no_shows / total_for_rate * 100, 1),
                    }

                    profile = kpis.get('profile') or {}
                    context['allergies'] = profile.get('allergies') or []
                    if profile.get('patient_id') is None:
                        profile['patient_id'] = profile.get('id')
                    status = kpis.get('status') or {}
                    profile.setdefault('status', status.get('status'))
                    profile.setdefault('status_label', status.get('label'))
                    profile.setdefault('insurance_type', None)
                else:
                    context['error'] = 'Keine Patienten vorhanden'
                    context['title'] = 'Patienten-Dashboard'
            except Exception as e:
                context['error'] = f'Fehler beim Laden: {str(e)}'
                context['title'] = 'Patienten-Dashboard'

        context['selected_patient_id'] = patient_id

        # Patientenliste für Dropdown / Seitennavigation.
        patients_payload: list[dict] = []
        try:
            patients = (
                Patient.objects.using('default')
                .all()
                .order_by('last_name', 'first_name', 'id')
            )[:50]
            patients_payload = [
                {'patient_id': p.id, 'display_name': f"{p.last_name}, {p.first_name}"}
                for p in patients
            ]
        except Exception:
            patients_payload = []

        if not patients_payload:
            ids = list(
                (
                    Appointment.objects.using('default')
                    .order_by()
                    .values_list('patient_id', flat=True)
                    .distinct()
                )[:50]
            )
            ids = [int(pid) for pid in ids if pid is not None]

            if ids:
                name_by_id: dict[int, str] = {}
                patients_payload = [
                    {
                        'patient_id': pid,
                        'display_name': name_by_id.get(pid, f"Patient #{pid}"),
                    }
                    for pid in ids
                ]
            else:
                patients_payload = []

        context['patients'] = patients_payload
        context['patient_list'] = [
            {'id': p['patient_id'], 'name': p['display_name']}
            for p in patients_payload
        ]
        
        return context


class PatientDocumentDetailView(TemplateView):
    """
    Detailansicht für ein Patientendokument (Demo/Legacy).
    """
    template_name = 'dashboard/patient_document_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient_id = self.kwargs.get('patient_id')
        doc_id = self.kwargs.get('doc_id')

        kpis = get_all_patient_kpis(patient_id)
        if 'error' in kpis:
            context['error'] = kpis['error']
            return context

        try:
            doc_obj = PatientDocument.objects.filter(patient_id=patient_id, id=doc_id).first()
        except OperationalError:
            doc_obj = None
        if doc_obj:
            document = {
                "id": doc_obj.id,
                "title": doc_obj.title,
                "kind": "Bericht" if doc_obj.doc_type == PatientDocument.DOC_TYPE_REPORT else "Dokument",
                "date": doc_obj.created_at.date().isoformat(),
                "source": "Upload",
                "url": doc_obj.file.url if doc_obj.file else None,
                "note": doc_obj.note,
            }
        else:
            documents = kpis.get('documents', [])
            document = next((d for d in documents if int(d.get('id', -1)) == int(doc_id)), None)
        if not document:
            context['error'] = 'Dokument nicht gefunden'
            return context

        context['patient'] = kpis.get('profile')
        context['document'] = document
        context['title'] = f"Dokument: {document.get('title', 'Unbekannt')}"
        return context


class PatientPrescriptionDetailView(TemplateView):
    """
    Detailansicht für ein Patientenrezept (Demo/Legacy).
    """
    template_name = 'dashboard/patient_prescription_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient_id = self.kwargs.get('patient_id')
        prescription_id = self.kwargs.get('prescription_id')

        kpis = get_all_patient_kpis(patient_id)
        if 'error' in kpis:
            context['error'] = kpis['error']
            return context

        prescriptions = kpis.get('prescriptions', [])
        prescription = next(
            (p for p in prescriptions if int(p.get('id', -1)) == int(prescription_id)),
            None,
        )
        if not prescription:
            context['error'] = 'Rezept nicht gefunden'
            return context

        context['patient'] = kpis.get('profile')
        context['prescription'] = prescription
        context['title'] = f"Rezept: {prescription.get('medication', 'Unbekannt')}"
        return context


class PatientDocumentUploadView(View):
    """
    Upload/Create a patient document.
    """

    def post(self, request, patient_id: int):
        title = (request.POST.get("title") or "").strip()
        doc_type = (request.POST.get("doc_type") or "").strip()
        note = (request.POST.get("note") or "").strip()
        file = request.FILES.get("file")

        if not title:
            return redirect("dashboard:patient_detail", patient_id=patient_id)

        if doc_type not in (
            PatientDocument.DOC_TYPE_DOCUMENT,
            PatientDocument.DOC_TYPE_REPORT,
        ):
            doc_type = PatientDocument.DOC_TYPE_DOCUMENT

        try:
            PatientDocument.objects.create(
                patient_id=patient_id,
                title=title,
                doc_type=doc_type,
                note=note,
                file=file,
            )
        except OperationalError:
            return redirect("dashboard:patient_detail", patient_id=patient_id)

        return redirect("dashboard:patient_detail", patient_id=patient_id)


class PatientNoteCreateView(View):
    """
    Create a new patient note.
    """

    def post(self, request, patient_id: int):
        content = (request.POST.get("content") or "").strip()
        if not content:
            return redirect("dashboard:patient_detail", patient_id=patient_id)

        user = getattr(request, "user", None)
        author_name = ""
        author_role = ""
        if user and getattr(user, "is_authenticated", False):
            full_name = ""
            try:
                full_name = user.get_full_name()
            except Exception:
                full_name = ""
            author_name = (full_name or getattr(user, "username", "") or "").strip()
            role = getattr(user, "role", None)
            author_role = (getattr(role, "name", "") or "").strip()
            if not author_role:
                if getattr(user, "is_superuser", False):
                    author_role = "Admin"
                elif getattr(user, "is_staff", False):
                    author_role = "Staff"

        try:
            PatientNote.objects.create(
                patient_id=patient_id,
                author_name=author_name,
                author_role=author_role,
                content=content,
            )
        except OperationalError:
            return redirect("dashboard:patient_detail", patient_id=patient_id)

        return redirect("dashboard:patient_detail", patient_id=patient_id)


class PatientAPIView(View):
    """
    JSON-API für Patienten-Dashboard-Daten.
    """
    
    def get(self, request, patient_id: int | None = None):
        if patient_id:
            # Einzelpatient
            kpis = get_all_patient_kpis(patient_id)
            charts = get_all_patient_charts(patient_id)
            
            return JsonResponse({
                'success': 'error' not in kpis,
                'kpis': kpis,
                'charts': charts,
            })
        else:
            # Übersicht
            stats = get_patient_overview_stats()
            
            return JsonResponse({
                'success': True,
                'stats': stats,
            })


class PatientSearchView(View):
    """
    API für Patientensuche.
    """
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'results': []})
        
        try:
            patients = Patient.objects.using('default').filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )[:10]
            
            results = [
                {
                    'id': p.id,
                    'name': f"{p.last_name}, {p.first_name}",
                    'birth_date': p.birth_date.isoformat(),
                }
                for p in patients
            ]
            
            return JsonResponse({'results': results})
        except Exception as e:
            return JsonResponse({'error': str(e), 'results': []})
