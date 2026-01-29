from __future__ import annotations

from datetime import datetime, time

from django.test import TestCase
from django.utils import timezone

from rest_framework import serializers

from praxi_backend.appointments.models import Appointment, AppointmentType, DoctorHours, PracticeHours, Resource
from praxi_backend.appointments.validators import (
	dedupe_int_list,
	resolve_active_resources,
	validate_no_patient_appointment_overlap,
	validate_patient_id,
	validate_within_working_hours_or_unavailable,
)
from praxi_backend.core.models import Role, User


class AppointmentValidatorsTest(TestCase):
	databases = {"default"}

	def setUp(self):
		role_admin, _ = Role.objects.using("default").get_or_create(name="admin", defaults={"label": "Admin"})
		role_doctor, _ = Role.objects.using("default").get_or_create(name="doctor", defaults={"label": "Doctor"})
		self.admin = User.objects.db_manager("default").create_user(
			username="admin_validators",
			email="admin_validators@example.com",
			password="DummyPass123!",
			role=role_admin,
		)
		self.doctor = User.objects.db_manager("default").create_user(
			username="doctor_validators",
			email="doctor_validators@example.com",
			password="DummyPass123!",
			role=role_doctor,
		)

		self.type = AppointmentType.objects.using("default").create(
			name="T",
			color="#000000",
			duration_minutes=20,
			active=True,
		)

		self.resource = Resource.objects.using("default").create(name="Room 1", type="room", active=True)
		self.inactive_resource = Resource.objects.using("default").create(name="Room X", type="room", active=False)

		# Ensure deterministic working-hours window for today.
		tz = timezone.get_current_timezone()
		self.today = timezone.localdate()
		weekday = self.today.weekday()
		PracticeHours.objects.using("default").create(
			weekday=weekday,
			start_time=time(9, 0),
			end_time=time(13, 0),
			active=True,
		)
		DoctorHours.objects.using("default").create(
			doctor=self.doctor,
			weekday=weekday,
			start_time=time(9, 0),
			end_time=time(13, 0),
			active=True,
		)
		# avoid unused local tz warning in some linters
		self._tz = tz

	def test_validate_patient_id_errors(self):
		with self.assertRaises(serializers.ValidationError):
			validate_patient_id(None)
		with self.assertRaises(serializers.ValidationError):
			validate_patient_id("x")
		with self.assertRaises(serializers.ValidationError):
			validate_patient_id(0)
		self.assertEqual(validate_patient_id("7"), 7)

	def test_dedupe_int_list(self):
		self.assertEqual(dedupe_int_list(["1", 1, 2, "2"], field_name="resource_ids"), [1, 2])
		with self.assertRaises(serializers.ValidationError):
			dedupe_int_list(["x"], field_name="resource_ids")

	def test_resolve_active_resources(self):
		resources = resolve_active_resources([self.resource.id])
		self.assertEqual([r.id for r in resources], [self.resource.id])
		with self.assertRaises(serializers.ValidationError):
			resolve_active_resources([self.inactive_resource.id])

	def test_validate_within_working_hours_ok_and_unavailable(self):
		tz = timezone.get_current_timezone()
		start_ok = timezone.make_aware(datetime.combine(self.today, time(10, 0)), tz)
		end_ok = timezone.make_aware(datetime.combine(self.today, time(10, 30)), tz)
		validate_within_working_hours_or_unavailable(doctor=self.doctor, start_time=start_ok, end_time=end_ok)

		start_bad = timezone.make_aware(datetime.combine(self.today, time(8, 0)), tz)
		end_bad = timezone.make_aware(datetime.combine(self.today, time(8, 30)), tz)
		with self.assertRaises(serializers.ValidationError) as ctx:
			validate_within_working_hours_or_unavailable(doctor=self.doctor, start_time=start_bad, end_time=end_bad)
		payload = ctx.exception.detail
		# legacy payload: {detail, alternatives}
		self.assertEqual(payload.get("detail"), "Doctor unavailable.")
		self.assertIn("alternatives", payload)

	def test_validate_no_patient_overlap(self):
		tz = timezone.get_current_timezone()
		start = timezone.make_aware(datetime.combine(self.today, time(11, 0)), tz)
		end = timezone.make_aware(datetime.combine(self.today, time(11, 30)), tz)
		Appointment.objects.using("default").create(
			patient_id=123,
			type=self.type,
			doctor=self.doctor,
			start_time=start,
			end_time=end,
			status=Appointment.STATUS_SCHEDULED,
		)
		with self.assertRaises(serializers.ValidationError) as ctx:
			validate_no_patient_appointment_overlap(
				patient_id=123,
				start_time=start,
				end_time=end,
				exclude_appointment_id=None,
			)
		self.assertIn("Appointment conflict", str(ctx.exception.detail))
