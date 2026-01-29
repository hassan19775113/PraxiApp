"""Doctor list endpoint(s).

Moved from `praxi_backend.appointments.views` in Phase 2B.
No logic changes; only module split.
"""

from __future__ import annotations

from django.db.models import Q
from praxi_backend.core.models import User
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import DoctorListSerializer


class DoctorListView(generics.ListAPIView):
    """List endpoint for doctors (for autocomplete/selection).

    Returns only active doctors with role='doctor'.
    Provides display names, no IDs visible in UI.

    Permission: Any authenticated user can view the doctor list.
    This is needed for appointment creation/editing where users need to select a doctor.
    """

    permission_classes = [IsAuthenticated]  # Simplified: any authenticated user can view doctors
    serializer_class = DoctorListSerializer

    def get_queryset(self):
        """Filter active doctors only."""
        return (
            User.objects.using("default")
            .filter(is_active=True, role__name="doctor")
            .order_by("last_name", "first_name", "id")
        )

    def list(self, request, *args, **kwargs):
        """List doctors with optional search query."""
        queryset = self.get_queryset()

        # Optional search query
        search_query = request.query_params.get("q", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
                | Q(username__icontains=search_query)
                | Q(email__icontains=search_query)
            )

        # Serialize all doctors
        serializer = self.get_serializer(queryset, many=True)
        doctors_data = serializer.data

        # Remove duplicates based on display name (keep first occurrence)
        seen_names = set()
        unique_doctors = []
        for doctor in doctors_data:
            name_key = doctor["name"].casefold() if doctor.get("name") else ""
            if name_key and name_key not in seen_names:
                seen_names.add(name_key)
                unique_doctors.append(doctor)
            elif not name_key:
                # Keep doctors without names (shouldn't happen, but safe)
                unique_doctors.append(doctor)

        return Response(unique_doctors, status=status.HTTP_200_OK)
