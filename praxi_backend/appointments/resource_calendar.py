"""Resource calendar API views.

Moved from `praxi_backend.appointments.views` in Phase 2B.
No logic changes; only module split.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.response import Response



def _log_patient_action(user, action: str, patient_id: int | None = None, meta: dict | None = None):
	"""Route audit logging through `praxi_backend.appointments.views.log_patient_action`.

	Tests patch `praxi_backend.appointments.views.log_patient_action`. Keep that
	patch point stable by resolving the function lazily from `views` at call time.
	"""
	from . import views as views_module

	return views_module.log_patient_action(user, action, patient_id, meta=meta)

from .models import (
	AppointmentResource,
	DoctorAbsence,
	DoctorBreak,
	Operation,
	OperationDevice,
	Resource,
)
from .permissions import ResourceCalendarPermission
from .scheduling_facade import doctor_display_name
from .serializers import OperationDashboardSerializer, ResourceCalendarColumnSerializer, ResourceSerializer
from .views_common import parse_required_date


def _parse_resource_ids(request):
	value = request.query_params.get('resource_ids')
	if not value:
		return None, Response({'detail': 'Provide resource_ids as comma-separated list.'}, status=status.HTTP_400_BAD_REQUEST)
	try:
		ids = [int(x) for x in value.split(',') if x.strip()]
	except ValueError:
		return None, Response({'detail': 'resource_ids must be integers.'}, status=status.HTTP_400_BAD_REQUEST)
	if not ids:
		return None, Response({'detail': 'resource_ids cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)
	# de-dup while preserving order
	seen = set()
	out = []
	for i in ids:
		if i not in seen:
			seen.add(i)
			out.append(i)
	return out, None


def _booking_status_for_operation(op: Operation):
	st = getattr(op, 'status', None)
	if st == Operation.STATUS_RUNNING:
		return 'running'
	if st in (Operation.STATUS_PLANNED, Operation.STATUS_CONFIRMED):
		return 'planned'
	return None


class ResourceCalendarResourcesView(generics.GenericAPIView):
	"""GET /api/resource-calendar/resources/

	- admin/assistant/billing: alle Ressourcen (rooms + devices)
	- doctor: nur Ressourcen, die er in Terminen/OPs nutzt
	"""

	permission_classes = [ResourceCalendarPermission]
	serializer_class = ResourceSerializer

	def get(self, request, *args, **kwargs):
		role_name = getattr(getattr(request.user, 'role', None), 'name', None)
		qs = Resource.objects.using('default').filter(active=True)
		if role_name != 'doctor':
			resources = list(qs.order_by('type', 'name', 'id'))
			_log_patient_action(request.user, 'resource_calendar_view', meta={'resources': True})
			return Response(self.get_serializer(resources, many=True).data, status=status.HTTP_200_OK)

		# Doctor: resources used by their appointments and operations.
		appt_res_ids = (
			AppointmentResource.objects.using('default')
			.filter(appointment__doctor=request.user)
			.values_list('resource_id', flat=True)
			.distinct()
		)
		op_qs = Operation.objects.using('default').filter(
			Q(primary_surgeon=request.user)
			| Q(assistant=request.user)
			| Q(anesthesist=request.user)
		)
		op_room_ids = op_qs.values_list('op_room_id', flat=True).distinct()
		op_ids = list(op_qs.values_list('id', flat=True))
		device_ids = []
		if op_ids:
			device_ids = list(
				OperationDevice.objects.using('default')
				.filter(operation_id__in=op_ids)
				.values_list('resource_id', flat=True)
				.distinct()
			)
		allowed_ids = set(list(appt_res_ids) + list(op_room_ids) + list(device_ids))
		resources = list(qs.filter(id__in=allowed_ids).order_by('type', 'name', 'id'))
		_log_patient_action(request.user, 'resource_calendar_view', meta={'resources': True})
		return Response(self.get_serializer(resources, many=True).data, status=status.HTTP_200_OK)


class ResourceCalendarView(generics.GenericAPIView):
	"""GET /api/resource-calendar/?date=YYYY-MM-DD&resource_ids=1,2,3"""

	permission_classes = [ResourceCalendarPermission]
	serializer_class = ResourceCalendarColumnSerializer

	def get(self, request, *args, **kwargs):
		day, err = parse_required_date(request)
		if err is not None:
			return err
		resource_ids, err2 = _parse_resource_ids(request)
		if err2 is not None:
			return err2

		role_name = getattr(getattr(request.user, 'role', None), 'name', None)
		tz = timezone.get_current_timezone()
		range_start = timezone.make_aware(datetime.combine(day, time.min), tz)
		range_end = timezone.make_aware(datetime.combine(day, time.max), tz)
		range_end_for_query = range_end + timedelta(microseconds=1)

		# Resource columns requested
		resources = list(
			Resource.objects.using('default')
			.filter(id__in=resource_ids, active=True)
			.order_by('type', 'name', 'id')
		)
		resource_by_id = {r.id: r for r in resources}
		ordered_resources = [resource_by_id[i] for i in resource_ids if i in resource_by_id]

		# Optional: for doctor, restrict to resources they actually use.
		# Note: We intentionally keep the requested resource columns.
		# RBAC is applied on bookings (appointments/operations/absences/breaks).

		# Bookings collected per resource_id
		bookings: dict[int, list[dict]] = {r.id: [] for r in ordered_resources}
		if not ordered_resources:
			_log_patient_action(request.user, 'resource_calendar_view', meta={'date': day.isoformat()})
			return Response([], status=status.HTTP_200_OK)

		selected_ids = [r.id for r in ordered_resources]

		# 1) Appointments via AppointmentResource
		ar_qs = (
			AppointmentResource.objects.using('default')
			.filter(
				resource_id__in=selected_ids,
				appointment__start_time__lt=range_end_for_query,
				appointment__end_time__gt=range_start,
			)
			.select_related('appointment', 'appointment__type', 'appointment__doctor')
			.order_by('appointment__start_time', 'appointment_id', 'resource_id', 'id')
		)
		if role_name == 'doctor':
			ar_qs = ar_qs.filter(appointment__doctor=request.user)

		for ar in ar_qs:
			appt = ar.appointment
			label = 'Termin'
			type_obj = getattr(appt, 'type', None)
			if type_obj is not None and getattr(type_obj, 'name', None):
				label = str(type_obj.name)
			doctor = getattr(appt, 'doctor', None)
			if doctor is not None:
				label = f"{label} – {doctor_display_name(doctor)}"
			color = getattr(type_obj, 'color', None) if type_obj is not None else None
			if color is None and doctor is not None:
				color = getattr(doctor, 'calendar_color', None)

			bookings[ar.resource_id].append(
				{
					'kind': 'appointment',
					'id': appt.id,
					'start_time': appt.start_time,
					'end_time': appt.end_time,
					'color': color,
					'label': label,
					'status': None,
				}
			)

		# 2) Operations (rooms)
		op_qs = Operation.objects.using('default').filter(
			start_time__lt=range_end_for_query,
			end_time__gt=range_start,
		)
		if role_name == 'doctor':
			op_qs = op_qs.filter(
				Q(primary_surgeon=request.user)
				| Q(assistant=request.user)
				| Q(anesthesist=request.user)
			)
		op_qs = op_qs.select_related('op_type', 'op_room', 'primary_surgeon').order_by('start_time', 'id')
		for op in op_qs:
			room_id = getattr(op, 'op_room_id', None)
			if room_id in bookings:
				t = getattr(op, 'op_type', None)
				primary = getattr(op, 'primary_surgeon', None)
				label = 'OP'
				if t is not None and getattr(t, 'name', None):
					label = str(t.name)
				if primary is not None:
					label = f"{label} – {doctor_display_name(primary)}"
				bookings[room_id].append(
					{
						'kind': 'operation',
						'id': op.id,
						'start_time': op.start_time,
						'end_time': op.end_time,
						'color': getattr(t, 'color', None) if t is not None else None,
						'label': label,
						'status': _booking_status_for_operation(op),
						'progress': OperationDashboardSerializer().get_progress(op),
					}
				)

		# 3) Operations (devices)
		# Query operation_devices only for selected device resources
		device_rows = (
			OperationDevice.objects.using('default')
			.filter(resource_id__in=selected_ids)
			.select_related('operation', 'operation__op_type', 'operation__primary_surgeon')
			.filter(operation__start_time__lt=range_end_for_query, operation__end_time__gt=range_start)
			.order_by('operation__start_time', 'operation_id', 'resource_id', 'id')
		)
		if role_name == 'doctor':
			device_rows = device_rows.filter(
				Q(operation__primary_surgeon=request.user)
				| Q(operation__assistant=request.user)
				| Q(operation__anesthesist=request.user)
			)
		for row in device_rows:
			op = row.operation
			res_id = row.resource_id
			if res_id not in bookings:
				continue
			t = getattr(op, 'op_type', None)
			primary = getattr(op, 'primary_surgeon', None)
			label = 'OP'
			if t is not None and getattr(t, 'name', None):
				label = str(t.name)
			if primary is not None:
				label = f"{label} – {doctor_display_name(primary)}"
			bookings[res_id].append(
				{
					'kind': 'operation',
					'id': op.id,
					'start_time': op.start_time,
					'end_time': op.end_time,
					'color': getattr(t, 'color', None) if t is not None else None,
					'label': label,
					'status': _booking_status_for_operation(op),
					'progress': OperationDashboardSerializer().get_progress(op),
				}
			)

		# 4) Doctor absence/break (added to every selected resource column)
		# Spec: absence=gelb, break=orange.
		ABSENCE_COLOR = '#FFD700'
		BREAK_COLOR = '#FFA500'

		abs_qs = DoctorAbsence.objects.using('default').filter(active=True, start_date__lte=day, end_date__gte=day)
		break_qs = DoctorBreak.objects.using('default').filter(active=True, date=day)
		if role_name == 'doctor':
			abs_qs = abs_qs.filter(doctor=request.user)
			break_qs = break_qs.filter(Q(doctor__isnull=True) | Q(doctor=request.user))

		absences = list(abs_qs.select_related('doctor').order_by('doctor_id', 'start_date', 'end_date', 'id'))
		breaks = list(break_qs.select_related('doctor').order_by('start_time', 'doctor_id', 'id'))

		for res_id in selected_ids:
			for a in absences:
				doc = getattr(a, 'doctor', None)
				reason = getattr(a, 'reason', None) or 'Abwesenheit'
				if doc is not None:
					reason = f"{reason} – {doctor_display_name(doc)}"
				bookings[res_id].append(
					{
						'kind': 'absence',
						'id': a.id,
						'start_time': range_start,
						'end_time': range_end,
						'color': ABSENCE_COLOR,
						'label': reason,
						'status': None,
					}
				)
			for b in breaks:
				doc = getattr(b, 'doctor', None)
				label = 'Pause'
				if doc is not None:
					label = f"{label} – {doctor_display_name(doc)}"
				start_dt = timezone.make_aware(datetime.combine(day, b.start_time), tz)
				end_dt = timezone.make_aware(datetime.combine(day, b.end_time), tz)
				bookings[res_id].append(
					{
						'kind': 'break',
						'id': b.id,
						'start_time': start_dt,
						'end_time': end_dt,
						'color': BREAK_COLOR,
						'label': label,
						'status': None,
					}
				)

		# Sort bookings by start_time
		payload = []
		for r in ordered_resources:
			items = bookings.get(r.id, [])
			items.sort(key=lambda x: (x.get('start_time'), x.get('end_time'), x.get('kind'), x.get('id')))
			payload.append({'resource': r, 'bookings': items})

		_log_patient_action(
			request.user,
			'resource_calendar_view',
			meta={'date': day.isoformat(), 'resource_ids': resource_ids},
		)
		return Response(self.get_serializer(payload, many=True).data, status=status.HTTP_200_OK)
