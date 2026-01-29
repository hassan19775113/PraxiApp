"""Patient-related utility functions.

Note: This module is the canonical home for patient display-name helpers.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from praxi_backend.patients.models import Patient


def format_patient_display_name(
    *,
    patient_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    birth_date: date | None = None,
) -> str:
    """Format the canonical patient display name.

    This is a pure function (no DB access) and exists to avoid N+1 lookups
    in serializers/views.

    Output must remain stable for UI/tests.
    """

    fn = (first_name or "").strip()
    ln = (last_name or "").strip()

    if not (fn or ln):
        return f"Patient #{patient_id}"

    name = f"{ln}, {fn}".strip(", ")
    if birth_date:
        try:
            birth_str = birth_date.strftime('%d.%m.%Y')
        except Exception:
            birth_str = ""
        if birth_str:
            name += f" ({birth_str})"
    return name


def get_patient_display_name(patient_id: int) -> str:
    """Fetch + format the patient display name (Name, birth date).

    Uses the managed Patient table (default DB). If not found, returns
    "Patient #ID".
    """
    try:
        patient = Patient.objects.using('default').get(id=patient_id)
        return format_patient_display_name(
            patient_id=patient_id,
            first_name=patient.first_name,
            last_name=patient.last_name,
            birth_date=patient.birth_date,
        )
    except Patient.DoesNotExist:
        pass
    except Exception:
        pass

    return f"Patient #{patient_id}"


def get_patient_display_name_map(patient_ids: Iterable[int]) -> dict[int, str]:
    """Return a display-name map for patient IDs with a single DB query.

    Missing IDs fall back to "Patient #ID".
    """
    ids = []
    seen = set()
    for raw in patient_ids or []:
        try:
            pid = int(raw)
        except Exception:
            continue
        if pid <= 0 or pid in seen:
            continue
        seen.add(pid)
        ids.append(pid)

    if not ids:
        return {}

    rows = (
        Patient.objects.using('default')
        .filter(id__in=ids)
        .only('id', 'first_name', 'last_name', 'birth_date')
    )
    found: dict[int, str] = {}
    for p in rows:
        found[int(p.id)] = format_patient_display_name(
            patient_id=int(p.id),
            first_name=getattr(p, 'first_name', None),
            last_name=getattr(p, 'last_name', None),
            birth_date=getattr(p, 'birth_date', None),
        )

    # Fill missing with stable fallback.
    for pid in ids:
        found.setdefault(int(pid), f"Patient #{pid}")
    return found
