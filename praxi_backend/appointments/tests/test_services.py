from __future__ import annotations

from datetime import datetime, time

from django.test import TestCase
from django.utils import timezone

from praxi_backend.appointments.models import Appointment, AppointmentType
from praxi_backend.appointments.services.querying import apply_overlap_date_filters
from praxi_backend.core.models import Role, User


class AppointmentServicesTest(TestCase):
	databases = {"default"}

	def setUp(self):
		role_doctor, _ = Role.objects.using("default").get_or_create(name="doctor", defaults={"label": "Doctor"})
		self.doctor = User.objects.db_manager("default").create_user(
			username="doctor_services",
			email="doctor_services@example.com",
			password="DummyPass123!",
			role=role_doctor,
		)
		self.type = AppointmentType.objects.using("default").create(
			name="T",
			color="#000000",
			duration_minutes=20,
			active=True,
		)

	def test_apply_overlap_date_filters_day(self):
		tz = timezone.get_current_timezone()
		day = timezone.localdate() + timezone.timedelta(days=10)

		start_in = timezone.make_aware(datetime.combine(day, time(10, 0)), tz)
		end_in = timezone.make_aware(datetime.combine(day, time(10, 30)), tz)
		Appointment.objects.using("default").create(
			patient_id=1,
			type=self.type,
			doctor=self.doctor,
			start_time=start_in,
			end_time=end_in,
			status=Appointment.STATUS_SCHEDULED,
		)

		start_out = timezone.make_aware(datetime.combine(day + timezone.timedelta(days=1), time(10, 0)), tz)
		end_out = timezone.make_aware(datetime.combine(day + timezone.timedelta(days=1), time(10, 30)), tz)
		Appointment.objects.using("default").create(
			patient_id=2,
			type=self.type,
			doctor=self.doctor,
			start_time=start_out,
			end_time=end_out,
			status=Appointment.STATUS_SCHEDULED,
		)

		qs = Appointment.objects.using("default").all().order_by("id")
		filtered = apply_overlap_date_filters(qs, date_str=str(day), start_date_str=None, end_date_str=None)
		self.assertEqual(filtered.count(), 1)

	def test_apply_overlap_date_filters_range(self):
		tz = timezone.get_current_timezone()
		start_day = timezone.localdate() + timezone.timedelta(days=20)
		end_day = start_day + timezone.timedelta(days=2)

		# appointment on start_day should match
		start_in = timezone.make_aware(datetime.combine(start_day, time(10, 0)), tz)
		end_in = timezone.make_aware(datetime.combine(start_day, time(10, 30)), tz)
		Appointment.objects.using("default").create(
			patient_id=3,
			type=self.type,
			doctor=self.doctor,
			start_time=start_in,
			end_time=end_in,
			status=Appointment.STATUS_SCHEDULED,
		)

		# appointment after range should not match
		start_out = timezone.make_aware(datetime.combine(end_day + timezone.timedelta(days=1), time(10, 0)), tz)
		end_out = timezone.make_aware(datetime.combine(end_day + timezone.timedelta(days=1), time(10, 30)), tz)
		Appointment.objects.using("default").create(
			patient_id=4,
			type=self.type,
			doctor=self.doctor,
			start_time=start_out,
			end_time=end_out,
			status=Appointment.STATUS_SCHEDULED,
		)

		qs = Appointment.objects.using("default").all().order_by("id")
		filtered = apply_overlap_date_filters(
			qs,
			date_str=None,
			start_date_str=str(start_day),
			end_date_str=str(end_day),
		)
		self.assertEqual(filtered.count(), 1)
