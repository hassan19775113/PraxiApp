from __future__ import annotations

from datetime import date

from django.test import TestCase
from praxi_backend.patients.validators import (
    normalize_str,
    validate_birth_date_not_future,
    validate_email_format,
    validate_patient_pk,
)
from rest_framework import serializers


class PatientValidatorsTest(TestCase):
    databases = {"default"}

    def test_validate_patient_pk(self):
        self.assertEqual(validate_patient_pk(1), 1)
        with self.assertRaises(serializers.ValidationError):
            validate_patient_pk(0)

    def test_validate_birth_date_not_future(self):
        self.assertEqual(validate_birth_date_not_future(None), None)
        with self.assertRaises(serializers.ValidationError):
            validate_birth_date_not_future(date.today().replace(year=date.today().year + 1))

    def test_normalize_str(self):
        self.assertEqual(normalize_str("  x  "), "x")
        self.assertEqual(normalize_str("  "), None)

    def test_validate_email_format(self):
        self.assertEqual(validate_email_format(None), None)
        self.assertEqual(validate_email_format("test@example.com"), "test@example.com")
        with self.assertRaises(Exception):
            validate_email_format("not-an-email")
