"""Deprecated database router module.

PraxiApp previously experimented with multi-database routing. The codebase has
since been migrated to a **single database** setup (`default`).

This file is kept as a tiny stub for backwards compatibility with older docs or
deployment scripts. It is not referenced by current settings.
"""


class PraxiAppRouter:  # pragma: no cover
    """Deprecated: router not used in the single-DB architecture."""

    def __getattr__(self, name):
        raise AttributeError(
            "PraxiAppRouter is deprecated; the project no longer uses multi-DB routing."
        )
