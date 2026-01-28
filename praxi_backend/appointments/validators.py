"""Validators for the appointments app.

These helpers centralize common validation rules so that serializers and services
do not duplicate scheduling/business logic.

Design notes:
- Functions may raise DRF serializers.ValidationError.
- Keep error payloads stable (tests assert on some messages/keys).
- All ORM access uses the single DB alias: using('default').
"""

from __future__ import annotations

from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from praxi_backend.core.models import User
from praxi_backend.core.utils import log_patient_action

from .models import (
	Appointment,
	AppointmentResource,
	DoctorAbsence,
	DoctorBreak,
	DoctorHours,
	Operation,
	OperationDevice,
	PracticeHours,
	Resource,
)
from .scheduling import compute_suggestions_for_doctor, doctor_display_name, get_active_doctors


def validate_positive_int(value, *, field_name: str, message_required: str, message_invalid: str, message_positive: str) -> int:
	if value is None:
		raise serializers.ValidationError(message_required)
	try:
		value_int = int(value)
	except (TypeError, ValueError):
		raise serializers.ValidationError(message_invalid)
	if value_int <= 0:
		raise serializers.ValidationError(message_positive)
	return value_int


def validate_patient_id(value) -> int:
	"""Validate patient_id is present and positive.

NOTE: We intentionally do not validate existence (patient_id is not a FK).
"""
	return validate_positive_int(
		value,
		field_name="patient_id",
		message_required="patient_id ist ein Pflichtfeld.",
		message_invalid="patient_id muss eine Ganzzahl sein.",
		message_positive="patient_id muss positiv sein.",
	)


def validate_time_range(start_time: datetime | None, end_time: datetime | None) -> None:
	if start_time is not None and end_time is not None and start_time >= end_time:
		raise serializers.ValidationError({"end_time": "Endzeit muss nach der Startzeit liegen."})


def validate_doctor_user(doctor: User | None, *, field_name: str = "doctor") -> None:
	if doctor is None:
		return
	role = getattr(doctor, "role", None)
	if not role or getattr(role, "name", None) != "doctor":
		raise serializers.ValidationError({field_name: "Der Arzt muss die Rolle \"doctor\" haben."})


def validate_doctor_self_only(*, request_user: User | None, doctor: User | None) -> None:
	"""RBAC rule: doctor role can only create/update their own appointments."""
	if request_user is None or doctor is None:
		return
	user_role = getattr(getattr(request_user, "role", None), "name", None)
	if user_role == "doctor" and getattr(doctor, "id", None) != getattr(request_user, "id", None):
		raise serializers.ValidationError({"doctor": "Ärzte dürfen nur eigene Termine anlegen/ändern."})


def dedupe_int_list(raw_values: list, *, field_name: str) -> list[int]:
	unique: list[int] = []
	seen: set[int] = set()
	for v in raw_values or []:
		try:
			iv = int(v)
		except (TypeError, ValueError):
			raise serializers.ValidationError({field_name: f"{field_name} muss eine Liste von Ganzzahlen sein."})
		if iv not in seen:
			seen.add(iv)
			unique.append(iv)
	return unique


def resolve_active_resources(resource_ids: list[int]) -> list[Resource]:
	if not resource_ids:
		return []
	resources = list(Resource.objects.using("default").filter(id__in=resource_ids, active=True).order_by("id"))
	found_ids = {r.id for r in resources}
	missing = [rid for rid in resource_ids if rid not in found_ids]
	if missing:
		raise serializers.ValidationError({"resource_ids": "resource_ids enthält unbekannte oder inaktive Ressource(n)."})
	return resources


def resolve_active_devices(device_ids: list[int]) -> list[Resource]:
	if not device_ids:
		return []
	devices = list(
		Resource.objects.using("default")
		.filter(id__in=device_ids, active=True, type="device")
		.order_by("id")
	)
	found_ids = {r.id for r in devices}
	missing = [rid for rid in device_ids if rid not in found_ids]
	if missing:
		raise serializers.ValidationError({"op_device_ids": "op_device_ids enthält unbekannte/inaktive/nicht-Gerät-Ressource(n)."})
	return devices


