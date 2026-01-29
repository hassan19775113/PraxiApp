"""Patients admin.

After removing the dual-DB setup, patients are now managed in the default DB.
"""

from django.contrib import admin
from django.utils.html import format_html
from praxi_backend.core.admin import praxi_admin_site
from praxi_backend.patients.models import Patient


@admin.register(Patient, site=praxi_admin_site)
class PatientAdmin(admin.ModelAdmin):
    """Admin for managed patients (default DB)."""

    list_display = (
        "id",
        "patient_id_badge",
        "full_name",
        "birth_date",
        "age_display",
        "created_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("id", "first_name", "last_name", "email", "phone")
    ordering = ("last_name", "first_name")
    list_per_page = 50

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "👤 Patientendaten",
            {"fields": ("id", "first_name", "last_name", "birth_date", "gender")},
        ),
        (
            "📞 Kontakt",
            {
                "fields": ("phone", "email"),
                "classes": ("collapse",),
            },
        ),
        ("📊 System", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def patient_id_badge(self, obj):
        """Patient-ID als Badge"""
        return format_html(
            '<span style="font-family: monospace; background-color: #1A73E8; '
            'color: white; padding: 2px 8px; border-radius: 4px;">#{}</span>',
            obj.id,
        )

    patient_id_badge.short_description = "Patient-ID"

    def full_name(self, obj):
        """Vollständiger Name"""
        return format_html(
            '<strong style="color: #1A73E8;">{}, {}</strong>', obj.last_name, obj.first_name
        )

    full_name.short_description = "Name"

    def age_display(self, obj):
        """Alter berechnen"""
        from datetime import date

        if not obj.birth_date:
            return format_html('<span style="color: #5F6368;">–</span>')

        today = date.today()
        age = (
            today.year
            - obj.birth_date.year
            - ((today.month, today.day) < (obj.birth_date.month, obj.birth_date.day))
        )
        return format_html('<span style="color: #5F6368;">{} Jahre</span>', age)

    age_display.short_description = "Alter"
