"""praxi_backend.appointments.scheduling_facade

Official scheduling entry point.

Phase 2A goal:
- Stop scheduling divergence in the *request path* by ensuring views/serializers/
  validators import scheduling capabilities from a single module.

Important constraints:
- No behavior changes: this module only delegates to existing implementations.
- We intentionally keep the two implementations for now, but callers must not
  import them directly.

Separation of concerns (current state):
- Suggestion/availability helpers live in ``praxi_backend.appointments.scheduling``.
- Conflict/planning helpers live in ``praxi_backend.appointments.services.scheduling``.

In Phase 2+ we can consider deeper consolidation, but Phase 2A is strictly
routing/adapter work.
"""

from __future__ import annotations

# Suggestion engine + availability (legacy module)
from .scheduling import availability_for_range  # noqa: F401
from .scheduling import (  # noqa: F401
    ceil_dt_to_minutes,
    compute_suggestions_for_doctor,
    doctor_display_name,
    get_active_doctors,
    iso_z,
    resolve_doctor,
    resolve_type,
)

# Conflict / planning engine (service module)
from .services.scheduling import filter_available_patients  # noqa: F401
from .services.scheduling import (  # noqa: F401
    get_available_doctors,
    get_available_rooms,
    plan_appointment,
    plan_operation,
)
