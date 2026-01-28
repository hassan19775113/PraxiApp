"""Deprecated database router module.

PraxiApp previously used a dual-database architecture (default + medical).
The codebase has been migrated to a *single database* setup.

This file is kept as a small stub for backwards compatibility with older docs
or deployment scripts. It is no longer referenced by settings.
"""


class PraxiAppRouter:  # pragma: no cover
	"""Deprecated: router not used in the single-DB architecture."""

	def __getattr__(self, name):
		raise AttributeError(
			"PraxiAppRouter is deprecated; the project no longer uses multi-DB routing."
		)
