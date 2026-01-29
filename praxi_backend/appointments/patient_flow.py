"""Patient flow (waiting room) API views.

Moved from `praxi_backend.appointments.views` in Phase 2B.
No logic changes; only module split.
"""

from __future__ import annotations

from django.db.models import Q

from rest_framework import generics, status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response



def _log_patient_action(user, action: str, patient_id: int | None = None, meta: dict | None = None):
	"""Route audit logging through `praxi_backend.appointments.views.log_patient_action`.

	Tests patch `praxi_backend.appointments.views.log_patient_action`. Keep that
	patch point stable by resolving the function lazily from `views` at call time.
	"""
	from . import views as views_module

	return views_module.log_patient_action(user, action, patient_id, meta=meta)

from .models import PatientFlow
from .permissions import PatientFlowPermission
from .serializers import (
	PatientFlowCreateUpdateSerializer,
	PatientFlowSerializer,
	PatientFlowStatusUpdateSerializer,
)


class PatientFlowListCreateView(generics.ListCreateAPIView):
	permission_classes = [PatientFlowPermission]
	renderer_classes = [JSONRenderer]
	pagination_class = None
	queryset = PatientFlow.objects.using('default').all()

	def get_serializer_class(self):
		if self.request.method in ('POST', 'PUT', 'PATCH'):
			return PatientFlowCreateUpdateSerializer
		return PatientFlowSerializer

	def get_queryset(self):
		qs = (
			PatientFlow.objects.using('default')
			.select_related(
				'appointment',
				'appointment__type',
				'appointment__doctor',
				'operation',
				'operation__op_type',
				'operation__op_room',
				'operation__primary_surgeon',
				'operation__assistant',
				'operation__anesthesist',
			)
			.prefetch_related(
				'appointment__resources',
				'operation__op_devices',
			)
			.order_by('-status_changed_at', '-id')
		)
		role_name = getattr(getattr(self.request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			qs = qs.filter(
				Q(appointment__doctor=self.request.user)
				| Q(operation__primary_surgeon=self.request.user)
				| Q(operation__assistant=self.request.user)
				| Q(operation__anesthesist=self.request.user)
			)
		return qs

	def list(self, request, *args, **kwargs):
		r = super().list(request, *args, **kwargs)
		_log_patient_action(request.user, 'patient_flow_view')
		return r

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		flow: PatientFlow = serializer.save()
		# Initial creation doesn't count as update/status-change audit by spec.
		out = PatientFlowSerializer(flow, context={'request': request}).data
		headers = self.get_success_headers(out)
		return Response(out, status=status.HTTP_201_CREATED, headers=headers)


class PatientFlowDetailView(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = [PatientFlowPermission]
	renderer_classes = [JSONRenderer]
	queryset = PatientFlow.objects.using('default').all()

	def get_serializer_class(self):
		if self.request.method in ('PUT', 'PATCH'):
			return PatientFlowCreateUpdateSerializer
		return PatientFlowSerializer

	def get_queryset(self):
		# Apply the same RBAC filter as list.
		qs = (
			PatientFlow.objects.using('default')
			.select_related(
				'appointment',
				'appointment__type',
				'appointment__doctor',
				'operation',
				'operation__op_type',
				'operation__op_room',
				'operation__primary_surgeon',
				'operation__assistant',
				'operation__anesthesist',
			)
			.prefetch_related(
				'appointment__resources',
				'operation__op_devices',
			)
			.order_by('-status_changed_at', '-id')
		)
		role_name = getattr(getattr(self.request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			qs = qs.filter(
				Q(appointment__doctor=self.request.user)
				| Q(operation__primary_surgeon=self.request.user)
				| Q(operation__assistant=self.request.user)
				| Q(operation__anesthesist=self.request.user)
			)
		return qs

	def retrieve(self, request, *args, **kwargs):
		r = super().retrieve(request, *args, **kwargs)
		_log_patient_action(request.user, 'patient_flow_view')
		return r

	def update(self, request, *args, **kwargs):
		obj = self.get_object()
		old_status = getattr(obj, 'status', None)
		r = super().update(request, *args, **kwargs)
		_log_patient_action(request.user, 'patient_flow_update')
		# If status changed via general update, also log status-update audit.
		obj.refresh_from_db(using='default')
		new_status = getattr(obj, 'status', None)
		if new_status != old_status:
			patient_id = None
			appt = getattr(obj, 'appointment', None)
			op = getattr(obj, 'operation', None)
			if appt is not None:
				patient_id = getattr(appt, 'patient_id', None)
			elif op is not None:
				patient_id = getattr(op, 'patient_id', None)
			_log_patient_action(
				request.user,
				'patient_flow_status_update',
				patient_id=patient_id,
				meta={'flow_id': obj.id, 'from': old_status, 'to': new_status},
			)
		return r

	def partial_update(self, request, *args, **kwargs):
		return self.update(request, *args, **kwargs)


class PatientFlowStatusUpdateView(generics.GenericAPIView):
	permission_classes = [PatientFlowPermission]
	renderer_classes = [JSONRenderer]
	serializer_class = PatientFlowStatusUpdateSerializer
	queryset = PatientFlow.objects.using('default').all()

	def get_queryset(self):
		# same RBAC filter as list
		qs = PatientFlow.objects.using('default').select_related(
			'appointment', 'appointment__doctor', 'operation', 'operation__primary_surgeon', 'operation__assistant', 'operation__anesthesist'
		).prefetch_related('appointment__resources', 'operation__op_devices')
		role_name = getattr(getattr(self.request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			qs = qs.filter(
				Q(appointment__doctor=self.request.user)
				| Q(operation__primary_surgeon=self.request.user)
				| Q(operation__assistant=self.request.user)
				| Q(operation__anesthesist=self.request.user)
			)
		return qs

	def patch(self, request, *args, **kwargs):
		obj = self.get_object()
		old_status = getattr(obj, 'status', None)
		ser = self.get_serializer(instance=obj, data=request.data, partial=True)
		ser.is_valid(raise_exception=True)
		obj = ser.save()

		patient_id = None
		appt = getattr(obj, 'appointment', None)
		op = getattr(obj, 'operation', None)
		if appt is not None:
			patient_id = getattr(appt, 'patient_id', None)
		elif op is not None:
			patient_id = getattr(op, 'patient_id', None)

		_log_patient_action(
			request.user,
			'patient_flow_status_update',
			patient_id=patient_id,
			meta={'flow_id': obj.id, 'from': old_status, 'to': getattr(obj, 'status', None)},
		)
		return Response(PatientFlowSerializer(obj, context={'request': request}).data, status=status.HTTP_200_OK)


class PatientFlowLiveView(generics.ListAPIView):
	permission_classes = [PatientFlowPermission]
	serializer_class = PatientFlowSerializer
	renderer_classes = [JSONRenderer]
	pagination_class = None

	def get_queryset(self):
		qs = (
			PatientFlow.objects.using('default')
			.exclude(status=PatientFlow.STATUS_DONE)
			.select_related(
				'appointment',
				'appointment__type',
				'appointment__doctor',
				'operation',
				'operation__op_type',
				'operation__op_room',
				'operation__primary_surgeon',
				'operation__assistant',
				'operation__anesthesist',
			)
			.prefetch_related(
				'appointment__resources',
				'operation__op_devices',
			)
			.order_by('-status_changed_at', '-id')
		)
		role_name = getattr(getattr(self.request.user, 'role', None), 'name', None)
		if role_name == 'doctor':
			qs = qs.filter(
				Q(appointment__doctor=self.request.user)
				| Q(operation__primary_surgeon=self.request.user)
				| Q(operation__assistant=self.request.user)
				| Q(operation__anesthesist=self.request.user)
			)
		return qs

	def list(self, request, *args, **kwargs):
		r = super().list(request, *args, **kwargs)
		_log_patient_action(request.user, 'patient_flow_view', meta={'live': True})
		return r
