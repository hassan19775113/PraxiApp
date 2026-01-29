"""Resource (rooms/devices) CRUD API views.

Moved from `praxi_backend.appointments.views` in Phase 2B.
No logic changes; only module split.
"""

from __future__ import annotations

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Resource
from .permissions import ResourcePermission
from .serializers import ResourceSerializer


def _log_patient_action(user, action: str, patient_id: int | None = None, meta: dict | None = None):
	"""Route audit logging through `praxi_backend.appointments.views.log_patient_action`.

	Tests patch `praxi_backend.appointments.views.log_patient_action`. We keep that
	patch point stable by resolving the function lazily from `views` at call time.
	"""
	from . import views as views_module

	return views_module.log_patient_action(user, action, patient_id, meta=meta)


class ResourceListCreateView(generics.ListCreateAPIView):
	"""List/Create endpoint for resources (rooms, devices).

	For GET requests (list), any authenticated user can view resources.
	This is needed for appointment creation/editing where users need to select a room.

	For POST requests (create), ResourcePermission applies (admin/assistant only).
	"""

	queryset = Resource.objects.using('default').all()
	serializer_class = ResourceSerializer

	def get_permissions(self):
		"""Use IsAuthenticated for GET, ResourcePermission for POST/PUT/DELETE."""
		if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
			return [IsAuthenticated()]
		return [ResourcePermission()]

	def get_queryset(self):
		queryset = Resource.objects.using('default').filter(active=True).order_by('type', 'name', 'id')

		# Filter nach type (room, device, etc.)
		resource_type = self.request.query_params.get('type', '').strip()
		if resource_type:
			queryset = queryset.filter(type=resource_type)

		return queryset

	def list(self, request, *args, **kwargs):
		_log_patient_action(request.user, 'resource_list')
		return super().list(request, *args, **kwargs)

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		_log_patient_action(request.user, 'resource_create')
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ResourceDetailView(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = [ResourcePermission]
	queryset = Resource.objects.using('default').all()
	serializer_class = ResourceSerializer

	def update(self, request, *args, **kwargs):
		r = super().update(request, *args, **kwargs)
		_log_patient_action(request.user, 'resource_update')
		return r

	def destroy(self, request, *args, **kwargs):
		r = super().destroy(request, *args, **kwargs)
		_log_patient_action(request.user, 'resource_delete')
		return r
