"""OP timeline API views.

Moved from `praxi_backend.appointments.views` in Phase 2B.
No logic changes; only module split.
"""

from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response

from .models import Operation, Resource
from .permissions import OpTimelinePermission
from .serializers import OpTimelineGroupSerializer
from .views_common import parse_required_date


def _log_patient_action(user, action: str, patient_id: int | None = None, meta: dict | None = None):
    """Route audit logging through `praxi_backend.appointments.views.log_patient_action`.

    Tests patch `praxi_backend.appointments.views.log_patient_action`. Keep that
    patch point stable by resolving the function lazily from `views` at call time.
    """
    from . import views as views_module

    return views_module.log_patient_action(user, action, patient_id, meta=meta)


class _OpTimelineBaseView(generics.GenericAPIView):
    permission_classes = [OpTimelinePermission]
    serializer_class = OpTimelineGroupSerializer

    def _ops_for_date(self, request, day: date):
        qs = Operation.objects.using("default").filter(start_time__date=day)
        role_name = getattr(getattr(request.user, "role", None), "name", None)
        if role_name == "doctor":
            qs = qs.filter(
                Q(primary_surgeon=request.user)
                | Q(assistant=request.user)
                | Q(anesthesist=request.user)
            )
        return qs.select_related(
            "op_type", "op_room", "primary_surgeon", "assistant", "anesthesist"
        )

    def _ops_for_live(self, request):
        now = timezone.now()
        threshold = now - timedelta(minutes=30)
        qs = Operation.objects.using("default").filter(
            status__in=[Operation.STATUS_RUNNING, Operation.STATUS_CONFIRMED],
            start_time__gte=threshold,
        )
        role_name = getattr(getattr(request.user, "role", None), "name", None)
        if role_name == "doctor":
            qs = qs.filter(
                Q(primary_surgeon=request.user)
                | Q(assistant=request.user)
                | Q(anesthesist=request.user)
            )
        return qs.select_related(
            "op_type", "op_room", "primary_surgeon", "assistant", "anesthesist"
        )

    def _group_by_room(self, ops):
        groups: dict[int, dict] = {}
        for op in ops:
            room = getattr(op, "op_room", None)
            if room is None:
                continue
            entry = groups.get(room.id)
            if entry is None:
                entry = {"room": room, "operations": []}
                groups[room.id] = entry
            entry["operations"].append(op)

        # Sort rooms by name, and ops by start_time inside each room.
        result = sorted(
            groups.values(),
            key=lambda e: (getattr(e["room"], "name", ""), getattr(e["room"], "id", 0)),
        )
        for e in result:
            e["operations"].sort(
                key=lambda o: (getattr(o, "start_time", None), getattr(o, "id", 0))
            )
        return result

    def _audit(self, request, *, day: date | None = None, live: bool = False):
        meta = {"live": bool(live)}
        if day is not None:
            meta["date"] = day.isoformat()
        _log_patient_action(request.user, "op_timeline_view", meta=meta)


class OpTimelineView(_OpTimelineBaseView):
    """GET /api/op-timeline/?date=YYYY-MM-DD"""

    def get(self, request, *args, **kwargs):
        day, err = parse_required_date(request)
        if err is not None:
            return err
        ops = list(self._ops_for_date(request, day).order_by("op_room__name", "start_time", "id"))
        payload = self._group_by_room(ops)
        self._audit(request, day=day)
        return Response(self.get_serializer(payload, many=True).data, status=status.HTTP_200_OK)


class OpTimelineRoomsView(generics.GenericAPIView):
    """GET /api/op-timeline/rooms/?date=YYYY-MM-DD

    Returns all rooms with their (visible) operations on that date.
    For doctors, rooms without visible operations may appear with operations=[].
    """

    permission_classes = [OpTimelinePermission]
    serializer_class = OpTimelineGroupSerializer

    def get(self, request, *args, **kwargs):
        day, err = parse_required_date(request)
        if err is not None:
            return err

        rooms = list(
            Resource.objects.using("default")
            .filter(type=Resource.TYPE_ROOM, active=True)
            .order_by("name", "id")
        )

        qs = Operation.objects.using("default").filter(start_time__date=day)
        role_name = getattr(getattr(request.user, "role", None), "name", None)
        if role_name == "doctor":
            qs = qs.filter(
                Q(primary_surgeon=request.user)
                | Q(assistant=request.user)
                | Q(anesthesist=request.user)
            )
        ops = list(
            qs.select_related(
                "op_type", "op_room", "primary_surgeon", "assistant", "anesthesist"
            ).order_by("start_time", "id")
        )

        ops_by_room: dict[int, list] = {}
        for op in ops:
            rid = getattr(op, "op_room_id", None)
            if rid is None:
                continue
            ops_by_room.setdefault(int(rid), []).append(op)

        payload = [{"room": r, "operations": ops_by_room.get(r.id, [])} for r in rooms]
        _log_patient_action(
            request.user, "op_timeline_view", meta={"rooms": True, "date": day.isoformat()}
        )
        return Response(self.get_serializer(payload, many=True).data, status=status.HTTP_200_OK)


class OpTimelineLiveView(_OpTimelineBaseView):
    """GET /api/op-timeline/live/"""

    def get(self, request, *args, **kwargs):
        ops = list(self._ops_for_live(request).order_by("op_room__name", "start_time", "id"))
        payload = self._group_by_room(ops)
        self._audit(request, live=True)
        return Response(self.get_serializer(payload, many=True).data, status=status.HTTP_200_OK)
