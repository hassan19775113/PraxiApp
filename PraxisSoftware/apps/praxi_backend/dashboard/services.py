"""Service layer for dashboard.

Goal: remove business logic from views by centralizing KPI/chart/widget assembly
and request parsing.

No new folders are introduced (Phase 3 constraint).
"""

from __future__ import annotations

import json
from datetime import timedelta

from django.db import OperationalError
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from praxi_backend.appointments.kpi import (
    calculate_patient_risk_score,
    calculate_patient_status,
    get_active_doctors,
    get_all_charts,
    get_all_doctor_charts,
    get_all_doctor_kpis,
    get_all_kpis,
    get_all_operations_charts,
    get_all_operations_kpis,
    get_all_patient_charts,
    get_all_patient_kpis,
    get_all_scheduling_charts,
    get_all_scheduling_kpis,
    get_doctor_comparison_data,
    get_doctor_profile,
    get_patient_overview_stats,
    get_patient_profile,
    get_realtime_operations_kpis,
)
from praxi_backend.appointments.models import Appointment, DoctorHours, Operation, Resource
from praxi_backend.appointments.serializers import ResourceSerializer
from praxi_backend.core.models import User
from praxi_backend.patients.models import Patient, PatientDocument, PatientNote

from .utils import get_patient_display_name
from .validators import parse_bool, parse_int, parse_optional_int, parse_period
from .widgets import build_kpi_cards, build_status_badges, build_utilization_bars


def build_main_dashboard_context() -> dict:
    """Build the context dict for the main dashboard HTML page."""
    kpis = get_all_kpis()
    charts = get_all_charts()
    return {
        "title": "PraxiApp Dashboard",
        "kpis": kpis,
        "kpi_cards": build_kpi_cards(kpis),
        "status_badges": build_status_badges(kpis),
        "utilization_bars": build_utilization_bars(kpis),
        "charts_json": json.dumps(charts),
        "heatmap_matrix": json.dumps(charts.get("hourly_heatmap", {}).get("matrix")),
    }


def build_main_dashboard_api_payload() -> dict:
    """Build JSON payload for dashboard AJAX refresh."""
    kpis = get_all_kpis()
    charts = get_all_charts()
    return {
        "kpis": kpis,
        "kpi_cards": build_kpi_cards(kpis),
        "status_badges": build_status_badges(kpis),
        "utilization_bars": build_utilization_bars(kpis),
        "charts": charts,
    }


# ---------------------------------------------------------------------------
# Scheduling dashboard services
# ---------------------------------------------------------------------------


def build_scheduling_dashboard_context() -> dict:
    """Build the context dict for the scheduling dashboard HTML page."""
    kpis = get_all_scheduling_kpis()
    charts = get_all_scheduling_charts()
    return {
        "title": "Scheduling KPIs",
        "kpis": kpis,
        "charts_json": json.dumps(charts),
        "heatmap_matrix": json.dumps((kpis.get("peak_load") or {}).get("matrix")),
        "funnel_data": json.dumps(charts.get("status_funnel")),
    }


def build_scheduling_api_payload() -> dict:
    """Build JSON payload for scheduling dashboard AJAX refresh."""
    kpis = get_all_scheduling_kpis()
    charts = get_all_scheduling_charts()
    return {"kpis": kpis, "charts": charts}


# ---------------------------------------------------------------------------
# Resources dashboard services
# ---------------------------------------------------------------------------


def build_resources_dashboard_context() -> dict:
    """Build the context dict for the resources/rooms dashboard HTML page."""
    resources = Resource.objects.using("default").filter(active=True).order_by("type", "name")
    rooms = [r for r in resources if r.type == Resource.TYPE_ROOM]
    devices = [r for r in resources if r.type == Resource.TYPE_DEVICE]

    rooms_data = [ResourceSerializer(r).data for r in rooms]
    devices_data = [ResourceSerializer(r).data for r in devices]

    return {
        "title": "Ressourcen & Räume",
        "rooms": rooms_data,
        "devices": devices_data,
        "rooms_json": json.dumps(rooms_data),
        "devices_json": json.dumps(devices_data),
    }


