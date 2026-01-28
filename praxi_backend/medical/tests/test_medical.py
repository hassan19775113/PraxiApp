"""Deprecated tests for the removed legacy medical app.

Kept to avoid breaking older references; intentionally skipped.
"""

from django.test import TestCase


class MedicalModelTestCase(TestCase):
	databases = {"default"}

	def test_deprecated(self):
		self.skipTest("praxi_backend.medical is deprecated (single DB).")
