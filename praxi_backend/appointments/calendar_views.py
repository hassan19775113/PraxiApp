"""Calendar day/week/month views.

Moved from `praxi_backend.appointments.views` in Phase 2B.
No logic changes; only module split.
"""

from __future__ import annotations

import calendar
from datetime import datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
	Appointment,
	AppointmentResource,
	DoctorAbsence,
	DoctorBreak,
	Operation,
	Resource,
)
from .permissions import AppointmentPermission, ResourcePermission
from .scheduling_facade import (
	availability_for_range,
	doctor_display_name,
	get_active_doctors,
	resolve_doctor,
)
from .serializers import (
	AppointmentSerializer,
	DoctorAbsenceSerializer,
	DoctorBreakSerializer,
	OperationSerializer,
	ResourceSerializer,
)


def _log_patient_action(user, action: str, patient_id: int | None = None, meta: dict | None = None):
	"""Route audit logging through `praxi_backend.appointments.views.log_patient_action`.

	Tests patch `praxi_backend.appointments.views.log_patient_action`. We keep that
	patch point stable by resolving the function lazily from `views` at call time.
	"""
	from . import views as views_module

	return views_module.log_patient_action(user, action, patient_id, meta=meta)


def _iso_z(dt: datetime) -> str:
	# Consistent ISO output; prefer Z when in UTC.
	value = dt.isoformat()
	return value.replace('+00:00', 'Z')


