"""Service layer for the patients app.

This module consolidates business logic previously scattered across views and
serializers.

No new folders are introduced (Phase 3 constraint).
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Q, QuerySet

from praxi_backend.patients.models import Patient

from .validators import (
	normalize_str,
	validate_birth_date_not_future,
	validate_email_format,
	validate_patient_pk,
	validate_phone_format,
)


def base_patient_queryset() -> QuerySet[Patient]:
	return Patient.objects.using("default").all()


def search_patients(*, query: str, limit: int = 20, empty_limit: int = 200) -> QuerySet[Patient]:
	"""Search patients for UI autocompletes.

	Rules (must match existing behavior):
	- If query is digits: allow exact id match.
	- Else: case-insensitive search on name/phone/email.
	- Without query: return first N for initial dropdown.
	"""
	q = (query or "").strip()
	qs = base_patient_queryset()

	if q:
		if q.isdigit():
			qs = qs.filter(id=int(q))
		else:
			qs = qs.filter(
				Q(first_name__icontains=q)
				| Q(last_name__icontains=q)
				| Q(phone__icontains=q)
				| Q(email__icontains=q)
			)
		return qs.order_by("last_name", "first_name", "id")[:limit]

	return qs.order_by("last_name", "first_name", "id")[:empty_limit]


@dataclass(frozen=True)
class PatientProfileInput:
	id: int
	first_name: str | None = None
	last_name: str | None = None
	birth_date: object | None = None  # serializer already converts, keep loose here
	gender: str | None = None
	phone: str | None = None
	email: str | None = None


def _normalize_profile_data(data: dict) -> dict:
	out = dict(data)
	out["first_name"] = normalize_str(out.get("first_name")) or ""
	out["last_name"] = normalize_str(out.get("last_name")) or ""
	out["gender"] = normalize_str(out.get("gender"))
	out["phone"] = validate_phone_format(out.get("phone"))
	out["email"] = validate_email_format(out.get("email"))
	if "birth_date" in out:
		out["birth_date"] = validate_birth_date_not_future(out.get("birth_date"))
	return out


def create_patient(*, data: dict) -> Patient:
	"""Create a patient in the default DB.

	The patients table uses a legacy integer PK, so id must be supplied.
	"""
	if "id" in data:
		data = dict(data)
		data["id"] = validate_patient_pk(data.get("id"))
	data = _normalize_profile_data(data)
	return Patient.objects.using("default").create(**data)


def update_patient(*, instance: Patient, data: dict) -> Patient:
	"""Update a patient in the default DB."""
	data = _normalize_profile_data(data)
	for attr, value in data.items():
		setattr(instance, attr, value)
	instance.save(using="default")
	return instance
