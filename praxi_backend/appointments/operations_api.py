"""Operation CRUD + suggest API views.

Moved from `praxi_backend.appointments.views` in Phase 2B.
No logic changes; only module split.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from django.db.models import Q

from django.utils import timezone

from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .exceptions import (
	DoctorAbsentError,
	DoctorBreakConflict,
	InvalidSchedulingData,
	SchedulingConflictError,
	SchedulingError,
	WorkingHoursViolation,
)
from .models import DoctorHours, Operation, OperationType, PracticeHours, Resource
from .permissions import (
	OpDashboardPermission,
	OperationPermission,
	OperationSuggestPermission,
	OperationTypePermission,
)
from .scheduling_facade import (
	doctor_display_name,
	plan_operation as scheduling_plan_operation,
	resolve_doctor,
)
from .serializers import (
	OperationCreateUpdateSerializer,
	OperationDashboardSerializer,
	OperationSerializer,
	OperationTypeSerializer,
)
from .services.querying import apply_overlap_date_filters
from praxi_backend.patients.utils import get_patient_display_name_map


def _log_patient_action(user, action: str, patient_id: int | None = None, meta: dict | None = None):
	"""Route audit logging through `praxi_backend.appointments.views.log_patient_action`.

	Tests patch `praxi_backend.appointments.views.log_patient_action`. We keep that
	patch point stable by resolving the function lazily from `views` at call time.
	"""
	from . import views as views_module

	return views_module.log_patient_action(user, action, patient_id, meta=meta)


def _extract_patient_id_from_request(request) -> int | None:
	try:
		value = getattr(request, 'data', {}).get('patient_id', None)
		return int(value) if value not in (None, '') else None
	except Exception:
		return None


def _maybe_audit_operation_conflict(*, request, exc: Exception) -> None:
	"""Audit operation conflicts without side-effects in serializers.

	OperationCreateUpdateSerializer uses a stable error payload containing
	"Operation conflict". Tests assert that conflict 400s write an audit entry
	with action "operation_conflict".
	"""
	detail = getattr(exc, 'detail', exc)
	if 'Operation conflict' not in str(detail):
		return
	patient_id = _extract_patient_id_from_request(request)
	_log_patient_action(request.user, 'operation_conflict', patient_id)


def _iso_z(dt: datetime) -> str:
	# Consistent ISO output; prefer Z when in UTC.
	value = dt.isoformat()
	return value.replace('+00:00', 'Z')


class OpDashboardView(generics.GenericAPIView):
	permission_classes = [OpDashboardPermission]
	serializer_class = OperationDashboardSerializer

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

	def _apply_rbac(self, request, qs):
		role_name = getattr(getattr(request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			qs = qs.filter(Q(primary_surgeon=request.user) | Q(assistant=request.user) | Q(anesthesist=request.user))
		return qs

	def get(self, request, *args, **kwargs):
		date_obj, err = self._parse_date(request)
		if err is not None:
			return err

		tz = timezone.get_current_timezone()
		range_start = timezone.make_aware(datetime.combine(date_obj, time.min), tz)
		range_end = timezone.make_aware(datetime.combine(date_obj, time.max), tz)
		range_end_for_query = range_end + timedelta(microseconds=1)

		qs = (
			Operation.objects.using('default')
			.select_related('op_type', 'op_room', 'primary_surgeon', 'assistant', 'anesthesist')
			.prefetch_related('op_devices')
			.filter(
				start_time__lt=range_end_for_query,
				end_time__gt=range_start,
			)
		)
		qs = self._apply_rbac(request, qs)
		qs = qs.order_by('start_time', 'id')

		_log_patient_action(request.user, 'op_dashboard_view', meta={'date': date_obj.isoformat()})
		data = self.get_serializer(qs, many=True, context={'request': request}).data
		return Response({'date': date_obj.isoformat(), 'operations': data}, status=status.HTTP_200_OK)


class OpDashboardLiveView(generics.GenericAPIView):
	permission_classes = [OpDashboardPermission]
	serializer_class = OperationDashboardSerializer

	def _apply_rbac(self, request, qs):
		role_name = getattr(getattr(request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			qs = qs.filter(Q(primary_surgeon=request.user) | Q(assistant=request.user) | Q(anesthesist=request.user))
		return qs

	def get(self, request, *args, **kwargs):
		now = timezone.now()
		qs = (
			Operation.objects.using('default')
			.select_related('op_type', 'op_room', 'primary_surgeon', 'assistant', 'anesthesist')
			.prefetch_related('op_devices')
			.filter(
				status=Operation.STATUS_RUNNING,
				start_time__lte=now,
			)
		)
		qs = self._apply_rbac(request, qs).order_by('start_time', 'id')
		_log_patient_action(request.user, 'op_dashboard_view', meta={'live': True})
		data = self.get_serializer(qs, many=True, context={'request': request}).data
		return Response({'operations': data}, status=status.HTTP_200_OK)


class OpDashboardStatusUpdateView(generics.GenericAPIView):
	permission_classes = [OpDashboardPermission]
	serializer_class = OperationDashboardSerializer

	def patch(self, request, pk: int, *args, **kwargs):
		obj = Operation.objects.using('default').filter(id=pk).first()
		if obj is None:
			return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

		def _audit(*, ok: bool, detail: str | None = None, meta: dict | None = None):
			payload = {'from': obj.status, 'to': (request.data or {}).get('status')}
			if meta:
				payload.update(meta)
			payload['ok'] = bool(ok)
			if detail:
				payload['detail'] = detail
			_log_patient_action(
				request.user,
				'op_status_update',
				obj.patient_id,
				meta=payload,
			)

		new_status = (request.data or {}).get('status')
		if not new_status:
			_audit(ok=False, detail='status is required')
			return Response({'detail': 'status is required.'}, status=status.HTTP_400_BAD_REQUEST)

		old_status = obj.status
		allowed = False
		if new_status == Operation.STATUS_CANCELLED:
			allowed = True
		elif old_status == Operation.STATUS_PLANNED and new_status == Operation.STATUS_CONFIRMED:
			allowed = True
		elif old_status == Operation.STATUS_CONFIRMED and new_status == Operation.STATUS_RUNNING:
			allowed = True
		elif old_status == Operation.STATUS_RUNNING and new_status == Operation.STATUS_DONE:
			allowed = True

		if not allowed:
			_audit(ok=False, detail='invalid_transition', meta={'from': old_status, 'to': new_status})
			return Response(
				{'detail': 'Invalid status transition.', 'from': old_status, 'to': new_status},
				status=status.HTTP_400_BAD_REQUEST,
			)

		now = timezone.now()
		if new_status == Operation.STATUS_RUNNING and now < obj.start_time:
			_audit(ok=False, detail='running_before_start', meta={'from': old_status, 'to': new_status})
			return Response(
				{'detail': 'running is only allowed when now >= start_time.'},
				status=status.HTTP_400_BAD_REQUEST,
			)
		if new_status == Operation.STATUS_DONE and old_status != Operation.STATUS_RUNNING:
			_audit(ok=False, detail='done_not_running', meta={'from': old_status, 'to': new_status})
			return Response(
				{'detail': 'done is only allowed when previous status was running.'},
				status=status.HTTP_400_BAD_REQUEST,
			)

		obj.status = new_status
		obj.save(update_fields=['status', 'updated_at'])
		_audit(ok=True, meta={'from': old_status, 'to': new_status})

		data = self.get_serializer(obj, context={'request': request}).data
		return Response(data, status=status.HTTP_200_OK)


class OperationTypeListCreateView(generics.ListCreateAPIView):
	permission_classes = [OperationTypePermission]
	queryset = OperationType.objects.using('default').all()
	serializer_class = OperationTypeSerializer

	def get_queryset(self):
		return OperationType.objects.using('default').all().order_by('name', 'id')

	def list(self, request, *args, **kwargs):
		_log_patient_action(request.user, 'operation_type_list')
		return super().list(request, *args, **kwargs)

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		_log_patient_action(request.user, 'operation_type_create')
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class OperationTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = [OperationTypePermission]
	queryset = OperationType.objects.using('default').all()
	serializer_class = OperationTypeSerializer

	def retrieve(self, request, *args, **kwargs):
		_log_patient_action(request.user, 'operation_type_view')
		return super().retrieve(request, *args, **kwargs)

	def update(self, request, *args, **kwargs):
		r = super().update(request, *args, **kwargs)
		_log_patient_action(request.user, 'operation_type_update')
		return r

	def destroy(self, request, *args, **kwargs):
		r = super().destroy(request, *args, **kwargs)
		_log_patient_action(request.user, 'operation_type_delete')
		return r


class OperationListCreateView(generics.ListCreateAPIView):
	"""List and create operations.

	POST uses the scheduling service for full validation including:
	- Doctor absence validation (for all team members)
	- Conflict detection (room, devices, all team members, patient)
	"""

	permission_classes = [OperationPermission]
	use_scheduling_service = True  # Set to False to use legacy serializer-based validation
	pagination_class = None

	def get_permissions(self):
		"""Use IsAuthenticated for GET, OperationPermission for write operations."""
		if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
			return [IsAuthenticated()]
		return [OperationPermission()]

	def get_queryset(self):
		qs = (
			Operation.objects.using('default')
			.select_related('op_type', 'op_room', 'primary_surgeon', 'assistant', 'anesthesist')
			.prefetch_related('op_devices')
			.all()
		)
		role_name = getattr(getattr(self.request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			qs = qs.filter(
				Q(primary_surgeon=self.request.user)
				| Q(assistant=self.request.user)
				| Q(anesthesist=self.request.user)
			)
		return qs.order_by('start_time', 'id')

	def get_serializer_class(self):
		if self.request.method == 'POST':
			return OperationCreateUpdateSerializer
		return OperationSerializer

	def list(self, request, *args, **kwargs):
		"""List operations with optional date filtering.

		Supports optional query parameters:
		- date: YYYY-MM-DD format to filter operations for a specific day
		- start_date: YYYY-MM-DD format for range start
		- end_date: YYYY-MM-DD format for range end
		"""
		_log_patient_action(request.user, 'operation_list')

		qs = self.get_queryset()
		qs = apply_overlap_date_filters(
			qs,
			date_str=request.query_params.get('date'),
			start_date_str=request.query_params.get('start_date'),
			end_date_str=request.query_params.get('end_date'),
		)

		qs = qs.order_by('start_time', 'id')

		# Build a patient name map once (avoids N+1 lookups in serializers).
		patient_name_map = {}
		try:
			patient_ids = list(qs.values_list('patient_id', flat=True))
			patient_name_map = get_patient_display_name_map(patient_ids)
		except Exception:
			patient_name_map = {}

		page = self.paginate_queryset(qs)
		serializer_class = self.get_serializer_class()
		context = self.get_serializer_context()
		context['patient_name_map'] = patient_name_map

		if page is not None:
			serializer = serializer_class(page, many=True, context=context)
			return self.get_paginated_response(serializer.data)

		serializer = serializer_class(qs, many=True, context=context)
		return Response(serializer.data)

	def create(self, request, *args, **kwargs):
		"""Create an operation using the scheduling service.

		The scheduling service performs full validation and conflict detection.
		Scheduling exceptions are translated to appropriate HTTP responses.
		"""
		if self.use_scheduling_service:
			return self._create_with_scheduling_service(request)
		return self._create_legacy(request)

	def _create_legacy(self, request):
		"""Legacy create using serializer validation only."""
		write_serializer = self.get_serializer(data=request.data, context={'request': request})
		try:
			write_serializer.is_valid(raise_exception=True)
		except serializers.ValidationError as exc:
			_maybe_audit_operation_conflict(request=request, exc=exc)
			raise
		obj = write_serializer.save()
		_log_patient_action(request.user, 'operation_create', obj.patient_id)

		read_serializer = OperationSerializer(obj, context={'request': request})
		headers = self.get_success_headers(read_serializer.data)
		return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

	def _create_with_scheduling_service(self, request):
		"""Create using the scheduling service with full validation."""
		# First validate basic field structure with serializer
		write_serializer = self.get_serializer(data=request.data, context={'request': request})
		try:
			write_serializer.is_valid(raise_exception=True)
		except serializers.ValidationError as exc:
			_maybe_audit_operation_conflict(request=request, exc=exc)
			raise
		validated_data = write_serializer.validated_data

		# Extract IDs from validated objects
		primary_surgeon = validated_data.get('primary_surgeon')
		assistant = validated_data.get('assistant')
		anesthesist = validated_data.get('anesthesist')
		op_room = validated_data.get('op_room')
		op_type = validated_data.get('op_type')

		# Build data dict for scheduling service
		scheduling_data = {
			'patient_id': validated_data.get('patient_id'),
			'primary_surgeon_id': primary_surgeon.id if primary_surgeon else None,
			'assistant_id': assistant.id if assistant else None,
			'anesthesist_id': anesthesist.id if anesthesist else None,
			'op_room_id': op_room.id if op_room else None,
			'op_type_id': op_type.id if op_type else None,
			'start_time': validated_data.get('start_time'),
			'op_device_ids': validated_data.get('op_device_ids', []),
			'status': validated_data.get('status', Operation.STATUS_PLANNED),
			'notes': validated_data.get('notes', ''),
		}

		try:
			operation = scheduling_plan_operation(
				data=scheduling_data,
				user=request.user,
			)
		except SchedulingConflictError as e:
			return Response(e.to_dict(), status=status.HTTP_400_BAD_REQUEST)
		except WorkingHoursViolation as e:
			return Response(e.to_dict(), status=status.HTTP_400_BAD_REQUEST)
		except DoctorAbsentError as e:
			return Response(e.to_dict(), status=status.HTTP_400_BAD_REQUEST)
		except DoctorBreakConflict as e:
			return Response(e.to_dict(), status=status.HTTP_400_BAD_REQUEST)
		except InvalidSchedulingData as e:
			return Response(e.to_dict(), status=status.HTTP_400_BAD_REQUEST)
		except SchedulingError as e:
			return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

		# Audit must happen exactly once per API call.
		_log_patient_action(request.user, 'operation_create', operation.patient_id)
		read_serializer = OperationSerializer(operation, context={'request': request})
		headers = self.get_success_headers(read_serializer.data)
		return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class OperationDetailView(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = [OperationPermission]
	queryset = Operation.objects.using('default').all()

	def get_serializer_class(self):
		if self.request.method in ('PUT', 'PATCH'):
			return OperationCreateUpdateSerializer
		return OperationSerializer

	def retrieve(self, request, *args, **kwargs):
		obj = self.get_object()
		_log_patient_action(request.user, 'operation_view', obj.patient_id)
		return super().retrieve(request, *args, **kwargs)

	def update(self, request, *args, **kwargs):
		partial = kwargs.pop('partial', False)
		obj = self.get_object()
		write_serializer = OperationCreateUpdateSerializer(
			obj,
			data=request.data,
			partial=partial,
			context={'request': request},
		)
		try:
			write_serializer.is_valid(raise_exception=True)
		except serializers.ValidationError as exc:
			_maybe_audit_operation_conflict(request=request, exc=exc)
			raise
		updated = write_serializer.save()
		_log_patient_action(request.user, 'operation_update', updated.patient_id)
		read_serializer = OperationSerializer(updated, context={'request': request})
		return Response(read_serializer.data, status=status.HTTP_200_OK)

	def destroy(self, request, *args, **kwargs):
		obj = self.get_object()
		patient_id = obj.patient_id
		r = super().destroy(request, *args, **kwargs)
		_log_patient_action(request.user, 'operation_delete', patient_id)
		return r


class OperationSuggestView(generics.GenericAPIView):
	permission_classes = [OperationSuggestPermission]

	def _parse_int(self, request, key: str, *, required: bool = False, default=None):
		value = request.query_params.get(key)
		if value in (None, ''):
			if required:
				return None, Response(
					{'detail': f'{key} query parameter is required.'},
					status=status.HTTP_400_BAD_REQUEST,
				)
			return default, None
		try:
			return int(value), None
		except ValueError:
			return None, Response(
				{'detail': f'{key} must be an integer.'},
				status=status.HTTP_400_BAD_REQUEST,
			)

	def _parse_date(self, request, key: str, *, default_value: date):
		value = request.query_params.get(key)
		if value in (None, ''):
			return default_value, None
		try:
			return datetime.strptime(value, '%Y-%m-%d').date(), None
		except ValueError:
			return None, Response(
				{'detail': f'{key} must be in format YYYY-MM-DD.'},
				status=status.HTTP_400_BAD_REQUEST,
			)

	def _parse_int_list(self, request, key: str):
		value = request.query_params.get(key)
		if value in (None, ''):
			return None, None
		parts = [p.strip() for p in str(value).split(',') if p.strip()]
		ids = []
		try:
			for p in parts:
				ids.append(int(p))
		except ValueError:
			return None, Response(
				{'detail': f'{key} must be a comma-separated list of integers.'},
				status=status.HTTP_400_BAD_REQUEST,
			)
		seen = set()
		unique = []
		for i in ids:
			if i not in seen:
				seen.add(i)
				unique.append(i)
		return unique, None

	def get(self, request, *args, **kwargs):
		patient_id, err = self._parse_int(request, 'patient_id', required=True)
		if err is not None:
			return err

		primary_surgeon_id, err = self._parse_int(request, 'primary_surgeon_id', required=True)
		if err is not None:
			return err

		assistant_id, err = self._parse_int(request, 'assistant_id')
		if err is not None:
			return err

		anesthesist_id, err = self._parse_int(request, 'anesthesist_id')
		if err is not None:
			return err

		op_type_id, err = self._parse_int(request, 'op_type_id', required=True)
		if err is not None:
			return err

		op_room_id, err = self._parse_int(request, 'op_room_id', required=True)
		if err is not None:
			return err

		op_device_ids, err = self._parse_int_list(request, 'op_device_ids')
		if err is not None:
			return err

		start_date, err = self._parse_date(request, 'start_date', default_value=timezone.localdate())
		if err is not None:
			return err

		limit, err = self._parse_int(request, 'limit', default=3)
		if err is not None:
			return err
		if limit is None or limit <= 0:
			return Response({'detail': 'limit must be >= 1.'}, status=status.HTTP_400_BAD_REQUEST)

		# Validate core references (serializer also validates, but we want clean 400s)
		primary_surgeon = resolve_doctor(primary_surgeon_id)
		if primary_surgeon is None:
			return Response({'detail': 'primary_surgeon_id not found.'}, status=status.HTTP_400_BAD_REQUEST)
		if getattr(getattr(primary_surgeon, 'role', None), 'name', None) != 'doctor':
			return Response(
				{'detail': 'primary_surgeon_id must reference a user with role "doctor".'},
				status=status.HTTP_400_BAD_REQUEST,
			)
		if not getattr(primary_surgeon, 'is_active', True):
			return Response(
				{'detail': 'primary_surgeon_id must reference an active doctor.'},
				status=status.HTTP_400_BAD_REQUEST,
			)

		op_type = OperationType.objects.using('default').filter(id=op_type_id).first()
		if op_type is None:
			return Response({'detail': 'op_type_id not found.'}, status=status.HTTP_400_BAD_REQUEST)
		if not getattr(op_type, 'active', True):
			return Response({'detail': 'op_type_id is inactive.'}, status=status.HTTP_400_BAD_REQUEST)

		op_room = Resource.objects.using('default').filter(id=op_room_id, active=True).first()
		if op_room is None:
			return Response({'detail': 'op_room_id not found.'}, status=status.HTTP_400_BAD_REQUEST)
		if getattr(op_room, 'type', None) != 'room':
			return Response(
				{'detail': 'op_room_id must reference a Resource with type "room".'},
				status=status.HTTP_400_BAD_REQUEST,
			)

		# Scan: propose the earliest valid slot per day window
		weekday = start_date.weekday()
		practice_hours = list(
			PracticeHours.objects.using('default').filter(weekday=weekday, active=True).order_by('start_time', 'id')
		)
		doctor_hours = list(
			DoctorHours.objects.using('default')
			.filter(doctor=primary_surgeon, weekday=weekday, active=True)
			.order_by('start_time', 'id')
		)
		if not (practice_hours and doctor_hours):
			_log_patient_action(request.user, 'operation_suggest')
			return Response(
				{
					'primary_surgeon': {
						'id': primary_surgeon.id,
						'name': doctor_display_name(primary_surgeon),
						'color': getattr(primary_surgeon, 'calendar_color', None),
					},
					'suggestions': [],
				},
				status=status.HTTP_200_OK,
			)

		tz = timezone.get_current_timezone()
		day_start = timezone.make_aware(datetime.combine(start_date, time.min), tz)
		now_local = timezone.localtime(timezone.now())

		step = timedelta(minutes=5)
		suggestions = []
		for ph in practice_hours:
			for dh in doctor_hours:
				window_start_t = max(ph.start_time, dh.start_time)
				window_end_t = min(ph.end_time, dh.end_time)
				if window_start_t >= window_end_t:
					continue
				window_start_dt = timezone.make_aware(datetime.combine(start_date, window_start_t), tz)
				window_end_dt = timezone.make_aware(datetime.combine(start_date, window_end_t), tz)

				candidate = window_start_dt
				if start_date == now_local.date():
					candidate = max(candidate, now_local)
				candidate = candidate.replace(second=0, microsecond=0)
				# align to 5 min
				mod = candidate.minute % 5
				if mod:
					candidate = candidate + timedelta(minutes=(5 - mod))

				while candidate < window_end_dt and len(suggestions) < limit:
					payload = {
						'patient_id': patient_id,
						'primary_surgeon': primary_surgeon_id,
						'assistant': assistant_id,
						'anesthesist': anesthesist_id,
						'op_room': op_room_id,
						'op_device_ids': op_device_ids or [],
						'op_type': op_type_id,
						'start_time': _iso_z(candidate),
						'status': 'planned',
						'notes': '',
					}
					ser = OperationCreateUpdateSerializer(
						data=payload,
						context={'request': request, 'suppress_conflict_audit': True},
					)
					if ser.is_valid():
						end_dt = ser.validated_data['end_time']
						suggestions.append(
							{
								'start_time': _iso_z(candidate),
								'end_time': _iso_z(end_dt),
								'op_type': {'id': op_type.id, 'name': op_type.name, 'color': op_type.color},
								'op_room': {'id': op_room.id, 'name': op_room.name, 'color': op_room.color},
								'op_device_ids': op_device_ids or [],
							}
						)
						break
					candidate = candidate + step

				if len(suggestions) >= limit:
					break
			if len(suggestions) >= limit:
				break

		_log_patient_action(request.user, 'operation_suggest')
		return Response(
			{
				'primary_surgeon': {
					'id': primary_surgeon.id,
					'name': doctor_display_name(primary_surgeon),
					'color': getattr(primary_surgeon, 'calendar_color', None),
				},
				'suggestions': suggestions,
			},
			status=status.HTTP_200_OK,
		)
