from __future__ import annotations

from datetime import datetime, time

from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIClient

from praxi_backend.appointments.models import Appointment, AppointmentType
from praxi_backend.core.models import AuditLog, Role, User


class AppointmentViewsMiniTest(TestCase):
	"""Small smoke tests for key appointments endpoints.

	Existing test modules already cover the full behavior; this file keeps a
	lightweight contract around list filtering and auditing.
	"""

	databases = {"default"}

	def setUp(self):
		role_admin, _ = Role.objects.using("default").get_or_create(name="admin", defaults={"label": "Admin"})
		role_doctor, _ = Role.objects.using("default").get_or_create(name="doctor", defaults={"label": "Doctor"})
		self.admin = User.objects.db_manager("default").create_user(
			username="admin_views",
			email="admin_views@example.com",
			password="DummyPass123!",
			role=role_admin,
		)
		self.doctor = User.objects.db_manager("default").create_user(
			username="doctor_views",
			email="doctor_views@example.com",
			password="DummyPass123!",
			role=role_doctor,
		)
		self.type = AppointmentType.objects.using("default").create(
			name="T",
			color="#000000",
			duration_minutes=20,
			active=True,
		)

		client = APIClient()
		client.defaults["HTTP_HOST"] = "localhost"
		client.force_authenticate(user=self.admin)
		self.client = client

	def test_appointments_list_date_filter_and_audit(self):
		tz = timezone.get_current_timezone()
		day = timezone.localdate() + timezone.timedelta(days=50)

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

		before = AuditLog.objects.using("default").count()
		r = self.client.get(f"/api/appointments/?date={day}")
		self.assertEqual(r.status_code, 200)
		after = AuditLog.objects.using("default").count()
		# list endpoint should write exactly one audit entry
		self.assertEqual(after, before + 1)
