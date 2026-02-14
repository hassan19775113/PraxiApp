from praxi_backend.core import audit as core_audit
from praxi_backend.patients.models import Patient
from praxi_backend.patients.permissions import PatientPermission
from praxi_backend.patients.serializers import PatientReadSerializer, PatientWriteSerializer
from praxi_backend.patients.services import search_patients
from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView


class PatientSearchView(APIView):
    """Lightweight search endpoint for UI autocompletes.

    - If `q` is provided: returns up to 20 matching patients.
    - If `q` is empty/missing: returns a capped list (first 200) for initial dropdown population.

    Returns a plain JSON array (no pagination) because the frontend expects it.
    """

    permission_classes = [PatientPermission]

    def get(self, request):
        query = (request.GET.get("q") or "").strip()
        qs = search_patients(query=query)

        data = PatientReadSerializer(qs, many=True).data
        return Response(data)


class PatientListCreateView(generics.ListCreateAPIView):
    """List all patients or create a new patient."""

    permission_classes = [PatientPermission]

    def get_queryset(self):
        return Patient.objects.using("default").all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PatientWriteSerializer
        return PatientReadSerializer

    def create(self, request, *args, **kwargs):
        """Create a patient and return the read representation.

        The write serializer accepts the legacy PK `id` as write_only, but clients
        (including E2E tests) need the created patient's id. Therefore we return
        `PatientReadSerializer` in the response.
        """
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        obj = write_serializer.save()
        log_patient_action(request.user, "patient_created", patient_id=obj.id)

        read_data = PatientReadSerializer(obj).data
        headers = self.get_success_headers(read_data)
        return Response(read_data, status=status.HTTP_201_CREATED, headers=headers)


class PatientRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a patient."""

    permission_classes = [PatientPermission]

    def get_queryset(self):
        return Patient.objects.using("default").all()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return PatientWriteSerializer
        return PatientReadSerializer

    def perform_update(self, serializer):
        obj = serializer.save()
        log_patient_action(self.request.user, "patient_updated", patient_id=obj.id)


def log_patient_action(user, action, patient_id=None, meta=None):
    """Stable audit patch point for patients tests.

    Tests patch `praxi_backend.patients.views.log_patient_action`.
    Internally we delegate to the central audit layer.
    """
    return core_audit.log_patient_action(user, action, patient_id, meta=meta)
