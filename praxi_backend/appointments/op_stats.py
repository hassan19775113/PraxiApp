"""OP statistics API views.

Moved from `praxi_backend.appointments.views` in Phase 2B.
No logic changes; only module split.
"""

import logging
from datetime import date, datetime, time, timedelta

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

from .models import Operation, OperationDevice, Resource
from .permissions import OpStatsPermission
from .scheduling_facade import doctor_display_name
from .serializers import (
	OPStatsDeviceSerializer,
	OPStatsOverviewSerializer,
	OPStatsRoomSerializer,
	OPStatsSurgeonSerializer,
	OPStatsTypeSerializer,
	ResourceSerializer,
)


logger = logging.getLogger(__name__)


def _parse_stats_range(request):
	"""Parse ?date=YYYY-MM-DD OR ?from=YYYY-MM-DD&to=YYYY-MM-DD.

	Returns (start_dt, end_dt_inclusive, start_date, end_date, err_response)
	"""
	date_str = request.query_params.get('date')
	from_str = request.query_params.get('from')
	to_str = request.query_params.get('to')

	def _parse_date(value: str):
		return datetime.strptime(value, '%Y-%m-%d').date()

	try:
		if date_str:
			d = _parse_date(date_str)
			start_date = d
			end_date = d
		elif from_str and to_str:
			start_date = _parse_date(from_str)
			end_date = _parse_date(to_str)
			if start_date > end_date:
				return None, None, None, None, Response(
					{'detail': 'from must be <= to.'},
					status=status.HTTP_400_BAD_REQUEST,
				)
		else:
			return None, None, None, None, Response(
				{'detail': 'Provide either ?date=YYYY-MM-DD or ?from=YYYY-MM-DD&to=YYYY-MM-DD.'},
				status=status.HTTP_400_BAD_REQUEST,
			)
	except ValueError:
		return None, None, None, None, Response(
			{'detail': 'Dates must be in format YYYY-MM-DD.'},
			status=status.HTTP_400_BAD_REQUEST,
		)

	tz = timezone.get_current_timezone()
	start_dt = timezone.make_aware(datetime.combine(start_date, time.min), tz)
	end_dt = timezone.make_aware(datetime.combine(end_date, time.max), tz)
	return start_dt, end_dt, start_date, end_date, None


def _default_room_total_minutes(*, start_date: date, end_date: date) -> int:
	# Default opening time: 08:00–16:00 (8 hours) per day.
	days = (end_date - start_date).days + 1
	return max(0, int(days) * 8 * 60)


