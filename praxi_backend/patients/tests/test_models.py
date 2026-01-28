from __future__ import annotations

from datetime import date

from django.test import TestCase

from praxi_backend.patients.models import Patient


class PatientModelsTest(TestCase):
	databases = {"default"}

	def test_can_create_patient_with_legacy_pk(self):
		p = Patient.objects.using("default").create(id=123, first_name="A", last_name="B", birth_date=date(1990, 1, 1))
		self.assertEqual(p.id, 123)
		self.assertTrue(str(p))
