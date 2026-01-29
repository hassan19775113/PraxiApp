"""
Assign fixed pastel calendar colors to doctors.

Usage:
    python manage.py update_doctor_colors
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

PASTEL_COLORS = [
    "#A8C7F4",
    "#A7D8CF",
    "#BFE6C8",
    "#F3E3B1",
    "#E7C3D3",
    "#C9D8F2",
    "#B7C9E6",
]


class Command(BaseCommand):
    help = "Set fixed calendar_color values for all doctors."

    def handle(self, *args, **options):
        User = get_user_model()

        doctors = User.objects.using("default").filter(role__name="doctor").order_by("id")

        if not doctors.exists():
            self.stdout.write("[INFO] Keine Ärzte gefunden.")
            return

        with transaction.atomic():
            updated = 0
            for idx, doctor in enumerate(doctors):
                color = PASTEL_COLORS[idx % len(PASTEL_COLORS)]
                if doctor.calendar_color != color:
                    doctor.calendar_color = color
                    doctor.save(update_fields=["calendar_color"])
                    updated += 1

        self.stdout.write(f"[OK] Aktualisiert: {updated} Arztfarben.")
