"""Availability helper endpoint.

Moved from `praxi_backend.appointments.views` in Phase 2B.
No logic changes; only module split.
"""

from __future__ import annotations

import logging
from datetime import datetime

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .scheduling_facade import filter_available_patients, get_available_doctors, get_available_rooms

logger = logging.getLogger(__name__)


class AvailabilityView(generics.GenericAPIView):
    """GET /api/availability/?start=ISO_DATETIME&end=ISO_DATETIME

    Returns available doctors, rooms, and patients for a given time range.

    Query Parameters:
            start: ISO datetime string (required)
            end: ISO datetime string (required)
            exclude_appointment_id: Optional appointment ID to exclude (for updates)

    Response:
            {
                    "available_doctors": [
                            {"id": 1, "name": "Dr. ...", "calendar_color": "#..."},
                            ...
                    ],
                    "available_rooms": [
                            {"id": 1, "name": "Raum 1", "type": "room"},
                            ...
                    ],
                    "available_patients": [
                            {"id": 1, "first_name": "...", "last_name": "..."},
                            ...
                    ]
            }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Parse start and end times
        start_str = request.query_params.get("start")
        end_str = request.query_params.get("end")
        exclude_appointment_id = request.query_params.get("exclude_appointment_id")

        if not start_str or not end_str:
            return Response(
                {"detail": "start and end query parameters are required (ISO datetime format)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError) as e:
            return Response(
                {"detail": f"Invalid datetime format: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure timezone-aware
        if not timezone.is_aware(start_time):
            start_time = timezone.make_aware(start_time, timezone.get_current_timezone())
        if not timezone.is_aware(end_time):
            end_time = timezone.make_aware(end_time, timezone.get_current_timezone())

        # Validate times
        if end_time <= start_time:
            return Response(
                {"detail": "end_time must be after start_time"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exclude_id = None
        if exclude_appointment_id:
            try:
                exclude_id = int(exclude_appointment_id)
            except (ValueError, TypeError):
                pass

        # Get available doctors
        available_doctors = get_available_doctors(
            start_time=start_time,
            end_time=end_time,
            exclude_appointment_id=exclude_id,
        )

        # Serialize doctors
        from .scheduling_facade import doctor_display_name

        doctors_data = [
            {
                "id": d.id,
                "name": doctor_display_name(d),
                "calendar_color": getattr(d, "calendar_color", None),
            }
            for d in available_doctors
        ]

        # Get available rooms
        available_rooms = get_available_rooms(
            start_time=start_time,
            end_time=end_time,
            exclude_appointment_id=exclude_id,
        )

        # Serialize rooms
        rooms_data = [
            {
                "id": r.id,
                "name": r.name,
                "type": r.type,
            }
            for r in available_rooms
        ]

        # Get available patients
        try:
            from praxi_backend.patients.models import Patient

            all_patients = list(
                Patient.objects.using("default").order_by("last_name", "first_name", "id")
            )
            all_patient_ids = [p.id for p in all_patients]

            # Filter available patients
            available_patient_ids = filter_available_patients(
                patient_ids=all_patient_ids,
                start_time=start_time,
                end_time=end_time,
                exclude_appointment_id=exclude_id,
            )

            # Get patient details for available IDs
            available_patients = Patient.objects.using("default").filter(
                id__in=available_patient_ids
            )

            # Serialize patients (avoid per-row DB lookups)
            from praxi_backend.patients.utils import format_patient_display_name

            patients_data = [
                {
                    "id": p.id,
                    "first_name": p.first_name or "",
                    "last_name": p.last_name or "",
                    "display_name": format_patient_display_name(
                        patient_id=int(p.id),
                        first_name=getattr(p, "first_name", None),
                        last_name=getattr(p, "last_name", None),
                        birth_date=getattr(p, "birth_date", None),
                    ),
                }
                for p in available_patients
            ]
        except Exception:
            # If patient lookup fails, return empty list
            logger.exception("AvailabilityView: error loading patients")
            patients_data = []

        return Response(
            {
                "available_doctors": doctors_data,
                "available_rooms": rooms_data,
                "available_patients": patients_data,
            },
            status=status.HTTP_200_OK,
        )
