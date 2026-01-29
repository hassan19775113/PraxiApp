"""Domain validators for the patients app.

Keep these rules centralized so serializers and services can reuse them.

Constraints:
- Single DB architecture: ORM access uses using('default').
- Error payloads should remain stable for existing tests.
"""

from __future__ import annotations

from datetime import date

from django.core.validators import EmailValidator

from rest_framework import serializers


def validate_patient_pk(value: int | None) -> int:
	"""Validate legacy patient primary key.

	Existing tests assert the exact error message.
	"""
	if value is None or value <= 0:
		raise serializers.ValidationError("id must be a positive integer.")
	return int(value)


def validate_birth_date_not_future(value: date | None) -> date | None:
	if value is None:
		return None
	if value > date.today():
		raise serializers.ValidationError("birth_date darf nicht in der Zukunft liegen.")
	return value


def normalize_str(value: str | None) -> str | None:
	if value is None:
		return None
	s = str(value).strip()
	return s if s else None


def validate_email_format(value: str | None) -> str | None:
	value = normalize_str(value)
	if not value:
		return None
	EmailValidator()(value)
	return value


def validate_phone_format(value: str | None) -> str | None:
	"""Conservative phone validation.

	We only normalize whitespace and accept a broad set of characters.
	"""
	value = normalize_str(value)
	if not value:
		return None
	return value
