"""Central audit logging facade.

Phase 2E goal:
- Centralize audit entry points in one module.
- Keep implementation stable by delegating to the existing implementation.

IMPORTANT:
- Do not add side-effects to validators/services.
- Views (or higher-level request handlers) are responsible for deciding *when*
  to audit. This module only provides the write primitives.
"""

from __future__ import annotations

from praxi_backend.core import utils as core_utils


def log_patient_action(user, action, patient_id=None, meta=None):
	"""Write a patient-related audit entry.

	Delegates to the legacy implementation in `praxi_backend.core.utils`.
	Signature and behavior are intentionally unchanged.
	"""
	return core_utils.log_patient_action(user, action, patient_id, meta=meta)
