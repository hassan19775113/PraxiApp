from django.db.models import Q
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from praxi_backend.core.utils import log_patient_action
from praxi_backend.patients.models import Patient
from praxi_backend.patients.permissions import PatientPermission
from praxi_backend.patients.serializers import PatientReadSerializer, PatientWriteSerializer


class PatientSearchView(APIView):
    """Lightweight search endpoint for UI autocompletes.

    - If `q` is provided: returns up to 20 matching patients.
    - If `q` is empty/missing: returns a capped list (first 200) for initial dropdown population.

    Returns a plain JSON array (no pagination) because the frontend expects it.
    """

    permission_classes = [PatientPermission]

    def get(self, request):
        query = (request.GET.get('q') or '').strip()
        qs = Patient.objects.using('default').all()

        if query:
            # If the user typed an ID, allow exact matches.
            if query.isdigit():
                qs = qs.filter(id=int(query))
            else:
                # Keep it simple + fast: name / phone / email.
                qs = qs.filter(
                    Q(first_name__icontains=query)
                    | Q(last_name__icontains=query)
                    | Q(phone__icontains=query)
                    | Q(email__icontains=query)
                )
            qs = qs.order_by('last_name', 'first_name', 'id')[:20]
        else:
            # Initial load without a query (e.g. focus): return a reasonable cap.
            qs = qs.order_by('last_name', 'first_name', 'id')[:200]

        data = PatientReadSerializer(qs, many=True).data
        return Response(data)


class PatientListCreateView(generics.ListCreateAPIView):
    """List all patients or create a new patient."""

    permission_classes = [PatientPermission]

    def get_queryset(self):
        return Patient.objects.using('default').all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PatientWriteSerializer
        return PatientReadSerializer

    def perform_create(self, serializer):
        obj = serializer.save()
        log_patient_action(
            self.request.user,
            'patient_created',
            patient_id=obj.id,
        )


class PatientRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a patient."""

    permission_classes = [PatientPermission]

    def get_queryset(self):
        return Patient.objects.using('default').all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PatientWriteSerializer
        return PatientReadSerializer

    def perform_update(self, serializer):
        obj = serializer.save()
        log_patient_action(
            self.request.user,
            'patient_updated',
            patient_id=obj.id,
        )
