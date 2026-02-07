"""
Appointments App - Vollständige Admin-Registrierung
Alle 12 Models mit Premium-Badges und Inlines
"""

import calendar as pycalendar
from datetime import date, timedelta

from django import forms
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth import get_user_model
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from praxi_backend.core.admin import praxi_admin_site
from praxi_backend.patients.utils import get_patient_display_name

from .models import (
    Appointment,
    AppointmentResource,
    AppointmentType,
    DoctorAbsence,
    DoctorBreak,
    DoctorHours,
    Operation,
    OperationDevice,
    OperationType,
    PatientFlow,
    PracticeHours,
    Resource,
)


# ============================================================================
# Inline Classes
# ============================================================================
class AppointmentResourceInline(admin.TabularInline):
    """Inline für Termin-Ressourcen"""

    model = AppointmentResource
    extra = 0


class OperationDeviceInline(admin.TabularInline):
    """Inline für OP-Geräte"""

    model = OperationDevice
    extra = 0


class DoctorAbsenceInline(admin.TabularInline):
    """Inline für Arzt-Abwesenheiten"""

    model = DoctorAbsence
    extra = 0
    fields = ("start_date", "end_date", "reason", "active")


class DoctorBreakInline(admin.TabularInline):
    """Inline für Arzt-Pausen"""

    model = DoctorBreak
    extra = 0
    fields = ("date", "start_time", "end_time", "reason", "active")


class DoctorHoursInline(admin.TabularInline):
    """Inline für Arzt-Arbeitszeiten"""

    model = DoctorHours
    extra = 0
    fields = ("weekday", "start_time", "end_time", "active")


