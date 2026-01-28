from __future__ import annotations

from datetime import date

from django.test import TestCase

from praxi_backend.dashboard.validators import (
    parse_iso_date,
    parse_optional_int,
    parse_period,
    validate_date_range,
)


class DashboardValidatorsTest(TestCase):
    databases = {"default"}

    def test_parse_optional_int(self):
        self.assertEqual(parse_optional_int("10"), 10)
        self.assertEqual(parse_optional_int("  10  "), 10)
        self.assertIsNone(parse_optional_int(""))
        self.assertIsNone(parse_optional_int(None))
        self.assertIsNone(parse_optional_int("x"))

    def test_parse_iso_date(self):
        fallback = date(2030, 1, 1)
        self.assertEqual(parse_iso_date("2030-02-03", default=fallback), date(2030, 2, 3))
        self.assertEqual(parse_iso_date("not-a-date", default=fallback), fallback)
        self.assertEqual(parse_iso_date(None, default=fallback), fallback)

    def test_validate_date_range(self):
        validate_date_range(start_date=date(2030, 1, 1), end_date=date(2030, 1, 1))
        validate_date_range(start_date=date(2030, 1, 1), end_date=date(2030, 1, 2))
        with self.assertRaises(ValueError):
            validate_date_range(start_date=date(2030, 1, 2), end_date=date(2030, 1, 1))

    def test_parse_period(self):
        self.assertEqual(parse_period("week"), ("week", 7, "Woche"))
        self.assertEqual(parse_period("month"), ("month", 30, "Monat"))
        self.assertEqual(parse_period("quarter"), ("quarter", 90, "Quartal"))
        # invalid -> default
        self.assertEqual(parse_period("bogus"), ("week", 7, "Woche"))