class _CalendarBaseView(generics.GenericAPIView):
	permission_classes = [AppointmentPermission]
	serializer_class = AppointmentSerializer

	audit_action: str = ''

	def _parse_date(self, request):
		date_str = request.query_params.get('date')
		if not date_str:
			return None, Response(
				{'detail': 'date query parameter is required (YYYY-MM-DD).'},
				status=status.HTTP_400_BAD_REQUEST,
			)
		try:
			return datetime.strptime(date_str, '%Y-%m-%d').date(), None
		except ValueError:
			return None, Response(
				{'detail': 'date must be in format YYYY-MM-DD.'},
				status=status.HTTP_400_BAD_REQUEST,
			)

	def _parse_int(self, request, key: str):
		value = request.query_params.get(key)
		if value in (None, ''):
			return None, None
		try:
			return int(value), None
		except ValueError:
			return None, Response(
				{'detail': f'{key} must be an integer.'},
				status=status.HTTP_400_BAD_REQUEST,
			)

	def _apply_rbac(self, request, qs):
		role_name = getattr(getattr(request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			return qs.filter(doctor=request.user)
		return qs

	def _apply_filters(self, request, qs):
		doctor_id, err = self._parse_int(request, 'doctor_id')
		if err is not None:
			return None, err
		patient_id, err = self._parse_int(request, 'patient_id')
		if err is not None:
			return None, err
		type_id, err = self._parse_int(request, 'type_id')
		if err is not None:
			return None, err

		if doctor_id is not None:
			qs = qs.filter(doctor_id=doctor_id)
		if patient_id is not None:
			qs = qs.filter(patient_id=patient_id)
		if type_id is not None:
			qs = qs.filter(type_id=type_id)

		return qs, None

	def _response(self, request, range_start: datetime, range_end_inclusive: datetime):
		doctor_id, err = self._parse_int(request, 'doctor_id')
		if err is not None:
			return err

		# Use __lt for end; make it effectively inclusive via +1 microsecond.
		range_end_for_query = range_end_inclusive + timedelta(microseconds=1)
		qs = Appointment.objects.using('default').filter(
			start_time__lt=range_end_for_query,
			end_time__gt=range_start,
		)
		qs = self._apply_rbac(request, qs)
		qs, err = self._apply_filters(request, qs)
		if err is not None:
			return err

		# Doctor absences for the same calendar range
		local_start = timezone.localtime(range_start) if timezone.is_aware(range_start) else range_start
		local_end = (
			timezone.localtime(range_end_inclusive)
			if timezone.is_aware(range_end_inclusive)
			else range_end_inclusive
		)
		range_start_date = local_start.date()
		range_end_date = local_end.date()

		abs_qs = DoctorAbsence.objects.using('default').filter(
			active=True,
			start_date__lte=range_end_date,
			end_date__gte=range_start_date,
		)

		role_name = getattr(getattr(request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			abs_qs = abs_qs.filter(doctor=request.user)
		elif doctor_id is not None:
			abs_qs = abs_qs.filter(doctor_id=doctor_id)

		absences = DoctorAbsenceSerializer(
			abs_qs.order_by('doctor_id', 'start_date', 'end_date', 'id'),
			many=True,
		).data

		break_qs = DoctorBreak.objects.using('default').filter(
			active=True,
			date__gte=range_start_date,
			date__lte=range_end_date,
		)

		if role_name == 'doctor':
			break_qs = break_qs.filter(Q(doctor__isnull=True) | Q(doctor=request.user))
		elif doctor_id is not None:
			break_qs = break_qs.filter(Q(doctor__isnull=True) | Q(doctor_id=doctor_id))

		breaks = DoctorBreakSerializer(
			break_qs.order_by('date', 'start_time', 'doctor_id', 'id'),
			many=True,
		).data

		resources = ResourceSerializer(
			Resource.objects.using('default').filter(active=True).order_by('type', 'name', 'id'),
			many=True,
		).data

		# Resource bookings for appointments in this calendar response (respect RBAC+filters)
		resource_bookings = []
		appt_ids_qs = qs.values_list('id', flat=True)
		res_qs = (
			AppointmentResource.objects.using('default')
			.filter(appointment_id__in=appt_ids_qs)
			.select_related('appointment')
			.order_by('appointment__start_time', 'appointment_id', 'resource_id', 'id')
		)
		for ar in res_qs:
			appt = ar.appointment
			resource_bookings.append(
				{
					'appointment_id': ar.appointment_id,
					'resource_id': ar.resource_id,
					'start_time': _iso_z(appt.start_time),
					'end_time': _iso_z(appt.end_time),
				}
			)

		# Available doctors summary for UI.
		available_doctors = []
		doctors = []
		if role_name == 'doctor':
			doctors = [request.user]
		elif doctor_id is not None:
			maybe = resolve_doctor(doctor_id)
			if (
				maybe is not None
				and getattr(getattr(maybe, 'role', None), 'name', None) == 'doctor'
				and getattr(maybe, 'is_active', True)
			):
				doctors = [maybe]
		else:
			doctors = get_active_doctors()

		for d in doctors:
			av = availability_for_range(
				doctor=d,
				start_date=range_start_date,
				end_date=range_end_date,
				duration_minutes=30,
			)
			available_doctors.append(
				{
					'id': d.id,
					'name': doctor_display_name(d),
						'color': getattr(d, 'calendar_color', None),
					'available': bool(av.available),
					'reason': av.reason,
				}
			)

		_log_patient_action(request.user, self.audit_action)
		_log_patient_action(request.user, 'doctor_substitution_list')

		data = self.get_serializer(qs.order_by('start_time', 'id'), many=True).data

		# Operations in the same calendar range
		op_qs = Operation.objects.using('default').filter(
			start_time__lt=range_end_for_query,
			end_time__gt=range_start,
		)
		role_name = getattr(getattr(request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			op_qs = op_qs.filter(
				Q(primary_surgeon=request.user)
				| Q(assistant=request.user)
				| Q(anesthesist=request.user)
			)
		elif doctor_id is not None:
			op_qs = op_qs.filter(
				Q(primary_surgeon_id=doctor_id)
				| Q(assistant_id=doctor_id)
				| Q(anesthesist_id=doctor_id)
			)

		patient_id, err2 = self._parse_int(request, 'patient_id')
		if err2 is not None:
			return err2
		if patient_id is not None:
			op_qs = op_qs.filter(patient_id=patient_id)

		operations = OperationSerializer(
			op_qs.order_by('start_time', 'id'),
			many=True,
			context={'request': request},
		).data
		return Response(
			{
				'range_start': _iso_z(range_start),
				'range_end': _iso_z(range_end_inclusive),
				'appointments': data,
				'operations': operations,
				'absences': absences,
				'breaks': breaks,
				'resources': resources,
				'resource_bookings': resource_bookings,
				'available_doctors': available_doctors,
			},
			status=status.HTTP_200_OK,
		)


class CalendarDayView(_CalendarBaseView):
	audit_action = 'calendar_day'

	def get(self, request, *args, **kwargs):
		date_obj, err = self._parse_date(request)
		if err is not None:
			return err

		tz = timezone.get_current_timezone()
		range_start = timezone.make_aware(datetime.combine(date_obj, time.min), tz)
		range_end = timezone.make_aware(datetime.combine(date_obj, time.max), tz)
		return self._response(request, range_start, range_end)


class CalendarWeekView(_CalendarBaseView):
	audit_action = 'calendar_week'

	def get(self, request, *args, **kwargs):
		date_obj, err = self._parse_date(request)
		if err is not None:
			return err

		monday = date_obj - timedelta(days=date_obj.weekday())
		sunday = monday + timedelta(days=6)

		tz = timezone.get_current_timezone()
		range_start = timezone.make_aware(datetime.combine(monday, time.min), tz)
		range_end = timezone.make_aware(datetime.combine(sunday, time.max), tz)
		return self._response(request, range_start, range_end)


class CalendarMonthView(_CalendarBaseView):
	audit_action = 'calendar_month'

	def get(self, request, *args, **kwargs):
		date_obj, err = self._parse_date(request)
		if err is not None:
			return err

		year = date_obj.year
		month = date_obj.month
		first_day = date_obj.replace(day=1)
		last_day = date_obj.replace(day=calendar.monthrange(year, month)[1])

		tz = timezone.get_current_timezone()
		range_start = timezone.make_aware(datetime.combine(first_day, time.min), tz)
		range_end = timezone.make_aware(datetime.combine(last_day, time.max), tz)
		return self._response(request, range_start, range_end)
