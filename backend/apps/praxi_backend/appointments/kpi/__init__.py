"""Central KPI + chart layer for PraxiApp.

Phase 2F goal:
- Dashboard should be a pure consumer.
- KPI/Chart definitions should live in the appointments domain layer.

Important constraints:
- No behavior changes: payload shapes and KPI definitions must remain identical.
- This module intentionally mirrors the previous public function surface that
  `praxi_backend.dashboard.services` consumed.
"""

from __future__ import annotations

# Main dashboard KPIs/charts
from praxi_backend.appointments.kpi.main_kpis import get_all_kpis  # noqa: F401
from praxi_backend.appointments.kpi.main_charts import get_all_charts  # noqa: F401

# Doctors dashboard KPIs/charts
from praxi_backend.appointments.kpi.doctor_kpis import (  # noqa: F401
	get_active_doctors,
	get_all_doctor_kpis,
	get_doctor_comparison_data,
	get_doctor_profile,
)
from praxi_backend.appointments.kpi.doctor_charts import get_all_doctor_charts  # noqa: F401

# Operations dashboard KPIs/charts
from praxi_backend.appointments.kpi.operations_kpis import (  # noqa: F401
	get_all_operations_kpis,
	get_realtime_operations_kpis,
)
from praxi_backend.appointments.kpi.operations_charts import get_all_operations_charts  # noqa: F401

# Scheduling dashboard KPIs/charts
from praxi_backend.appointments.kpi.scheduling_kpis import get_all_scheduling_kpis  # noqa: F401
from praxi_backend.appointments.kpi.scheduling_charts import get_all_scheduling_charts  # noqa: F401

# Patient dashboard KPIs/charts
from praxi_backend.appointments.kpi.patient_kpis import (  # noqa: F401
	calculate_patient_risk_score,
	calculate_patient_status,
	get_all_patient_kpis,
	get_patient_overview_stats,
	get_patient_profile,
)
from praxi_backend.appointments.kpi.patient_charts import get_all_patient_charts  # noqa: F401
