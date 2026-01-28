from __future__ import annotations

from datetime import datetime, time

from django.test import TestCase
from django.utils import timezone

from praxi_backend.appointments.models import Appointment, AppointmentType
from praxi_backend.core.models import Role, User


class AppointmentModelsMiniTest(TestCase):
	databases = {"default"}

	def test_can_create_basic_appointment(self):
		role_doctor, _ = Role.objects.using("default").get_or_create(name="doctor", defaults={"label": "Doctor"})
		doctor = User.objects.db_manager("default").create_user(
			username="doctor_models",
			email="doctor_models@example.com",
			password="DummyPass123!",
			role=role_doctor,
		)
		type_obj = AppointmentType.objects.using("default").create(
			name="T",
			color="#000000",
			duration_minutes=20,
			active=True,
		)

		tz = timezone.get_current_timezone()
		day = timezone.localdate() + timezone.timedelta(days=40)
		start = timezone.make_aware(datetime.combine(day, time(10, 0)), tz)
		end = timezone.make_aware(datetime.combine(day, time(10, 30)), tz)

		appt = Appointment.objects.using("default").create(
			patient_id=999,
			type=type_obj,
			doctor=doctor,
			start_time=start,
			end_time=end,
			status=Appointment.STATUS_SCHEDULED,
		)
		self.assertIsNotNone(appt.id)