def _duration_minutes(a: datetime, b: datetime) -> int:
	seconds = (b - a).total_seconds()
	minutes = int(seconds // 60)
	if seconds % 60:
		minutes += 1
	return max(1, minutes)


def doctor_unavailable_payload(*, doctor: User, local_start_dt: datetime, local_end_dt: datetime) -> dict:
	"""Build the legacy payload used by AppointmentCreateUpdateSerializer."""
	duration_min = _duration_minutes(local_start_dt, local_end_dt)
	alts: list[dict] = []
	for rep in get_active_doctors(exclude_doctor_id=getattr(doctor, "id", None)):
		sug = compute_suggestions_for_doctor(
			doctor=rep,
			start_date=local_start_dt.date(),
			duration_minutes=duration_min,
			limit=1,
			type_obj=None,
			max_days=31,
		)
		if sug:
			alts.append(
				{
					"doctor": {"id": rep.id, "name": doctor_display_name(rep)},
					"next_available": sug[0]["start_time"],
				}
			)
	return {"detail": "Doctor unavailable.", "alternatives": alts}


def raise_doctor_unavailable(*, doctor: User, start_time: datetime, end_time: datetime) -> None:
	local_start = timezone.localtime(start_time) if timezone.is_aware(start_time) else start_time
	local_end = timezone.localtime(end_time) if timezone.is_aware(end_time) else end_time
	raise serializers.ValidationError(doctor_unavailable_payload(doctor=doctor, local_start_dt=local_start, local_end_dt=local_end))


def validate_within_working_hours_or_unavailable(*, doctor: User, start_time: datetime, end_time: datetime) -> None:
	"""Legacy working-hours check (practice + doctor) used by AppointmentCreateUpdateSerializer."""
	local_start = timezone.localtime(start_time) if timezone.is_aware(start_time) else start_time
	local_end = timezone.localtime(end_time) if timezone.is_aware(end_time) else end_time
	weekday = local_start.weekday()
	start_t = local_start.time().replace(tzinfo=None)
	end_t = local_end.time().replace(tzinfo=None)

	practice_qs = PracticeHours.objects.using("default").filter(weekday=weekday, active=True)
	if not practice_qs.exists():
		raise_doctor_unavailable(doctor=doctor, start_time=start_time, end_time=end_time)
	if not practice_qs.filter(start_time__lte=start_t, end_time__gte=end_t).exists():
		raise_doctor_unavailable(doctor=doctor, start_time=start_time, end_time=end_time)

	dh_qs = DoctorHours.objects.using("default").filter(doctor=doctor, weekday=weekday, active=True)
	if not dh_qs.exists():
		raise_doctor_unavailable(doctor=doctor, start_time=start_time, end_time=end_time)
	if not dh_qs.filter(start_time__lte=start_t, end_time__gte=end_t).exists():
		raise_doctor_unavailable(doctor=doctor, start_time=start_time, end_time=end_time)

	# Absences
	start_date = local_start.date()
	end_date = local_end.date()
	if DoctorAbsence.objects.using("default").filter(
		doctor=doctor,
		active=True,
		start_date__lte=end_date,
		end_date__gte=start_date,
	).exists():
		raise_doctor_unavailable(doctor=doctor, start_time=start_time, end_time=end_time)

	# Breaks (practice-wide or doctor-specific)
	breaks = DoctorBreak.objects.using("default").filter(
		active=True,
		date__gte=start_date,
		date__lte=end_date,
	).filter(Q(doctor__isnull=True) | Q(doctor=doctor))
	if not breaks.exists():
		return

	tz = timezone.get_current_timezone()
	day = start_date
	while day <= end_date:
		day_start_dt = timezone.make_aware(datetime.combine(day, datetime.min.time()), tz)
		day_end_dt = timezone.make_aware(datetime.combine(day, datetime.max.time()), tz)
		seg_start = max(local_start, day_start_dt)
		seg_end = min(local_end, day_end_dt)
		for br in breaks.filter(date=day):
			br_start = timezone.make_aware(datetime.combine(day, br.start_time), tz)
			br_end = timezone.make_aware(datetime.combine(day, br.end_time), tz)
			if seg_start < br_end and seg_end > br_start:
				raise_doctor_unavailable(doctor=doctor, start_time=start_time, end_time=end_time)
		day = day + timedelta(days=1)


def validate_no_doctor_appointment_overlap_or_unavailable(
	*,
	doctor: User,
	start_time: datetime,
	end_time: datetime,
	exclude_appointment_id: int | None = None,
) -> None:
	qs = Appointment.objects.using("default").filter(
		doctor=doctor,
		start_time__lt=end_time,
		end_time__gt=start_time,
	)
	if exclude_appointment_id is not None:
		qs = qs.exclude(id=exclude_appointment_id)
	if qs.exists():
		raise_doctor_unavailable(doctor=doctor, start_time=start_time, end_time=end_time)


def validate_no_patient_appointment_overlap(
	*,
	patient_id: int,
	start_time: datetime,
	end_time: datetime,
	exclude_appointment_id: int | None = None,
) -> None:
	qs = Appointment.objects.using("default").filter(
		patient_id=patient_id,
		start_time__lt=end_time,
		end_time__gt=start_time,
	)
	if exclude_appointment_id is not None:
		qs = qs.exclude(id=exclude_appointment_id)
	if qs.exists():
		raise serializers.ValidationError(
			{"detail": "Appointment conflict: patient already has an appointment in this time range."}
		)


def validate_no_resource_conflicts(
	*,
	start_time: datetime,
	end_time: datetime,
	resources: list[Resource],
	exclude_appointment_id: int | None,
	request_user: User | None,
	patient_id: int | None,
) -> None:
	if not resources:
		return
	resource_ids = [r.id for r in resources]
	qs = AppointmentResource.objects.using("default").filter(
		resource_id__in=resource_ids,
		appointment__start_time__lt=end_time,
		appointment__end_time__gt=start_time,
	)
	if exclude_appointment_id is not None:
		qs = qs.exclude(appointment_id=exclude_appointment_id)

	conflict = qs.select_related("appointment", "resource").order_by("id").first()
	conflict_meta: dict | None = None
	if conflict is not None:
		conflict_meta = {"resource_id": conflict.resource_id, "appointment_id": conflict.appointment_id}

	# Also block resources that are booked by operations (room + devices).
	if conflict_meta is None:
		room_ids = [r.id for r in resources if getattr(r, "type", None) == "room"]
		if room_ids:
			op = (
				Operation.objects.using("default")
				.filter(op_room_id__in=room_ids, start_time__lt=end_time, end_time__gt=start_time)
				.order_by("start_time", "id")
				.first()
			)
			if op is not None:
				conflict_meta = {"resource_id": op.op_room_id, "operation_id": op.id, "reason": "operation_room"}

	if conflict_meta is None:
		device_ids = [r.id for r in resources if getattr(r, "type", None) == "device"]
		if device_ids:
			od = (
				OperationDevice.objects.using("default")
				.filter(
					resource_id__in=device_ids,
					operation__start_time__lt=end_time,
					operation__end_time__gt=start_time,
				)
				.select_related("operation")
				.order_by("operation__start_time", "operation_id", "resource_id", "id")
				.first()
			)
			if od is not None:
				conflict_meta = {"resource_id": od.resource_id, "operation_id": od.operation_id, "reason": "operation_device"}

	if conflict_meta is None:
		return

	if request_user is not None:
		try:
			pid = int(patient_id) if patient_id is not None else None
		except Exception:
			pid = None
		log_patient_action(request_user, "resource_booking_conflict", pid, meta=conflict_meta)

	raise serializers.ValidationError("Resource conflict")
