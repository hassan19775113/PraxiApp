from __future__ import annotations

from datetime import date

from django.test import TestCase

from praxi_backend.patients.models import Patient
from praxi_backend.patients.services import create_patient, search_patients, update_patient


class PatientServicesTest(TestCase):
	databases = {"default"}

	def setUp(self):
		Patient.objects.using("default").create(id=1001, first_name="Max", last_name="Mustermann")
		Patient.objects.using("default").create(id=2002, first_name="Erika", last_name="Musterfrau")

	def test_search_patients_by_name(self):
		qs = search_patients(query="muster")
		self.assertGreaterEqual(qs.count(), 2)

	def test_search_patients_by_id(self):
		qs = search_patients(query="1001")
		self.assertEqual(list(qs.values_list("id", flat=True)), [1001])

	def test_create_and_update_patient(self):
		p = create_patient(data={"id": 3003, "first_name": "Test", "last_name": "User", "birth_date": date(2000, 1, 1)})
		self.assertEqual(p.id, 3003)
		p2 = update_patient(instance=p, data={"phone": "123"})
		self.assertEqual(p2.phone, "123")
