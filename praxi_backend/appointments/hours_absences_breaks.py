"""Practice/Doctor hours, absences and breaks API views.

Moved from `praxi_backend.appointments.views` in Phase 2B.
No logic changes; only module split.
"""

from __future__ import annotations

from django.utils.dateparse import parse_date

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DoctorAbsence, DoctorBreak, DoctorHours, PracticeHours
from .permissions import DoctorAbsencePermission, DoctorBreakPermission, DoctorHoursPermission, PracticeHoursPermission
from .serializers import DoctorAbsenceSerializer, DoctorBreakSerializer, DoctorHoursSerializer, PracticeHoursSerializer
from .services.absence_preview import build_absence_preview
from .scheduling_facade import resolve_doctor


def _log_patient_action(user, action: str, patient_id: int | None = None, meta: dict | None = None):
	"""Route audit logging through `praxi_backend.appointments.views.log_patient_action`.

	Tests patch `praxi_backend.appointments.views.log_patient_action`. We keep that
	patch point stable by resolving the function lazily from `views` at call time.
	"""
	from . import views as views_module

	return views_module.log_patient_action(user, action, patient_id, meta=meta)


class PracticeHoursListCreateView(generics.ListCreateAPIView):
	permission_classes = [PracticeHoursPermission]
	queryset = PracticeHours.objects.using('default').all()
	serializer_class = PracticeHoursSerializer

	def list(self, request, *args, **kwargs):
		_log_patient_action(request.user, 'practice_hours_list')
		return super().list(request, *args, **kwargs)

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		_log_patient_action(request.user, 'practice_hours_create')
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class PracticeHoursDetailView(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = [PracticeHoursPermission]
	queryset = PracticeHours.objects.using('default').all()
	serializer_class = PracticeHoursSerializer

	def get_serializer_class(self):
		if self.request.method in ('PUT', 'PATCH'):
			return PracticeHoursCreateUpdateSerializer
		return PracticeHoursSerializer

	def retrieve(self, request, *args, **kwargs):
		_log_patient_action(request.user, 'practice_hours_view')
		return super().retrieve(request, *args, **kwargs)

	def update(self, request, *args, **kwargs):
		response = super().update(request, *args, **kwargs)
		_log_patient_action(request.user, 'practice_hours_update')
		return response

	def destroy(self, request, *args, **kwargs):
		response = super().destroy(request, *args, **kwargs)
		_log_patient_action(request.user, 'practice_hours_delete')
		return response


class DoctorHoursListCreateView(generics.ListCreateAPIView):
	permission_classes = [DoctorHoursPermission]
	serializer_class = DoctorHoursSerializer

	def get_queryset(self):
		qs = DoctorHours.objects.using('default').all()
		role_name = getattr(getattr(self.request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			return qs.filter(doctor=self.request.user)
		return qs

	def list(self, request, *args, **kwargs):
		_log_patient_action(request.user, 'doctor_hours_list')
		return super().list(request, *args, **kwargs)

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		_log_patient_action(request.user, 'doctor_hours_create')
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class DoctorHoursDetailView(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = [DoctorHoursPermission]
	serializer_class = DoctorHoursSerializer

	def get_queryset(self):
		qs = DoctorHours.objects.using('default').all()
		role_name = getattr(getattr(self.request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			return qs.filter(doctor=self.request.user)
		return qs

	def retrieve(self, request, *args, **kwargs):
		_log_patient_action(request.user, 'doctor_hours_view')
		return super().retrieve(request, *args, **kwargs)

	def update(self, request, *args, **kwargs):
		response = super().update(request, *args, **kwargs)
		_log_patient_action(request.user, 'doctor_hours_update')
		return response

	def destroy(self, request, *args, **kwargs):
		response = super().destroy(request, *args, **kwargs)
		_log_patient_action(request.user, 'doctor_hours_delete')
		return response


class DoctorAbsenceListCreateView(generics.ListCreateAPIView):
	permission_classes = [DoctorAbsencePermission]
	serializer_class = DoctorAbsenceSerializer

	def get_queryset(self):
		qs = DoctorAbsence.objects.using('default').all()
		role_name = getattr(getattr(self.request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			return qs.filter(doctor=self.request.user)
		return qs

	def list(self, request, *args, **kwargs):
		_log_patient_action(request.user, 'doctor_absence_list')
		return super().list(request, *args, **kwargs)

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		_log_patient_action(request.user, 'doctor_absence_create')
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class DoctorAbsenceDetailView(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = [DoctorAbsencePermission]
	serializer_class = DoctorAbsenceSerializer

	def get_queryset(self):
		qs = DoctorAbsence.objects.using('default').all()
		role_name = getattr(getattr(self.request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			return qs.filter(doctor=self.request.user)
		return qs

	def retrieve(self, request, *args, **kwargs):
		_log_patient_action(request.user, 'doctor_absence_view')
		return super().retrieve(request, *args, **kwargs)

	def update(self, request, *args, **kwargs):
		response = super().update(request, *args, **kwargs)
		_log_patient_action(request.user, 'doctor_absence_update')
		return response

	def destroy(self, request, *args, **kwargs):
		response = super().destroy(request, *args, **kwargs)
		_log_patient_action(request.user, 'doctor_absence_delete')
		return response


class DoctorAbsencePreviewView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		doctor_id = request.query_params.get('doctor_id')
		start_date = parse_date(request.query_params.get('start_date', ''))
		end_date = parse_date(request.query_params.get('end_date', ''))
		reason = request.query_params.get('reason', '')

		doctor = None
		try:
			doctor = resolve_doctor(int(doctor_id)) if doctor_id else None
		except Exception:
			doctor = None

		preview = build_absence_preview(
			doctor=doctor,
			reason=reason,
			start_date=start_date,
			end_date=end_date,
		)

		return Response(
			{
				'duration_workdays': preview.duration_workdays or 0,
				'return_date': preview.return_date.isoformat() if preview.return_date else None,
				'remaining_days': preview.remaining_days,
			}
		)


class DoctorBreakListCreateView(generics.ListCreateAPIView):
	permission_classes = [DoctorBreakPermission]
	serializer_class = DoctorBreakSerializer

	def get_queryset(self):
		qs = DoctorBreak.objects.using('default').all()
		role_name = getattr(getattr(self.request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			return qs.filter(doctor=self.request.user)
		return qs

	def list(self, request, *args, **kwargs):
		_log_patient_action(request.user, 'doctor_break_list')
		return super().list(request, *args, **kwargs)

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		_log_patient_action(request.user, 'doctor_break_create')
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class DoctorBreakDetailView(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = [DoctorBreakPermission]
	serializer_class = DoctorBreakSerializer

	def get_queryset(self):
		qs = DoctorBreak.objects.using('default').all()
		role_name = getattr(getattr(self.request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			return qs.filter(doctor=self.request.user)
		return qs

	def retrieve(self, request, *args, **kwargs):
		_log_patient_action(request.user, 'doctor_break_view')
		return super().retrieve(request, *args, **kwargs)

	def update(self, request, *args, **kwargs):
		r = super().update(request, *args, **kwargs)
		_log_patient_action(request.user, 'doctor_break_update')
		return r

	def destroy(self, request, *args, **kwargs):
		r = super().destroy(request, *args, **kwargs)
		_log_patient_action(request.user, 'doctor_break_delete')
		return r
