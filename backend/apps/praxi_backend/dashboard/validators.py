"""Dashboard validators / parsing helpers.

Dashboard views use query parameters heavily (days, mode, charts, etc.).
These helpers keep parsing consistent and prevent ValueError crashes.
"""

from __future__ import annotations

from datetime import date


def parse_int(value, *, default: int, min_value: int | None = None, max_value: int | None = None) -> int:
	try:
		iv = int(value)
	except (TypeError, ValueError):
		iv = default
	if min_value is not None:
		iv = max(min_value, iv)
	if max_value is not None:
		iv = min(max_value, iv)
	return iv


def parse_optional_int(value) -> int | None:
	"""Parse an optional integer query param.

	Returns None for empty/invalid values.
	"""
	if value in (None, ""):
		return None
	try:
		return int(str(value).strip())
	except (TypeError, ValueError):
		return None


def parse_bool(value, *, default: bool = False) -> bool:
	if value is None:
		return default
	if isinstance(value, bool):
		return value
	s = str(value).strip().lower()
	if s in {"1", "true", "yes", "y", "on"}:
		return True
	if s in {"0", "false", "no", "n", "off"}:
		return False
	return default


def parse_iso_date(value: str | None, *, default: date) -> date:
	"""Parse YYYY-MM-DD into a date, falling back to default."""
	if not value:
		return default
	try:
		return date.fromisoformat(str(value))
	except Exception:
		return default


def validate_date_range(*, start_date: date, end_date: date) -> None:
	"""Validate that start_date <= end_date.

	Raises:
		ValueError: if the range is invalid.
	"""
	if end_date < start_date:
		raise ValueError("start_date must be <= end_date")


def parse_period(value: str | None, *, default: str = "week") -> tuple[str, int, str]:
	"""Parse UI period values into (period_key, days, german_label)."""
	period = (value or "").strip().lower()
	if period not in {"week", "month", "quarter"}:
		period = default
	if period == "week":
		return period, 7, "Woche"
	if period == "month":
		return period, 30, "Monat"
	return period, 90, "Quartal"
