"""Query helpers for the appointments app.

These helpers keep list/filter logic out of DRF views.
They intentionally only operate on QuerySets and do not perform side effects.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from django.db.models import QuerySet
from django.utils import timezone


def apply_overlap_date_filters(
	qs: QuerySet,
	*,
	date_str: str | None = None,
	start_date_str: str | None = None,
	end_date_str: str | None = None,
) -> QuerySet:
	"""Filter rows by overlap with a day or date range.

	Assumes the model has start_time/end_time datetime fields.

	- If date_str is provided (YYYY-MM-DD): return objects overlapping that day.
	- Else if start_date_str/end_date_str provided: filter by overlap with that range.
	- Invalid date strings are ignored (keeps backwards-compatible behavior).
	"""
	# Single day
	if date_str:
		try:
			day = datetime.strptime(date_str, "%Y-%m-%d").date()
		except ValueError:
			return qs

		tz = timezone.get_current_timezone()
		range_start = timezone.make_aware(datetime.combine(day, time.min), tz)
		range_end = timezone.make_aware(datetime.combine(day, time.max), tz)
		range_end_for_query = range_end + timedelta(microseconds=1)
		return qs.filter(start_time__lt=range_end_for_query, end_time__gt=range_start)

	# Date range
	if not (start_date_str or end_date_str):
		return qs

	tz = timezone.get_current_timezone()
	if start_date_str:
		try:
			start_day = datetime.strptime(start_date_str, "%Y-%m-%d").date()
			range_start = timezone.make_aware(datetime.combine(start_day, time.min), tz)
			qs = qs.filter(end_time__gt=range_start)
		except ValueError:
			pass

	if end_date_str:
		try:
			end_day = datetime.strptime(end_date_str, "%Y-%m-%d").date()
			range_end = timezone.make_aware(datetime.combine(end_day, time.max), tz)
			range_end_for_query = range_end + timedelta(microseconds=1)
			qs = qs.filter(start_time__lt=range_end_for_query)
		except ValueError:
			pass

	return qs