def parse_operations_request(query_params) -> tuple[int, str, bool]:
    """Parse common query params for operations dashboard/API."""
    days = parse_int(query_params.get("days"), default=30, min_value=1, max_value=366)
    mode = (query_params.get("mode") or "standard").strip().lower()
    include_charts = parse_bool(query_params.get("charts"), default=True)
    return days, mode, include_charts


def build_operations_dashboard_context(*, days: int, view_mode: str) -> tuple[dict, dict]:
    """Return (context, charts) for operations dashboard HTML."""
    if view_mode == "realtime":
        kpis = get_realtime_operations_kpis()
    else:
        kpis = get_all_operations_kpis(days=days)

    charts = get_all_operations_charts(days=days, kpis=kpis)
    context = {
        "title": "Operations-Dashboard",
        "period": kpis.get("period"),
        "selected_days": days,
        "view_mode": view_mode,
        "utilization": kpis.get("utilization"),
        "throughput": kpis.get("throughput"),
        "no_show": kpis.get("no_show"),
        "cancellation": kpis.get("cancellation"),
        "resources": kpis.get("resources"),
        "bottleneck": kpis.get("bottleneck"),
        "hourly": kpis.get("hourly"),
        "status_distribution": kpis.get("status_distribution"),
        "patient_flow": kpis.get("patient_flow"),
        "flow_times": kpis.get("flow_times"),
        "punctuality": kpis.get("punctuality"),
        "documentation": kpis.get("documentation"),
        "services": kpis.get("services"),
        "charts": charts,
        "charts_json": json.dumps(charts),
        "rooms": (kpis.get("resources") or {}).get("rooms"),
        "devices": (kpis.get("resources") or {}).get("devices"),
    }
    return context, charts


def build_operations_api_payload(*, days: int, mode: str, include_charts: bool) -> dict:
    if mode == "realtime":
        kpis = get_realtime_operations_kpis()
    else:
        kpis = get_all_operations_kpis(days=days)

    response_data = {"success": True, "mode": mode, "kpis": kpis}
    if include_charts:
        response_data["charts"] = get_all_operations_charts(days=days, kpis=kpis)
    return response_data


# ---------------------------------------------------------------------------
# Doctors dashboard services
# ---------------------------------------------------------------------------


def parse_doctors_dashboard_request(*, query_params, kwargs) -> tuple[int | None, str, int, str]:
    """Parse query params/kwargs for doctors dashboard.

    Returns (selected_doctor_id, period_key, days, period_label).
    """
    selected_doctor_id = parse_optional_int(query_params.get("doctor_id"))
    if selected_doctor_id is None:
        selected_doctor_id = parse_optional_int(kwargs.get("doctor_id"))

    days_override = parse_optional_int(query_params.get("days"))
    period, days, period_label = parse_period(query_params.get("period"), default="week")
    if days_override is not None and days_override > 0:
        days = int(days_override)
    return selected_doctor_id, period, days, period_label


def _doctor_full_name(u: User) -> str:
    name = (u.get_full_name() or "").strip()
    return name or getattr(u, "username", str(u.id))


def _normalize_doctor_title_and_name(name: str) -> tuple[str, str]:
    cleaned = (name or "").strip()
    lowered = cleaned.lower()
    if lowered.startswith("dr. "):
        cleaned = cleaned[4:].lstrip()
    elif lowered.startswith("dr "):
        cleaned = cleaned[3:].lstrip()
    return "Dr.", cleaned or name


def _doctor_initials(u: User) -> str:
    first = (getattr(u, "first_name", "") or "").strip()
    last = (getattr(u, "last_name", "") or "").strip()
    if first or last:
        return (first[:1] + last[:1]).upper()
    username = (getattr(u, "username", "") or "").strip()
    return (username[:2] or "DR").upper()


