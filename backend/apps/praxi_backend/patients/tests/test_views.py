from __future__ import annotations

from datetime import date

from django.test import TestCase
from praxi_backend.core.models import Role, User
from praxi_backend.patients.models import Patient
from rest_framework.test import APIClient


class PatientViewsMiniTest(TestCase):
    databases = {"default"}

    def setUp(self):
        role_admin, _ = Role.objects.using("default").get_or_create(
            name="admin", defaults={"label": "Admin"}
        )
        self.admin = User.objects.db_manager("default").create_user(
            username="admin_pat_views",
            email="admin_pat_views@example.com",
            password="DummyPass123!",
            role=role_admin,
        )
        Patient.objects.using("default").create(
            id=1001, first_name="Max", last_name="Mustermann", birth_date=date(1990, 5, 15)
        )

        client = APIClient()
        client.defaults["HTTP_HOST"] = "localhost"
        client.force_authenticate(user=self.admin)
        self.client = client

    def test_search_endpoint_returns_array(self):
        r = self.client.get("/api/patients/search/?q=Must")
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(r.data, list)
        self.assertGreaterEqual(len(r.data), 1)
