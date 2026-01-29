from __future__ import annotations

from django.test import TestCase
from praxi_backend.appointments.models import Resource
from praxi_backend.dashboard.services import (
    build_resources_dashboard_context,
    build_scheduling_api_payload,
)
from praxi_backend.patients.models import Patient


class DashboardServicesTest(TestCase):
    databases = {"default"}

    def setUp(self):
        Patient.objects.using("default").create(id=1, first_name="Max", last_name="Mustermann")
        Resource.objects.using("default").create(
            name="Raum 1",
            type=Resource.TYPE_ROOM,
            color="#4A90E2",
            active=True,
        )
        Resource.objects.using("default").create(
            name="Device 1",
            type=Resource.TYPE_DEVICE,
            color="#7ED6C1",
            active=True,
        )

    def test_build_resources_dashboard_context_shape(self):
        ctx = build_resources_dashboard_context()
        self.assertEqual(ctx.get("title"), "Ressourcen & Räume")
        self.assertIn("rooms", ctx)
        self.assertIn("devices", ctx)
        self.assertIn("rooms_json", ctx)
        self.assertIn("devices_json", ctx)
        self.assertTrue(isinstance(ctx["rooms"], list))
        self.assertTrue(isinstance(ctx["devices"], list))

    def test_build_scheduling_api_payload_shape(self):
        payload = build_scheduling_api_payload()
        self.assertIn("kpis", payload)
        self.assertIn("charts", payload)
