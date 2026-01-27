from django.db.models import Q

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from praxi_backend.core.permissions import IsAdmin, IsAssistant, IsBilling, IsDoctor
from praxi_backend.core.utils import log_patient_action

from .models import Patient
from .serializers import (
    PatientBillingSerializer,
    PatientSerializer,
)


class PatientListView(ListAPIView):
    """
    Read-only list of patients from the legacy medical database.

    NOTE: The medical database is READ-ONLY. Patient creation/update
    must be done via the patients app (system database cache) or
    through the legacy system directly.
    """
    permission_classes = [IsAdmin | IsDoctor | IsAssistant | IsBilling]

    def get_queryset(self):
        return Patient.objects.using('medical').order_by('id')

    def get_serializer_class(self):
        user = getattr(self.request, 'user', None)
        role = getattr(user, 'role', None)
        if role and role.name == 'billing':
            return PatientBillingSerializer
        return PatientSerializer

    def list(self, request, *args, **kwargs):
        log_patient_action(request.user, 'patient_list')
        return super().list(request, *args, **kwargs)


class PatientDetailView(RetrieveAPIView):
    """Read-only patient detail from the legacy medical database."""
    permission_classes = [IsAdmin | IsDoctor | IsAssistant | IsBilling]

    def get_queryset(self):
        return Patient.objects.using('medical').all()

    def get_serializer_class(self):
        user = getattr(self.request, 'user', None)
        role = getattr(user, 'role', None)
        if role and role.name == 'billing':
            return PatientBillingSerializer
        return PatientSerializer

    def retrieve(self, request, *args, **kwargs):
        log_patient_action(request.user, 'patient_view', patient_id=kwargs.get('pk'))
        return super().retrieve(request, *args, **kwargs)


class PatientSearchView(ListAPIView):
    """Read-only patient search on the legacy medical database.
    
    Returns all patients if no query parameter is provided.
    Filters by query if 'q' parameter is provided.
    
    Permission: Any authenticated user can search patients.
    This is needed for appointment creation/editing where users need to select a patient.
    """
    permission_classes = [IsAuthenticated]  # Simplified: any authenticated user can search patients

    def get_queryset(self):
        q = (self.request.query_params.get('q') or '').strip()
        
        # Wenn keine Suche, alle Patienten zurückgeben (limit auf 100 für Performance)
        if not q:
            return Patient.objects.using('medical').order_by('last_name', 'first_name', 'id')[:100]

        # Wenn Suche, filtere
        return (
            Patient.objects.using('medical')
            .filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(phone__icontains=q)
                | Q(email__icontains=q)
            )
            .order_by('last_name', 'first_name', 'id')[:50]
        )

    def get_serializer_class(self):
        user = getattr(self.request, 'user', None)
        role = getattr(user, 'role', None)
        if role and role.name == 'billing':
            return PatientBillingSerializer
        return PatientSerializer

    def list(self, request, *args, **kwargs):
        q = (request.query_params.get('q') or '').strip()
        log_patient_action(request.user, 'patient_search', meta={'query': q})
        return super().list(request, *args, **kwargs)
