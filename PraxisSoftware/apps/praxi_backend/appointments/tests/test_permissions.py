from __future__ import annotations

from datetime import datetime, time

from django.test import TestCase
from django.utils import timezone
from praxi_backend.appointments.models import Appointment, AppointmentType
from praxi_backend.appointments.permissions import AppointmentPermission
from praxi_backend.core.models import Role, User
from rest_framework.test import APIRequestFactory


class AppointmentPermissionsTest(TestCase):
    databases = {"default"}

    def setUp(self):
        role_doctor, _ = Role.objects.using("default").get_or_create(
            name="doctor", defaults={"label": "Doctor"}
        )
        role_billing, _ = Role.objects.using("default").get_or_create(
            name="billing", defaults={"label": "Billing"}
        )
        self.doctor_a = User.objects.db_manager("default").create_user(
            username="doctor_perm_a",
            email="doctor_perm_a@example.com",
            password="DummyPass123!",
            role=role_doctor,
        )
        self.doctor_b = User.objects.db_manager("default").create_user(
            username="doctor_perm_b",
            email="doctor_perm_b@example.com",
            password="DummyPass123!",
            role=role_doctor,
        )
        self.billing = User.objects.db_manager("default").create_user(
            username="billing_perm",
            email="billing_perm@example.com",
            password="DummyPass123!",
            role=role_billing,
        )
        self.type = AppointmentType.objects.using("default").create(
            name="T",
            color="#000000",
            duration_minutes=20,
            active=True,
        )

    def test_appointment_permission_doctor_object_scope(self):
        perm = AppointmentPermission()
        factory = APIRequestFactory()
        req = factory.get("/api/appointments/")
        req.user = self.doctor_a
        self.assertTrue(perm.has_permission(req, view=None))

        tz = timezone.get_current_timezone()
        day = timezone.localdate() + timezone.timedelta(days=30)
        start = timezone.make_aware(datetime.combine(day, time(10, 0)), tz)
        end = timezone.make_aware(datetime.combine(day, time(10, 30)), tz)
        own = Appointment.objects.using("default").create(
            patient_id=1,
            type=self.type,
            doctor=self.doctor_a,
            start_time=start,
            end_time=end,
            status=Appointment.STATUS_SCHEDULED,
        )
        other = Appointment.objects.using("default").create(
            patient_id=2,
            type=self.type,
            doctor=self.doctor_b,
            start_time=start,
            end_time=end,
            status=Appointment.STATUS_SCHEDULED,
        )

        self.assertTrue(perm.has_object_permission(req, view=None, obj=own))
        self.assertFalse(perm.has_object_permission(req, view=None, obj=other))

    def test_appointment_permission_billing_read_only(self):
        perm = AppointmentPermission()
        factory = APIRequestFactory()
        req = factory.post("/api/appointments/", {})
        req.user = self.billing
        self.assertFalse(perm.has_permission(req, view=None))
