"""Re-export shim for appointments API views.

Phase 2B goal: keep `praxi_backend.appointments.views` as the stable import surface
used by `praxi_backend.appointments.urls` while splitting the large monolithic
views module into smaller, thematic modules.

IMPORTANT:
- Tests patch `praxi_backend.appointments.views.log_patient_action`.
  Therefore we keep that symbol here and route audit logging calls through it.
"""

from __future__ import annotations

from django.utils import timezone

from praxi_backend.core import audit as core_audit


def log_patient_action(user, action, patient_id=None, meta=None):
	"""Stable audit patch point for tests.

	Tests patch `praxi_backend.appointments.views.log_patient_action`.
	Internally we delegate to the central audit layer.
	"""
	return core_audit.log_patient_action(user, action, patient_id, meta=meta)

# Appointments (CRUD + suggest + types)
from .appointments_api import (
	AppointmentDetailView,
	AppointmentListCreateView,
	AppointmentSuggestView,
	AppointmentTypeDetailView,
	AppointmentTypeListCreateView,
)

# Operations (CRUD + suggest + types + dashboard)
from .operations_api import (
	OpDashboardLiveView,
	OpDashboardStatusUpdateView,
	OpDashboardView,
	OperationDetailView,
	OperationListCreateView,
	OperationSuggestView,
	OperationTypeDetailView,
	OperationTypeListCreateView,
)

# Calendar
from .calendar_views import CalendarDayView, CalendarMonthView, CalendarWeekView

# Practice hours / doctor hours / absences / breaks
from .hours_absences_breaks import (
	DoctorAbsenceDetailView,
	DoctorAbsenceListCreateView,
	DoctorAbsencePreviewView,
	DoctorBreakDetailView,
	DoctorBreakListCreateView,
	DoctorHoursDetailView,
	DoctorHoursListCreateView,
	PracticeHoursDetailView,
	PracticeHoursListCreateView,
)

# Doctors
from .doctor_views import DoctorListView

# Resources
from .resources_api import ResourceDetailView, ResourceListCreateView

# Availability
from .availability_api import AvailabilityView

# Resource calendar
from .resource_calendar import ResourceCalendarResourcesView, ResourceCalendarView

# Patient flow
from .patient_flow import (
	PatientFlowDetailView,
	PatientFlowListCreateView,
	PatientFlowLiveView,
	PatientFlowStatusUpdateView,
)

# OP timeline
from .op_timeline import OpTimelineLiveView, OpTimelineRoomsView, OpTimelineView

# OP stats
from .op_stats import (
	OpStatsDevicesView,
	OpStatsOverviewView,
	OpStatsRoomsView,
	OpStatsSurgeonsView,
	OpStatsTypesView,
)