# ============================================================================
# AppointmentType Admin
# ============================================================================
@admin.register(AppointmentType, site=praxi_admin_site)
class AppointmentTypeAdmin(admin.ModelAdmin):
    """Admin für Termintypen"""

    list_display = ("name", "duration_badge", "color_preview", "active_badge", "created_at")
    list_filter = ("active", "created_at")
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 50

    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("📋 Termintyp", {"fields": ("name", "color", "duration_minutes", "active")}),
        ("📊 System", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def duration_badge(self, obj):
        """Dauer als Badge"""
        if not obj.duration_minutes:
            return mark_safe('<span style="color: #9AA0A6;">—</span>')

        if obj.duration_minutes < 30:
            color = "#34A853"
        elif obj.duration_minutes < 60:
            color = "#1A73E8"
        else:
            color = "#FBBC05"

        return format_html(
            '<span class="status-badge" style="background-color: {}; color: white;">'
            "⏱️ {} min</span>",
            color,
            obj.duration_minutes,
        )

    duration_badge.short_description = "Dauer"

    def color_preview(self, obj):
        """Farbvorschau"""
        return format_html(
            '<div style="width: 30px; height: 20px; background-color: {}; '
            'border-radius: 4px; border: 1px solid #ccc;"></div>',
            obj.color or "#2E8B57",
        )

    color_preview.short_description = "Farbe"

    def active_badge(self, obj):
        """Aktiv-Status"""
        if obj.active:
            return mark_safe(
                '<span class="status-badge" style="background-color: #34A853; color: white;">✅ Aktiv</span>'
            )
        return mark_safe(
            '<span class="status-badge" style="background-color: #9AA0A6; color: white;">⏸️ Inaktiv</span>'
        )

    active_badge.short_description = "Status"


# ============================================================================
# PracticeHours Admin
# ============================================================================
@admin.register(PracticeHours, site=praxi_admin_site)
class PracticeHoursAdmin(admin.ModelAdmin):
    """Admin für Praxis-Öffnungszeiten"""

    WEEKDAY_NAMES = {
        0: "Montag",
        1: "Dienstag",
        2: "Mittwoch",
        3: "Donnerstag",
        4: "Freitag",
        5: "Samstag",
        6: "Sonntag",
    }

    list_display = ("weekday_display", "time_range", "active_badge")
    list_filter = ("weekday", "active")
    ordering = ("weekday", "start_time")
    list_per_page = 50

    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("📅 Öffnungszeiten", {"fields": ("weekday", "start_time", "end_time", "active")}),
        ("📊 System", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def weekday_display(self, obj):
        """Wochentag als Text"""
        name = self.WEEKDAY_NAMES.get(obj.weekday, f"Tag {obj.weekday}")
        return format_html("<strong>{}</strong>", name)

    weekday_display.short_description = "Wochentag"

    def time_range(self, obj):
        """Zeitraum formatiert"""
        return format_html(
            '<span style="font-family: monospace; color: #1A73E8;">{} - {}</span>',
            obj.start_time.strftime("%H:%M"),
            obj.end_time.strftime("%H:%M"),
        )

    time_range.short_description = "Öffnungszeit"

    def active_badge(self, obj):
        if obj.active:
            return mark_safe('<span style="color: #34A853;">✅ Aktiv</span>')
        return mark_safe('<span style="color: #9AA0A6;">⏸️ Inaktiv</span>')

    active_badge.short_description = "Status"


# ============================================================================
# DoctorHours Admin
# ============================================================================
@admin.register(DoctorHours, site=praxi_admin_site)
class DoctorHoursAdmin(admin.ModelAdmin):
    """Admin für Arzt-Arbeitszeiten"""

    WEEKDAY_NAMES = {0: "Mo", 1: "Di", 2: "Mi", 3: "Do", 4: "Fr", 5: "Sa", 6: "So"}
    WEEKDAY_CHOICES = [
        (0, "Montag"),
        (1, "Dienstag"),
        (2, "Mittwoch"),
        (3, "Donnerstag"),
        (4, "Freitag"),
        (5, "Samstag"),
        (6, "Sonntag"),
    ]

    list_display = ("doctor_display", "weekday_display", "time_range", "active_badge")
    list_filter = ("doctor", "weekday", "active")
    search_fields = ("doctor__username", "doctor__first_name", "doctor__last_name")
    ordering = ("doctor", "weekday", "start_time")
    list_per_page = 100

    readonly_fields = ("id", "created_at", "updated_at")
    actions = ["remove_duplicate_hours"]

    class DoctorHoursForm(forms.ModelForm):
        class Meta:
            model = DoctorHours
            fields = "__all__"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            doctor_field = self.fields.get("doctor")
            if doctor_field is not None:
                doctor_field.label_from_instance = lambda u: u.get_full_name() or u.username
            weekday_field = self.fields.get("weekday")
            if weekday_field is not None:
                weekday_field.widget = forms.Select(choices=DoctorHoursAdmin.WEEKDAY_CHOICES)

    form = DoctorHoursForm

    def get_queryset(self, request):
        return super().get_queryset(request).distinct()

    def remove_duplicate_hours(self, request, queryset):
        all_rows = self.get_queryset(request).order_by(
            "doctor_id", "weekday", "start_time", "end_time", "active", "id"
        )
        seen = set()
        duplicates = []
        for row in all_rows:
            key = (row.doctor_id, row.weekday, row.start_time, row.end_time, row.active)
            if key in seen:
                duplicates.append(row.id)
            else:
                seen.add(key)
        deleted = 0
        if duplicates:
            deleted, _ = DoctorHours.objects.filter(id__in=duplicates).delete()
        self.message_user(request, f"Duplikate entfernt: {deleted}.")

    remove_duplicate_hours.short_description = "Duplikate entfernen (global)"

    def doctor_display(self, obj):
        doctor = getattr(obj, "doctor", None)
        if not doctor:
            return "—"
        return doctor.get_full_name() or doctor.username

    doctor_display.short_description = "Arzt"

    def weekday_display(self, obj):
        return self.WEEKDAY_NAMES.get(obj.weekday, str(obj.weekday))

    weekday_display.short_description = "Tag"

    def time_range(self, obj):
        return format_html(
            '<span style="font-family: monospace;">{} - {}</span>',
            obj.start_time.strftime("%H:%M"),
            obj.end_time.strftime("%H:%M"),
        )

    time_range.short_description = "Arbeitszeit"

    def active_badge(self, obj):
        if obj.active:
            return mark_safe('<span style="color: #34A853;">✅</span>')
        return mark_safe('<span style="color: #9AA0A6;">⏸️</span>')

    active_badge.short_description = "Aktiv"


# ============================================================================
# DoctorAbsence Admin
# ============================================================================
@admin.register(DoctorAbsence, site=praxi_admin_site)
class DoctorAbsenceAdmin(admin.ModelAdmin):
    """Admin für Arzt-Abwesenheiten"""

    class DoctorNameFilter(SimpleListFilter):
        title = "Arzt"
        parameter_name = "doctor"

        def lookups(self, request, model_admin):
            qs = model_admin.get_queryset(request).select_related("doctor")
            doctors = (
                qs.values_list(
                    "doctor_id", "doctor__first_name", "doctor__last_name", "doctor__username"
                )
                .distinct()
                .order_by("doctor__last_name", "doctor__first_name", "doctor__username")
            )
            options = []
            for doctor_id, first_name, last_name, username in doctors:
                if not doctor_id:
                    continue
                full_name = f"{first_name or ''} {last_name or ''}".strip()
                label = full_name or username or f"Arzt #{doctor_id}"
                options.append((str(doctor_id), label))
            return options

        def queryset(self, request, queryset):
            value = self.value()
            if value:
                return queryset.filter(doctor_id=value)
            return queryset

    class DoctorAbsenceForm(forms.ModelForm):
        REASON_CHOICES = [
            ("Urlaub", "Urlaub"),
            ("Krank", "Krank"),
            ("Kind krank", "Kind krank"),
            ("Unbezahlter Urlaub", "Unbezahlter Urlaub"),
            ("Fortbildung", "Fortbildung"),
            ("Dienstreise", "Dienstreise"),
            ("Sonstiges", "Sonstiges"),
        ]

        class Meta:
            model = DoctorAbsence
            fields = "__all__"
            widgets = {
                "start_date": forms.DateInput(attrs={"type": "date"}),
                "end_date": forms.DateInput(attrs={"type": "date"}),
                "return_date": forms.DateInput(attrs={"type": "date"}),
            }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            doctor_field = self.fields.get("doctor")
            if doctor_field is not None:
                doctor_field.label_from_instance = lambda u: u.get_full_name() or u.username
            reason_field = self.fields.get("reason")
            if reason_field is not None:
                reason_field.widget = forms.Select(choices=self.REASON_CHOICES)
                if reason_field.initial and reason_field.initial not in dict(self.REASON_CHOICES):
                    reason_field.widget.choices = [
                        (reason_field.initial, reason_field.initial)
                    ] + list(self.REASON_CHOICES)

    list_display = ("doctor_display", "date_range", "reason_display", "active_badge")
    list_filter = (DoctorNameFilter, "active", "start_date")
    search_fields = ("doctor__username", "doctor__first_name", "doctor__last_name", "reason")
    ordering = ("-start_date",)
    date_hierarchy = "start_date"
    list_per_page = 50

    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("👨‍⚕️ Arzt", {"fields": ("doctor",)}),
        (
            "📅 Abwesenheit",
            {
                "fields": (
                    "start_date",
                    "end_date",
                    "reason",
                    "duration_workdays",
                    "remaining_days",
                    "return_date",
                    "active",
                )
            },
        ),
        ("📊 System", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    form = DoctorAbsenceForm

    change_list_template = "admin/appointments/doctorabsence/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "calendar/",
                self.admin_site.admin_view(self.calendar_view),
                name="appointments_doctorabsence_calendar",
            ),
        ]
        return custom_urls + urls

    def calendar_view(self, request):
        today = timezone.localdate()
        try:
            year = int(request.GET.get("year", today.year))
            month = int(request.GET.get("month", today.month))
        except (TypeError, ValueError):
            year = today.year
            month = today.month

        if month < 1 or month > 12:
            month = today.month

        first_day = date(year, month, 1)
        days_in_month = pycalendar.monthrange(year, month)[1]
        last_day = date(year, month, days_in_month)
        dates = [first_day + timedelta(days=i) for i in range(days_in_month)]

        def shift_month(target_year, target_month, delta):
            new_month = target_month + delta
            new_year = target_year
            if new_month < 1:
                new_month = 12
                new_year -= 1
            elif new_month > 12:
                new_month = 1
                new_year += 1
            return new_year, new_month

        prev_year, prev_month = shift_month(year, month, -1)
        next_year, next_month = shift_month(year, month, 1)

        User = get_user_model()
        doctors = User.objects.filter(role__name="doctor").order_by(
            "last_name", "first_name", "username"
        )

        absences = DoctorAbsence.objects.select_related("doctor").filter(
            start_date__lte=last_day, end_date__gte=first_day, active=True
        )

        absence_map = {}
        for absence in absences:
            if not absence.doctor_id:
                continue
            absence_map.setdefault(absence.doctor_id, []).append(absence)

        calendar_rows = []
        for doctor in doctors:
            entries = []
            doctor_absences = absence_map.get(doctor.id, [])
            for day in dates:
                match = None
                for absence in doctor_absences:
                    if (
                        absence.start_date
                        and absence.end_date
                        and absence.start_date <= day <= absence.end_date
                    ):
                        match = absence
                        break
                entries.append(match)
            calendar_rows.append(
                {
                    "doctor": doctor,
                    "entries": entries,
                }
            )

        context = dict(
            self.admin_site.each_context(request),
            title="Abwesenheiten – Kalenderansicht",
            opts=self.model._meta,
            dates=dates,
            calendar_rows=calendar_rows,
            month_label=first_day.strftime("%B %Y"),
            prev_url=f"?year={prev_year}&month={prev_month}",
            next_url=f"?year={next_year}&month={next_month}",
            changelist_url=reverse(f"{self.admin_site.name}:appointments_doctorabsence_changelist"),
        )
        return self.render_calendar(request, context)

    def render_calendar(self, request, context):
        from django.shortcuts import render

        return render(request, "admin/appointments/doctorabsence/calendar.html", context)

    def date_range(self, obj):
        """Datumsbereich"""
        return format_html(
            '<span style="font-family: monospace;">{} → {}</span>',
            obj.start_date.strftime("%d.%m.%Y"),
            obj.end_date.strftime("%d.%m.%Y"),
        )

    date_range.short_description = "Zeitraum"

    def doctor_display(self, obj):
        doctor = getattr(obj, "doctor", None)
        if not doctor:
            return "—"
        return doctor.get_full_name() or doctor.username

    doctor_display.short_description = "Arzt"

    def reason_display(self, obj):
        if obj.reason:
            return obj.reason[:50] + "..." if len(obj.reason) > 50 else obj.reason
        return mark_safe('<span style="color: #9AA0A6; font-style: italic;">Kein Grund</span>')

    reason_display.short_description = "Grund"

    def active_badge(self, obj):
        if obj.active:
            return mark_safe('<span style="color: #34A853;">✅ Aktiv</span>')
        return mark_safe('<span style="color: #9AA0A6;">⏸️ Inaktiv</span>')

    active_badge.short_description = "Status"


# ============================================================================
# DoctorBreak Admin
# ============================================================================
@admin.register(DoctorBreak, site=praxi_admin_site)
class DoctorBreakAdmin(admin.ModelAdmin):
    """Admin für Arzt-Pausen"""

    list_display = ("date", "doctor_display", "time_range", "reason_display", "active_badge")
    list_filter = ("doctor", "active", "date")
    search_fields = ("doctor__username", "reason")
    ordering = ("-date", "start_time")
    date_hierarchy = "date"
    list_per_page = 50

    readonly_fields = ("id", "created_at", "updated_at")

    def doctor_display(self, obj):
        if obj.doctor:
            return obj.doctor.get_full_name() or obj.doctor.username
        return mark_safe('<span style="color: #1A73E8; font-weight: bold;">🏥 Praxisweit</span>')

    doctor_display.short_description = "Arzt"

    def time_range(self, obj):
        return format_html(
            '<span style="font-family: monospace;">{} - {}</span>',
            obj.start_time.strftime("%H:%M"),
            obj.end_time.strftime("%H:%M"),
        )

    time_range.short_description = "Zeit"

    def reason_display(self, obj):
        if obj.reason:
            return obj.reason[:30] + "..." if len(obj.reason) > 30 else obj.reason
        return mark_safe('<span style="color: #9AA0A6;">—</span>')

    reason_display.short_description = "Grund"

    def active_badge(self, obj):
        if obj.active:
            return mark_safe('<span style="color: #34A853;">✅</span>')
        return mark_safe('<span style="color: #9AA0A6;">⏸️</span>')

    active_badge.short_description = "Aktiv"


# ============================================================================
# Appointment Admin (Enhanced with Inline)
# ============================================================================
@admin.register(Appointment, site=praxi_admin_site)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin für Termine mit Ressourcen-Inline"""

    list_display = ("id", "patient_id", "doctor", "type", "time_display", "status_badge")
    list_filter = ("status", "doctor", "type", "start_time")
    search_fields = ("patient_id", "doctor__username", "notes")
    ordering = ("-start_time",)
    date_hierarchy = "start_time"
    list_per_page = 50

    inlines = [AppointmentResourceInline]

    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("👤 Patient & Arzt", {"fields": ("patient_id", "doctor", "type")}),
        ("📅 Termin", {"fields": ("start_time", "end_time", "status")}),
        ("📝 Notizen", {"fields": ("notes",), "classes": ("collapse",)}),
        ("📊 System", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def time_display(self, obj):
        """Termin formatiert"""
        if not obj.start_time:
            return mark_safe('<span style="color: #9AA0A6;">—</span>')

        start = obj.start_time.strftime("%d.%m.%Y %H:%M")
        end = obj.end_time.strftime("%H:%M") if obj.end_time else "?"

        return format_html(
            '<div style="line-height: 1.4;">'
            '<span style="color: #1A73E8; font-weight: 600;">{}</span><br>'
            '<span style="color: #5F6368; font-size: 11px;">bis {}</span>'
            "</div>",
            start,
            end,
        )

    time_display.short_description = "Zeitraum"

    def status_badge(self, obj):
        """Termin-Status als Badge"""
        status_map = {
            "scheduled": ("📅", "#1A73E8", "Geplant"),
            "confirmed": ("✔️", "#34A853", "Bestätigt"),
            "completed": ("✅", "#34A853", "Erledigt"),
            "cancelled": ("❌", "#EA4335", "Abgesagt"),
        }

        icon, color, label = status_map.get(obj.status, ("❓", "#5F6368", obj.status.upper()))

        return format_html(
            '<span class="status-badge" style="background-color: {}; color: white;">'
            "{} {}</span>",
            color,
            icon,
            label,
        )

    status_badge.short_description = "Status"


# ============================================================================
# Resource Admin
# ============================================================================
@admin.register(Resource, site=praxi_admin_site)
class ResourceAdmin(admin.ModelAdmin):
    """Admin für Ressourcen (Räume & Geräte)"""

    list_display = ("name", "type_badge", "active_badge", "color_preview")
    list_filter = ("type", "active")
    search_fields = ("name",)
    ordering = ("type", "name")
    list_per_page = 50

    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("🏥 Ressource", {"fields": ("name", "type", "color", "active")}),
        ("📊 System", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def type_badge(self, obj):
        """Ressourcentyp als Badge"""
        type_map = {
            "room": ("🏥", "#1A73E8", "Raum"),
            "device": ("🔬", "#34A853", "Gerät"),
        }

        icon, color, label = type_map.get(obj.type, ("❓", "#5F6368", obj.type.upper()))

        return format_html(
            '<span class="status-badge" style="background-color: {}; color: white;">'
            "{} {}</span>",
            color,
            icon,
            label,
        )

    type_badge.short_description = "Typ"

    def active_badge(self, obj):
        """Aktiv-Status als Badge"""
        if obj.active:
            return mark_safe('<span style="color: #34A853;">✅ Aktiv</span>')
        return mark_safe('<span style="color: #9AA0A6;">⏸️ Inaktiv</span>')

    active_badge.short_description = "Status"

    def color_preview(self, obj):
        """Farbvorschau"""
        return format_html(
            '<div style="width: 30px; height: 20px; background-color: {}; '
            'border-radius: 4px; border: 1px solid #ccc;"></div>',
            obj.color,
        )

    color_preview.short_description = "Farbe"


# ============================================================================
# AppointmentResource Admin
# ============================================================================
@admin.register(AppointmentResource, site=praxi_admin_site)
class AppointmentResourceAdmin(admin.ModelAdmin):
    """Admin für Termin-Ressourcen-Zuordnungen"""

    list_display = ("id", "appointment", "resource")
    list_filter = ("resource__type",)
    search_fields = ("appointment__id", "resource__name")
    ordering = ("-appointment__start_time",)
    list_per_page = 100

    readonly_fields = ("id",)


# ============================================================================
# OperationType Admin
# ============================================================================
@admin.register(OperationType, site=praxi_admin_site)
class OperationTypeAdmin(admin.ModelAdmin):
    """Admin für OP-Typen"""

    list_display = ("name", "duration_badge", "color_preview", "active_badge")
    search_fields = ("name",)
    list_filter = ("active",)
    ordering = ("name",)
    list_per_page = 50

    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("🏥 OP-Typ", {"fields": ("name", "color", "active")}),
        ("⏱️ Dauern (Minuten)", {"fields": ("prep_duration", "op_duration", "post_duration")}),
        ("📊 System", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def duration_badge(self, obj):
        """Gesamtdauer mit Farbcodierung"""
        total = obj.prep_duration + obj.op_duration + obj.post_duration

        if total < 60:
            color = "#34A853"
        elif total < 120:
            color = "#1A73E8"
        else:
            color = "#EA4335"

        return format_html(
            '<span class="status-badge" style="background-color: {}; color: white;">'
            "⏱️ {} min</span><br>"
            '<span style="font-size: 10px; color: #5F6368;">Vor: {} | OP: {} | Nach: {}</span>',
            color,
            total,
            obj.prep_duration,
            obj.op_duration,
            obj.post_duration,
        )

    duration_badge.short_description = "Dauer"

    def color_preview(self, obj):
        return format_html(
            '<div style="width: 30px; height: 20px; background-color: {}; '
            'border-radius: 4px; border: 1px solid #ccc;"></div>',
            obj.color,
        )

    color_preview.short_description = "Farbe"

    def active_badge(self, obj):
        if obj.active:
            return mark_safe('<span style="color: #34A853;">✅ Aktiv</span>')
        return mark_safe('<span style="color: #9AA0A6;">⏸️ Inaktiv</span>')

    active_badge.short_description = "Status"


# ============================================================================
# Operation Admin (with Device Inline)
# ============================================================================
@admin.register(Operation, site=praxi_admin_site)
class OperationAdmin(admin.ModelAdmin):
    """Admin für Operationen mit Geräte-Inline"""

    change_list_template = "admin/appointments/operation/change_list.html"

    class OperationForm(forms.ModelForm):
        class Meta:
            model = Operation
            fields = "__all__"
            widgets = {
                "start_time": forms.SplitDateTimeWidget(
                    date_attrs={"type": "date", "class": "prx-date"},
                    time_attrs={"type": "time", "class": "prx-time"},
                ),
                "end_time": forms.SplitDateTimeWidget(
                    date_attrs={"type": "date", "class": "prx-date"},
                    time_attrs={"type": "time", "class": "prx-time"},
                ),
            }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for field_name in ("primary_surgeon", "assistant", "anesthesist"):
                field = self.fields.get(field_name)
                if field is not None:
                    field.label_from_instance = lambda u: u.get_full_name() or u.username

    form = OperationForm

    list_display = (
        "id",
        "patient_display",
        "primary_surgeon_display",
        "op_type",
        "op_room",
        "time_display",
        "status_badge",
    )
    list_filter = ("status", "primary_surgeon", "op_type", "op_room", "start_time")
    search_fields = ("patient_id", "primary_surgeon__username", "notes")
    ordering = ("-start_time",)
    date_hierarchy = "start_time"
    list_per_page = 50

    inlines = [OperationDeviceInline]

    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("👤 Patient", {"fields": ("patient_id",)}),
        ("👨‍⚕️ OP-Team", {"fields": ("primary_surgeon", "assistant", "anesthesist")}),
        ("🏥 OP-Details", {"fields": ("op_type", "op_room")}),
        ("📅 Zeitraum", {"fields": ("start_time", "end_time", "status")}),
        ("📝 Notizen", {"fields": ("notes",), "classes": ("collapse",)}),
        ("📊 System", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            obj = self.get_object(request, object_id)
            if obj:
                op_type = getattr(getattr(obj, "op_type", None), "name", None) or "Operation"
                surgeon = getattr(
                    getattr(obj, "primary_surgeon", None), "get_full_name", lambda: ""
                )() or getattr(getattr(obj, "primary_surgeon", None), "username", "—")
                patient = (
                    get_patient_display_name(getattr(obj, "patient_id", None))
                    if getattr(obj, "patient_id", None)
                    else "—"
                )
                extra_context["title"] = f"OP #{obj.id} – {op_type} – {surgeon} – {patient}"
        return super().changeform_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "calendar/",
                self.admin_site.admin_view(self.calendar_view),
                name="appointments_operation_calendar",
            ),
        ]
        return custom_urls + urls

    def calendar_view(self, request):
        context = dict(
            self.admin_site.each_context(request),
            title="Operationen – Kalenderansicht",
            opts=self.model._meta,
            changelist_url=reverse(f"{self.admin_site.name}:appointments_operation_changelist"),
        )
        from django.shortcuts import render

        return render(request, "admin/appointments/operation/calendar.html", context)

    def patient_display(self, obj):
        if not obj.patient_id:
            return mark_safe('<span style="color: #9AA0A6;">—</span>')
        return get_patient_display_name(obj.patient_id)

    patient_display.short_description = "Patient"

    def primary_surgeon_display(self, obj):
        surgeon = getattr(obj, "primary_surgeon", None)
        if not surgeon:
            return mark_safe('<span style="color: #9AA0A6;">—</span>')
        return surgeon.get_full_name() or surgeon.username

    primary_surgeon_display.short_description = "Hauptoperateur"

    def time_display(self, obj):
        if not obj.start_time:
            return mark_safe('<span style="color: #9AA0A6;">—</span>')

        start = obj.start_time.strftime("%d.%m.%Y %H:%M")
        end = obj.end_time.strftime("%H:%M") if obj.end_time else "?"

        return format_html(
            '<div style="line-height: 1.4;">'
            '<span style="color: #1A73E8; font-weight: 600;">{}</span><br>'
            '<span style="color: #5F6368; font-size: 11px;">bis {}</span>'
            "</div>",
            start,
            end,
        )

    time_display.short_description = "Zeitraum"

    def status_badge(self, obj):
        status_map = {
            "planned": ("📋", "#5F6368", "Geplant"),
            "confirmed": ("✔️", "#1A73E8", "Bestätigt"),
            "running": ("🔴", "#EA4335", "Läuft"),
            "done": ("✅", "#34A853", "Erledigt"),
            "cancelled": ("❌", "#9AA0A6", "Abgesagt"),
        }

        icon, color, label = status_map.get(obj.status, ("❓", "#5F6368", obj.status.upper()))

        return format_html(
            '<span class="status-badge" style="background-color: {}; color: white;">'
            "{} {}</span>",
            color,
            icon,
            label,
        )

    status_badge.short_description = "Status"


# ============================================================================
# OperationDevice Admin
# ============================================================================
@admin.register(OperationDevice, site=praxi_admin_site)
class OperationDeviceAdmin(admin.ModelAdmin):
    """Admin für OP-Geräte-Zuordnungen"""

    list_display = ("id", "operation", "resource")
    list_filter = ("resource",)
    search_fields = ("operation__id", "resource__name")
    ordering = ("-operation__start_time",)
    list_per_page = 100

    readonly_fields = ("id",)


# ============================================================================
# PatientFlow Admin
# ============================================================================
@admin.register(PatientFlow, site=praxi_admin_site)
class PatientFlowAdmin(admin.ModelAdmin):
    """Admin für Patienten-Flow (Wartezeiten & Status)"""

    list_display = (
        "id",
        "appointment_display",
        "operation_display",
        "status_badge",
        "arrival_time_display",
        "status_changed_at",
    )
    list_filter = ("status", "status_changed_at")
    search_fields = ("appointment__id", "operation__id", "notes")
    ordering = ("-status_changed_at",)
    date_hierarchy = "status_changed_at"
    list_per_page = 50

    readonly_fields = ("id", "status_changed_at")

    fieldsets = (
        ("📋 Referenz", {"fields": ("appointment", "operation")}),
        ("🚶 Patienten-Status", {"fields": ("status", "arrival_time")}),
        ("📝 Notizen", {"fields": ("notes",), "classes": ("collapse",)}),
        ("📊 System", {"fields": ("id", "status_changed_at"), "classes": ("collapse",)}),
    )

    def appointment_display(self, obj):
        if obj.appointment:
            return format_html(
                '<a href="/praxi_backend/appointments/appointment/{}/change/" '
                'style="color: #1A73E8;">Termin #{}</a>',
                obj.appointment.id,
                obj.appointment.id,
            )
        return mark_safe('<span style="color: #9AA0A6;">—</span>')

    appointment_display.short_description = "Termin"

    def operation_display(self, obj):
        if obj.operation:
            return format_html(
                '<a href="/praxi_backend/appointments/operation/{}/change/" '
                'style="color: #1A73E8;">OP #{}</a>',
                obj.operation.id,
                obj.operation.id,
            )
        return mark_safe('<span style="color: #9AA0A6;">—</span>')

    operation_display.short_description = "Operation"

    def status_badge(self, obj):
        status_map = {
            "registered": ("📝", "#5F6368", "Angemeldet"),
            "waiting": ("⏳", "#FBBC05", "Wartend"),
            "preparing": ("🔧", "#1A73E8", "Vorbereitung"),
            "in_treatment": ("🏥", "#EA4335", "In Behandlung"),
            "post_treatment": ("🩹", "#9334E6", "Nachbehandlung"),
            "done": ("✅", "#34A853", "Fertig"),
        }

        icon, color, label = status_map.get(obj.status, ("❓", "#5F6368", obj.status.upper()))

        return format_html(
            '<span class="status-badge" style="background-color: {}; color: white;">'
            "{} {}</span>",
            color,
            icon,
            label,
        )

    status_badge.short_description = "Status"

    def arrival_time_display(self, obj):
        if obj.arrival_time:
            return obj.arrival_time.strftime("%d.%m.%Y %H:%M")
        return mark_safe('<span style="color: #9AA0A6;">—</span>')

    arrival_time_display.short_description = "Ankunft"
