"""Deprecated legacy seeder.

Use `praxi_backend.patients.seeders.seed_patients()`.
"""

def seed_medical() -> dict:  # pragma: no cover
	return {"medical_patients": 0}