class _OpStatsBaseView(generics.GenericAPIView):
	permission_classes = [OpStatsPermission]
	stats_scope: str = ''

	def _ops_queryset(self, request, start_dt: datetime, end_dt_inclusive: datetime):
		# inclusive end via +1 microsecond and __lt
		end_for_query = end_dt_inclusive + timedelta(microseconds=1)
		qs = Operation.objects.using('default').filter(
			start_time__lt=end_for_query,
			end_time__gt=start_dt,
		)
		role_name = getattr(getattr(request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			# Doctors only see their own operations for allowed endpoints.
			qs = qs.filter(
				Q(primary_surgeon=request.user)
				| Q(assistant=request.user)
				| Q(anesthesist=request.user)
			)
		return qs.select_related('op_type', 'op_room', 'primary_surgeon', 'assistant', 'anesthesist')

	def _audit(self, request, *, start_date: date, end_date: date):
		_log_patient_action(
			request.user,
			'op_stats_view',
			meta={
				'scope': self.stats_scope,
				'from': start_date.isoformat(),
				'to': end_date.isoformat(),
			},
		)


class OpStatsOverviewView(_OpStatsBaseView):
	stats_scope = 'overview'
	serializer_class = OPStatsOverviewSerializer

	def get(self, request, *args, **kwargs):
		start_dt, end_dt, start_date, end_date, err = _parse_stats_range(request)
		if err is not None:
			return err

		ops = list(self._ops_queryset(request, start_dt, end_dt).order_by('start_time', 'id'))
		durations = []
		for op in ops:
			minutes = int(max(0, (op.end_time - op.start_time).total_seconds() // 60))
			durations.append(minutes)

		total_minutes = int(sum(durations))
		count = int(len(durations))
		avg = float(total_minutes / count) if count else 0.0

		payload = {
			'range_from': start_date,
			'range_to': end_date,
			'op_count': count,
			'total_op_minutes': total_minutes,
			'average_op_duration': avg,
		}
		self._audit(request, start_date=start_date, end_date=end_date)
		return Response(self.get_serializer(payload).data, status=status.HTTP_200_OK)


class OpStatsRoomsView(_OpStatsBaseView):
	stats_scope = 'rooms'
	serializer_class = OPStatsRoomSerializer

	def get(self, request, *args, **kwargs):
		start_dt, end_dt, start_date, end_date, err = _parse_stats_range(request)
		if err is not None:
			return err

		total_minutes = _default_room_total_minutes(start_date=start_date, end_date=end_date)
		ops = list(self._ops_queryset(request, start_dt, end_dt).order_by('start_time', 'id'))

		used_by_room: dict[int, int] = {}
		rooms: dict[int, Resource] = {}
		for op in ops:
			room = op.op_room
			if room is None:
				continue
			rooms[room.id] = room
			minutes = int(max(0, (op.end_time - op.start_time).total_seconds() // 60))
			used_by_room[room.id] = used_by_room.get(room.id, 0) + minutes

		items = []
		for room_id in sorted(rooms.keys()):
			used = int(used_by_room.get(room_id, 0))
			util = float(used / total_minutes) if total_minutes else 0.0
			items.append(
				{
					'room': ResourceSerializer(rooms[room_id]).data,
					'total_minutes': total_minutes,
					'used_minutes': used,
					'utilization': util,
				}
			)

		self._audit(request, start_date=start_date, end_date=end_date)
		return Response(
			{
				'range_from': start_date.isoformat(),
				'range_to': end_date.isoformat(),
				'rooms': self.get_serializer(items, many=True).data,
			},
			status=status.HTTP_200_OK,
		)


class OpStatsDevicesView(_OpStatsBaseView):
	stats_scope = 'devices'
	serializer_class = OPStatsDeviceSerializer

	def get(self, request, *args, **kwargs):
		start_dt, end_dt, start_date, end_date, err = _parse_stats_range(request)
		if err is not None:
			return err

		ops = list(self._ops_queryset(request, start_dt, end_dt).order_by('start_time', 'id'))
		if not ops:
			self._audit(request, start_date=start_date, end_date=end_date)
			return Response(
				{
					'range_from': start_date.isoformat(),
					'range_to': end_date.isoformat(),
					'devices': [],
				},
				status=status.HTTP_200_OK,
			)

		op_ids = [o.id for o in ops]
		row_qs = (
			OperationDevice.objects.using('default')
			.filter(operation_id__in=op_ids)
			.select_related('resource', 'operation')
			.order_by('resource_id', 'operation_id', 'id')
		)

		usage: dict[int, int] = {}
		devices: dict[int, Resource] = {}
		for row in row_qs:
			dev = row.resource
			devices[dev.id] = dev
			op = row.operation
			minutes = int(max(0, (op.end_time - op.start_time).total_seconds() // 60))
			usage[dev.id] = usage.get(dev.id, 0) + minutes

		items = []
		for dev_id in sorted(devices.keys()):
			items.append(
				{
					'device': ResourceSerializer(devices[dev_id]).data,
					'usage_minutes': int(usage.get(dev_id, 0)),
				}
			)

		self._audit(request, start_date=start_date, end_date=end_date)
		return Response(
			{
				'range_from': start_date.isoformat(),
				'range_to': end_date.isoformat(),
				'devices': self.get_serializer(items, many=True).data,
			},
			status=status.HTTP_200_OK,
		)


class OpStatsSurgeonsView(_OpStatsBaseView):
	stats_scope = 'surgeons'
	serializer_class = OPStatsSurgeonSerializer

	def get(self, request, *args, **kwargs):
		start_dt, end_dt, start_date, end_date, err = _parse_stats_range(request)
		if err is not None:
			return err

		ops_qs = self._ops_queryset(request, start_dt, end_dt)
		role_name = getattr(getattr(request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			# Do not leak other surgeons even if the doctor assisted.
			ops_qs = ops_qs.filter(primary_surgeon=request.user)

		ops = list(ops_qs.order_by('start_time', 'id'))
		by: dict[int, dict] = {}
		for op in ops:
			surgeon = op.primary_surgeon
			if surgeon is None:
				continue
			key = surgeon.id
			entry = by.get(key)
			if entry is None:
				entry = {
					'surgeon': {
						'id': surgeon.id,
						'name': doctor_display_name(surgeon),
						'color': getattr(surgeon, 'calendar_color', None),
					},
					'op_count': 0,
					'total_op_minutes': 0,
				}
				by[key] = entry
			minutes = int(max(0, (op.end_time - op.start_time).total_seconds() // 60))
			entry['op_count'] += 1
			entry['total_op_minutes'] += minutes

		items = []
		for key in sorted(by.keys()):
			entry = by[key]
			count = int(entry['op_count'])
			total = int(entry['total_op_minutes'])
			entry['average_op_duration'] = float(total / count) if count else 0.0
			items.append(entry)

		self._audit(request, start_date=start_date, end_date=end_date)
		return Response(
			{
				'range_from': start_date.isoformat(),
				'range_to': end_date.isoformat(),
				'surgeons': self.get_serializer(items, many=True).data,
			},
			status=status.HTTP_200_OK,
		)


class OpStatsTypesView(_OpStatsBaseView):
	stats_scope = 'types'
	serializer_class = OPStatsTypeSerializer

	def get(self, request, *args, **kwargs):
		start_dt, end_dt, start_date, end_date, err = _parse_stats_range(request)
		if err is not None:
			return err

		ops = list(self._ops_queryset(request, start_dt, end_dt).order_by('start_time', 'id'))
		by: dict[int, dict] = {}
		for op in ops:
			t = op.op_type
			if t is None:
				continue
			key = t.id
			minutes = int(max(0, (op.end_time - op.start_time).total_seconds() // 60))
			entry = by.get(key)
			if entry is None:
				entry = {
					'type': {'id': t.id, 'name': t.name, 'color': t.color},
					'_durations': [],
				}
				by[key] = entry
			entry['_durations'].append(minutes)

		items = []
		for key in sorted(by.keys()):
			entry = by[key]
			durations = entry.pop('_durations')
			count = int(len(durations))
			total = int(sum(durations))
			items.append(
				{
					'type': entry['type'],
					'count': count,
					'avg_duration': float(total / count) if count else 0.0,
					'min_duration': int(min(durations)) if durations else 0,
					'max_duration': int(max(durations)) if durations else 0,
				}
			)

		self._audit(request, start_date=start_date, end_date=end_date)
		return Response(
			{
				'range_from': start_date.isoformat(),
				'range_to': end_date.isoformat(),
				'types': self.get_serializer(items, many=True).data,
			},
			status=status.HTTP_200_OK,
		)
