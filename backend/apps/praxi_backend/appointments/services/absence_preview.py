"""Doctor absence preview helpers.

The preview endpoint returns:
- number of workdays in a requested absence period
- return-to-work day (next weekday)
- remaining vacation days when reason == "Urlaub" (optional)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from praxi_backend.appointments.models import DoctorAbsence
from praxi_backend.core.models import User


@dataclass(frozen=True)
class AbsencePreview:
    duration_workdays: int
    return_date: date | None
    remaining_days: int | None


def count_workdays(start_date: date | None, end_date: date | None) -> int:
    if start_date is None or end_date is None or end_date < start_date:
        return 0
    days = 0
    cur = start_date
    while cur <= end_date:
        if cur.weekday() < 5:
            days += 1
        cur += timedelta(days=1)
    return days


def next_workday(date_value: date | None) -> date | None:
    if date_value is None:
        return None
    cur = date_value + timedelta(days=1)
    while cur.weekday() >= 5:
        cur += timedelta(days=1)
    return cur


def remaining_vacation_days(
    *,
    doctor: User | None,
    reason: str | None,
    start_date: date | None,
    end_date: date | None,
    duration_workdays: int,
) -> int | None:
    """Return remaining vacation days for the given year.

    Only applies when reason == "Urlaub" (case-insensitive).
    """
    if doctor is None:
        return None
    if (reason or "").strip().lower() != "urlaub":
        return None
    if start_date is None:
        return None
    year = start_date.year

    allocation = getattr(doctor, "vacation_days_per_year", 30) or 0
    qs = DoctorAbsence.objects.using("default").filter(
        doctor_id=doctor.id,
        reason__iexact="Urlaub",
        active=True,
    )
    used = 0
    for absence in qs:
        if absence.start_date is None or absence.end_date is None:
            continue
        if absence.start_date.year > year or absence.end_date.year < year:
            continue
        start = max(absence.start_date, date(year, 1, 1))
        end = min(absence.end_date, date(year, 12, 31))
        used += count_workdays(start, end)

    used += int(duration_workdays or 0)
    return max(0, int(allocation) - int(used))


def build_absence_preview(
    *,
    doctor: User | None,
    reason: str | None,
    start_date: date | None,
    end_date: date | None,
) -> AbsencePreview:
    duration = count_workdays(start_date, end_date)
    return_date = next_workday(end_date)
    remaining = remaining_vacation_days(
        doctor=doctor,
        reason=reason,
        start_date=start_date,
        end_date=end_date,
        duration_workdays=duration,
    )
    return AbsencePreview(
        duration_workdays=duration, return_date=return_date, remaining_days=remaining
    )