def _status_badge(status: str) -> tuple[str, str]:
    status = (status or "").lower()
    mapping = {
        "scheduled": ("info", "Geplant"),
        "confirmed": ("success", "Bestätigt"),
        "completed": ("neutral", "Abgeschlossen"),
        "cancelled": ("danger", "Storniert"),
    }
    return mapping.get(status, ("info", status or "—"))


def build_doctors_list_payload(doctors: list[User]) -> list[dict]:
    """Payload used by the doctors selector UI."""
    payload: list[dict] = []
    for d in doctors:
        payload.append(
            {
                "id": d.id,
                "full_name": _doctor_full_name(d),
                "name": (
                    get_doctor_profile(d).get("name") if d is not None else _doctor_full_name(d)
                ),
                "color": getattr(d, "calendar_color", None) or "#1E90FF",
            }
        )
    return payload


def build_doctors_dashboard_context(
    *,
    selected_doctor_id: int | None,
    days: int,
    period: str,
    period_label: str,
) -> dict:
    """Build context for `dashboard/doctors.html`.

    The template expects keys like: stats, doctors_list, doctors_overview,
    doctor_kpis, charts_json, schedule, upcoming_appointments.
    """
    doctors = get_active_doctors()
    doctor_ids = [d.id for d in doctors]

    tz = timezone.get_current_timezone()
    end_dt = timezone.now()
    start_dt = end_dt - timedelta(days=days)

    # Header KPIs
    appt_qs = Appointment.objects.using("default").filter(
        doctor_id__in=doctor_ids,
        start_time__gte=start_dt,
        start_time__lte=end_dt,
    )
    op_qs = (
        Operation.objects.using("default")
        .filter(start_time__gte=start_dt, start_time__lte=end_dt)
        .filter(
            Q(primary_surgeon_id__in=doctor_ids)
            | Q(assistant_id__in=doctor_ids)
            | Q(anesthesist_id__in=doctor_ids)
        )
    )

    comparison = get_doctor_comparison_data(days=days)
    avg_utilization = comparison.get("aggregates", {}).get("avg_utilization", 0)

    context: dict = {
        "doctors_list": build_doctors_list_payload(doctors),
        # Backward compatible key used elsewhere.
        "doctor_list": build_doctors_list_payload(doctors),
        "stats": {
            "active_doctors": len(doctors),
            "total_appointments": appt_qs.count(),
            "total_operations": op_qs.count(),
            "avg_utilization": avg_utilization,
        },
        "selected_doctor_id": selected_doctor_id,
        "period": period,
        "period_label": period_label,
    }

    # Detail view
    if selected_doctor_id is not None:
        kpis = get_all_doctor_kpis(selected_doctor_id, days=days)
        if "error" in kpis:
            context["error"] = kpis["error"]
            context["doctor"] = None
            context["title"] = "Ärzte-Dashboard"
            context["is_detail"] = True
            return context

        doctor_obj = (
            User.objects.using("default").filter(id=selected_doctor_id, role__name="doctor").first()
        )

        profile = kpis.get("profile", {})
        color = (
            profile.get("calendar_color")
            or (getattr(doctor_obj, "calendar_color", None) if doctor_obj else None)
            or "#1E90FF"
        )
        raw_name = _doctor_full_name(doctor_obj) if doctor_obj else profile.get("name", "Unbekannt")
        title, clean_name = _normalize_doctor_title_and_name(raw_name)

        context["doctor"] = {
            "id": selected_doctor_id,
            "title": title,
            "full_name": clean_name,
            "initials": _doctor_initials(doctor_obj) if doctor_obj else "DR",
            "specialty": getattr(doctor_obj, "specialty", None) or "Allgemeinmedizin",
            "email": getattr(doctor_obj, "email", "") if doctor_obj else "",
            "phone": getattr(doctor_obj, "phone", None) if doctor_obj else None,
            "color": color,
            "is_active": bool(getattr(doctor_obj, "is_active", True)) if doctor_obj else True,
        }

        op_count = (
            Operation.objects.using("default")
            .filter(start_time__gte=start_dt, start_time__lte=end_dt)
            .filter(
                Q(primary_surgeon_id=selected_doctor_id)
                | Q(assistant_id=selected_doctor_id)
                | Q(anesthesist_id=selected_doctor_id)
            )
            .count()
        )

        volume = kpis.get("volume", {})
        util = kpis.get("utilization", {})
        no_show = kpis.get("no_show", {})
        duration = kpis.get("duration", {})

        context["doctor_kpis"] = {
            "appointments": volume.get("total", 0),
            "completed": volume.get("completed", 0),
            "completion_rate": volume.get("completion_rate", 0),
            "operations": op_count,
            "utilization": util.get("utilization", 0),
            "no_shows": no_show.get("no_show_count", 0),
            "no_show_rate": no_show.get("no_show_rate", 0),
            "avg_duration": duration.get("avg_actual", 0) or duration.get("avg_planned", 0),
        }

        # Weekly schedule
        weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        hours_rows = list(
            DoctorHours.objects.using("default")
            .filter(doctor_id=selected_doctor_id, active=True)
            .order_by("weekday", "start_time", "id")
        )
        by_day: dict[int, list] = {i: [] for i in range(7)}
        for h in hours_rows:
            by_day[h.weekday].append(h)
        schedule: list[dict] = []
        for i in range(7):
            rows = by_day.get(i) or []
            if not rows:
                schedule.append({"name": weekdays[i], "active": False, "start": None, "end": None})
                continue
            start_t = min(r.start_time for r in rows)
            end_t = max(r.end_time for r in rows)
            schedule.append(
                {
                    "name": weekdays[i],
                    "active": True,
                    "start": start_t.strftime("%H:%M"),
                    "end": end_t.strftime("%H:%M"),
                }
            )
        context["schedule"] = schedule

        # Upcoming appointments
        now_local = timezone.localtime(timezone.now(), tz)
        upcoming = list(
            Appointment.objects.using("default")
            .filter(doctor_id=selected_doctor_id, start_time__gte=now_local)
            .select_related("type")
            .order_by("start_time", "id")[:25]
        )
        upcoming_payload: list[dict] = []
        for appt in upcoming:
            status_class, status_label = _status_badge(getattr(appt, "status", ""))
            type_obj = getattr(appt, "type", None)
            upcoming_payload.append(
                {
                    "patient_initials": f"P{str(getattr(appt, 'patient_id', '') or '')[:1]}" or "P",
                    "patient_name": f"Patient #{appt.patient_id}",
                    "type_name": getattr(type_obj, "name", None) or "Termin",
                    "type_color": getattr(type_obj, "color", None) or "#0078D4",
                    "status_class": status_class,
                    "status_label": status_label,
                    "date": timezone.localtime(appt.start_time, tz).isoformat(),
                }
            )
        context["upcoming_appointments"] = upcoming_payload

        # Minimal chart payloads expected by doctors.html
        daily = (
            Appointment.objects.using("default")
            .filter(doctor_id=selected_doctor_id, start_time__gte=start_dt, start_time__lte=end_dt)
            .annotate(day=TruncDate("start_time"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        labels = [d["day"].strftime("%Y-%m-%d") for d in daily]
        data = [d["count"] for d in daily]
        status_rows = (
            Appointment.objects.using("default")
            .filter(doctor_id=selected_doctor_id, start_time__gte=start_dt, start_time__lte=end_dt)
            .values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        s_labels = [r["status"] for r in status_rows]
        s_data = [r["count"] for r in status_rows]

        charts_min = {
            "appointments_per_day": {
                "labels": labels,
                "datasets": [{"label": "Termine", "data": data}],
            },
            "status_distribution": {
                "labels": s_labels,
                "datasets": [{"label": "Status", "data": s_data}],
            },
        }
        context["charts_json"] = json.dumps(charts_min)
        context["title"] = f"Ärzte-Dashboard: {context['doctor']['full_name']}"
        context["is_detail"] = True
        return context

    # Overview mode
    comparison_rows = comparison.get("doctors", [])
    comparison_by_id = {row.get("doctor_id"): row for row in comparison_rows}

    operation_counts: dict[int, int] = {d.id: 0 for d in doctors}
    base_ops = Operation.objects.using("default").filter(
        start_time__gte=start_dt, start_time__lte=end_dt
    )
    for field in ("primary_surgeon_id", "assistant_id", "anesthesist_id"):
        rows = base_ops.filter(**{f"{field}__in": doctor_ids}).values(field).annotate(c=Count("id"))
        for r in rows:
            doctor_id = r.get(field)
            if doctor_id is not None:
                operation_counts[int(doctor_id)] = operation_counts.get(int(doctor_id), 0) + int(
                    r.get("c") or 0
                )

    doctors_overview: list[dict] = []
    for d in doctors:
        row = comparison_by_id.get(d.id, {})
        doctors_overview.append(
            {
                "id": d.id,
                "full_name": _doctor_full_name(d),
                "initials": _doctor_initials(d),
                "specialty": getattr(d, "specialty", None) or "Allgemein",
                "appointments": row.get("appointments", 0),
                "operations": operation_counts.get(d.id, 0),
                "utilization": row.get("utilization", 0),
                "no_show_rate": row.get("no_show_rate", 0),
                "color": getattr(d, "calendar_color", None) or "#1E90FF",
            }
        )

    context["doctors_overview"] = doctors_overview
    context["charts_json"] = json.dumps(
        {
            "utilization_by_doctor": {
                "labels": [row["full_name"] for row in doctors_overview],
                "datasets": [
                    {
                        "label": "Auslastung (%)",
                        "data": [row["utilization"] for row in doctors_overview],
                    }
                ],
            }
        }
    )
    context["title"] = "Ärzte-Dashboard"
    context["is_detail"] = False
    return context


def build_doctors_api_payload(*, doctor_id: int | None, days: int) -> dict:
    """Build JSON payload for doctors dashboard AJAX API."""
    if doctor_id is not None:
        kpis = get_all_doctor_kpis(doctor_id, days=days)
        charts = get_all_doctor_charts(doctor_id=doctor_id, days=days)
        return {"success": ("error" not in kpis), "kpis": kpis, "charts": charts}

    comparison = get_doctor_comparison_data(days=days)
    charts = get_all_doctor_charts(days=days)
    return {"success": True, "comparison": comparison, "charts": charts}


def build_doctors_compare_context(
    *, doctor1_id: int | None, doctor2_id: int | None, days: int
) -> dict:
    """Build context for the optional doctors compare template."""
    context: dict = {}
    if doctor1_id is not None and doctor2_id is not None:
        context["doctor1"] = get_all_doctor_kpis(int(doctor1_id), days=days)
        context["doctor2"] = get_all_doctor_kpis(int(doctor2_id), days=days)
        context["comparison_mode"] = True
    else:
        context["comparison_mode"] = False

    context["doctor_list"] = [
        {"id": d.id, "name": get_doctor_profile(d).get("name")} for d in get_active_doctors()
    ]
    context["title"] = "Ärzte-Vergleich"
    context["selected_days"] = days
    return context


# ---------------------------------------------------------------------------
# Patients dashboard services
# ---------------------------------------------------------------------------


def parse_patient_id(*, query_params, kwargs) -> int | None:
    """Parse patient_id from URL kwargs or query params."""
    patient_id = parse_optional_int(kwargs.get("patient_id"))
    param = query_params.get("patient_id")
    if param not in (None, ""):
        parsed = parse_optional_int(param)
        if parsed is not None:
            patient_id = parsed
    return patient_id


def build_patients_overview_context() -> dict:
    """Build context for `dashboard/patients_overview.html`."""
    stats = get_patient_overview_stats()
    patient_list: list[dict] = []
    error_messages: list[str] = []

    # Primary source: managed Patient table.
    try:
        patients = Patient.objects.using("default").all().order_by("last_name", "first_name")[:100]
        for patient in patients:
            try:
                display_name = f"{patient.last_name}, {patient.first_name}"
                if patient.birth_date:
                    display_name += f" ({patient.birth_date.strftime('%d.%m.%Y')})"

                age = None
                if patient.birth_date:
                    today = timezone.localdate()
                    age = (
                        today.year
                        - patient.birth_date.year
                        - (
                            (today.month, today.day)
                            < (patient.birth_date.month, patient.birth_date.day)
                        )
                    )

                try:
                    status = calculate_patient_status(patient.id)
                    status_dict = {
                        "label": status.label,
                        "color": status.color,
                        "icon": status.icon,
                    }
                except Exception:
                    status_dict = {"label": "Unbekannt", "color": "#7A8A99", "icon": "○"}

                try:
                    risk = calculate_patient_risk_score(patient.id)
                    risk_dict = {
                        "score": risk["score"],
                        "level": risk["level"],
                        "color": risk["level_color"],
                    }
                except Exception:
                    risk_dict = {"score": 0, "level": "low", "color": "#6FCF97"}

                try:
                    profile = get_patient_profile(patient.id)
                    if profile and profile.get("age") and not age:
                        age = profile["age"]
                except Exception:
                    profile = None

                gender_normalized = patient.gender
                if gender_normalized:
                    gender_normalized = gender_normalized.lower()
                    if gender_normalized in ["female", "w", "weiblich"]:
                        gender_normalized = "W"
                    elif gender_normalized in ["male", "m", "männlich"]:
                        gender_normalized = "M"
                    else:
                        gender_normalized = "D"

                patient_list.append(
                    {
                        "id": patient.id,
                        "name": display_name,
                        "birth_date": patient.birth_date,
                        "age": age,
                        "gender": gender_normalized or "Unbekannt",
                        "status": status_dict,
                        "risk": risk_dict,
                    }
                )
            except Exception as e:
                error_messages.append(f"Patient {getattr(patient, 'id', '?')}: Fehler - {str(e)}")
    except Exception as e:
        error_messages.append(f"Patient DB Fehler: {str(e)}")

    # Fallback: derive patient IDs from appointments.
    if not patient_list:
        try:
            patient_ids = (
                Appointment.objects.using("default")
                .values_list("patient_id", flat=True)
                .distinct()[:100]
            )
            for patient_id in patient_ids:
                if not patient_id:
                    continue
                try:
                    status = calculate_patient_status(patient_id)
                    risk = calculate_patient_risk_score(patient_id)
                    profile = get_patient_profile(patient_id)
                    age = profile.get("age") if profile else None
                    patient_list.append(
                        {
                            "id": int(patient_id),
                            "name": get_patient_display_name(patient_id),
                            "birth_date": profile.get("birth_date") if profile else None,
                            "age": age,
                            "gender": profile.get("gender") if profile else None,
                            "status": {
                                "label": status.label,
                                "color": status.color,
                                "icon": status.icon,
                            },
                            "risk": {
                                "score": risk["score"],
                                "level": risk["level"],
                                "color": risk["level_color"],
                            },
                        }
                    )
                except Exception:
                    continue
        except Exception:
            pass

    ctx: dict = {"title": "Patienten-Übersicht", "stats": stats, "patients": patient_list}
    if error_messages:
        ctx["debug_errors"] = error_messages[:5]
    return ctx


def _build_uploaded_documents_payload(*, patient_id: int) -> list[dict]:
    try:
        uploaded_docs = list(
            PatientDocument.objects.using("default")
            .filter(patient_id=patient_id)
            .only("id", "title", "doc_type", "created_at", "file", "note")
        )
    except OperationalError:
        uploaded_docs = []

    payload: list[dict] = []
    for d in uploaded_docs:
        payload.append(
            {
                "id": d.id,
                "title": d.title,
                "kind": "Bericht" if d.doc_type == PatientDocument.DOC_TYPE_REPORT else "Dokument",
                "date": d.created_at.date().isoformat(),
                "source": "Upload",
                "url": d.file.url if d.file else None,
                "note": d.note,
            }
        )
    return payload


def _load_patient_notes(*, patient_id: int):
    try:
        return list(
            PatientNote.objects.using("default")
            .filter(patient_id=patient_id)
            .only("id", "author_name", "author_role", "content", "created_at")
        )
    except OperationalError:
        return []


def build_patient_detail_context(*, patient_id: int) -> dict:
    """Build the context block used by `dashboard/patients.html` for a single patient."""
    kpis = get_all_patient_kpis(patient_id)
    charts = get_all_patient_charts(patient_id)
    if "error" in kpis:
        return {"error": kpis["error"], "title": "Patienten-Dashboard"}

    uploaded_docs_payload = _build_uploaded_documents_payload(patient_id=patient_id)
    documents = uploaded_docs_payload + (kpis.get("documents", []) or [])
    documents.sort(key=lambda d: d.get("date", ""), reverse=True)
    reports = [d for d in documents if d.get("kind") == "Bericht"]

    notes = _load_patient_notes(patient_id=patient_id)

    ctx: dict = {
        "patient": kpis.get("profile"),
        "status": kpis.get("status"),
        "risk": kpis.get("risk"),
        "appointments": kpis.get("appointments"),
        "compliance": kpis.get("compliance"),
        "vitals": kpis.get("vitals"),
        "labs": kpis.get("labs"),
        "conditions": kpis.get("conditions"),
        "documents": documents,
        "reports": reports,
        "prescriptions": kpis.get("prescriptions", []),
        "charts": charts,
        "notes": notes,
        "charts_json": json.dumps(charts),
        "vitals_json": json.dumps(kpis.get("vitals")),
        "labs_json": json.dumps(kpis.get("labs")),
    }

    # Template compatibility: top KPI strip expects `kpis.*`.
    appt = kpis.get("appointments") or {}
    last_dt = (appt.get("last_appointment") or {}).get("date")
    next_dt = (appt.get("next_appointment") or {}).get("date")
    no_shows = int(appt.get("no_shows") or 0)
    past_done = int(appt.get("total_past") or 0)
    total_for_rate = max(1, past_done + no_shows)
    ctx["kpis"] = {
        "total_appointments": int(appt.get("total_past") or 0)
        + int(appt.get("future") or 0)
        + int(appt.get("cancelled") or 0),
        "last_visit": (last_dt or "")[:10] or None,
        "next_appointment": (next_dt or "")[:10] or None,
        "no_show_rate": round(no_shows / total_for_rate * 100, 1),
    }

    profile = kpis.get("profile") or {}
    ctx["allergies"] = profile.get("allergies") or []
    if profile.get("patient_id") is None:
        profile["patient_id"] = profile.get("id")
    status = kpis.get("status") or {}
    profile.setdefault("status", status.get("status"))
    profile.setdefault("status_label", status.get("label"))
    profile.setdefault("insurance_type", None)

    ctx["title"] = f"Patient: {profile.get('full_name', 'Unbekannt')}"
    return ctx


def build_patients_nav_payload(*, limit: int = 50) -> list[dict]:
    """Build the patient list used in the patient dashboard dropdown."""
    try:
        patients = (
            Patient.objects.using("default").all().order_by("last_name", "first_name", "id")
        )[:limit]
        payload = [
            {"patient_id": p.id, "display_name": f"{p.last_name}, {p.first_name}"} for p in patients
        ]
        if payload:
            return payload
    except Exception:
        pass

    ids = list(
        (
            Appointment.objects.using("default")
            .order_by()
            .values_list("patient_id", flat=True)
            .distinct()
        )[:limit]
    )
    ids = [int(pid) for pid in ids if pid is not None]
    return [{"patient_id": pid, "display_name": f"Patient #{pid}"} for pid in ids]


def build_patients_dashboard_context(*, patient_id: int | None) -> dict:
    """Build full context for patients dashboard view, including fallbacks."""
    if patient_id is None:
        ctx: dict = {
            "title": "Patienten-Dashboard",
            "error": "Bitte wählen Sie einen Patienten aus der Liste aus oder verwenden Sie /patients/overview/ für die Patientenliste.",
            "show_redirect_hint": True,
        }
        try:
            first_patient = Patient.objects.using("default").first()
            if first_patient:
                patient_id = first_patient.id
                ctx.update(build_patient_detail_context(patient_id=patient_id))
        except Exception as e:
            ctx["error"] = f"Fehler beim Laden: {str(e)}"
        return ctx

    return build_patient_detail_context(patient_id=patient_id)


def build_patients_api_payload(*, patient_id: int | None) -> dict:
    if patient_id is not None:
        kpis = get_all_patient_kpis(patient_id)
        charts = get_all_patient_charts(patient_id)
        return {"success": ("error" not in kpis), "kpis": kpis, "charts": charts}
    stats = get_patient_overview_stats()
    return {"success": True, "stats": stats}


def search_patients_payload(*, query: str, limit: int = 10) -> dict:
    query = (query or "").strip()
    if len(query) < 2:
        return {"results": []}
    try:
        patients = Patient.objects.using("default").filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )[:limit]
        results = [
            {
                "id": p.id,
                "name": f"{p.last_name}, {p.first_name}",
                "birth_date": p.birth_date.isoformat(),
            }
            for p in patients
        ]
        return {"results": results}
    except Exception as e:
        return {"error": str(e), "results": []}


def create_patient_document(
    *,
    patient_id: int,
    title: str,
    doc_type: str,
    note: str,
    file,
) -> None:
    """Persist an uploaded patient document (best-effort)."""
    if not title:
        return
    if doc_type not in (PatientDocument.DOC_TYPE_DOCUMENT, PatientDocument.DOC_TYPE_REPORT):
        doc_type = PatientDocument.DOC_TYPE_DOCUMENT
    PatientDocument.objects.using("default").create(
        patient_id=patient_id,
        title=title,
        doc_type=doc_type,
        note=note,
        file=file,
    )


def create_patient_note(
    *, patient_id: int, author_name: str, author_role: str, content: str
) -> None:
    if not content:
        return
    PatientNote.objects.using("default").create(
        patient_id=patient_id,
        author_name=(author_name or "").strip(),
        author_role=(author_role or "").strip(),
        content=content,
    )


def build_patient_document_detail_context(*, patient_id: int, doc_id: int) -> dict:
    """Build context for a single patient document detail page."""
    kpis = get_all_patient_kpis(patient_id)
    if "error" in kpis:
        return {"error": kpis["error"]}

    try:
        doc_obj = (
            PatientDocument.objects.using("default")
            .filter(patient_id=patient_id, id=doc_id)
            .first()
        )
    except OperationalError:
        doc_obj = None

    if doc_obj:
        document = {
            "id": doc_obj.id,
            "title": doc_obj.title,
            "kind": (
                "Bericht" if doc_obj.doc_type == PatientDocument.DOC_TYPE_REPORT else "Dokument"
            ),
            "date": doc_obj.created_at.date().isoformat(),
            "source": "Upload",
            "url": doc_obj.file.url if doc_obj.file else None,
            "note": doc_obj.note,
        }
    else:
        documents = kpis.get("documents", [])
        document = next((d for d in documents if int(d.get("id", -1)) == int(doc_id)), None)

    if not document:
        return {"error": "Dokument nicht gefunden"}

    return {
        "patient": kpis.get("profile"),
        "document": document,
        "title": f"Dokument: {document.get('title', 'Unbekannt')}",
    }


def build_patient_prescription_detail_context(*, patient_id: int, prescription_id: int) -> dict:
    """Build context for a single prescription detail page."""
    kpis = get_all_patient_kpis(patient_id)
    if "error" in kpis:
        return {"error": kpis["error"]}

    prescriptions = kpis.get("prescriptions", [])
    prescription = next(
        (p for p in prescriptions if int(p.get("id", -1)) == int(prescription_id)),
        None,
    )
    if not prescription:
        return {"error": "Rezept nicht gefunden"}

    return {
        "patient": kpis.get("profile"),
        "prescription": prescription,
        "title": f"Rezept: {prescription.get('medication', 'Unbekannt')}",
    }
