from __future__ import annotations

from django.test import TestCase

from rest_framework.test import APIRequestFactory

from praxi_backend.core.models import Role, User
from praxi_backend.patients.permissions import PatientPermission


class PatientPermissionsTest(TestCase):
	databases = {"default"}

	def setUp(self):
		self.role_billing, _ = Role.objects.using("default").get_or_create(name="billing", defaults={"label": "Billing"})
		self.role_doctor, _ = Role.objects.using("default").get_or_create(name="doctor", defaults={"label": "Doctor"})
		self.billing = User.objects.db_manager("default").create_user(
			username="billing_pat_perm",
			email="billing_pat_perm@example.com",
			password="DummyPass123!",
			role=self.role_billing,
		)
		self.doctor = User.objects.db_manager("default").create_user(
			username="doctor_pat_perm",
			email="doctor_pat_perm@example.com",
			password="DummyPass123!",
			role=self.role_doctor,
		)

	def test_billing_is_read_only(self):
		perm = PatientPermission()
		factory = APIRequestFactory()
		req = factory.post("/api/patients/", {})
		req.user = self.billing
		self.assertFalse(perm.has_permission(req, view=None))

	def test_doctor_can_write(self):
		perm = PatientPermission()
		factory = APIRequestFactory()
		req = factory.post("/api/patients/", {})
		req.user = self.doctor
		self.assertTrue(perm.has_permission(req, view=None))
