
"""Deprecated legacy `medical` app.

PraxiApp no longer uses a separate `medical` database or the `praxi_backend.medical`
application. Patient master data is now stored in the managed `praxi_backend.patients`
app/table on the default database.

This package remains as a stub only to avoid breaking stale imports in external
scripts. It is not installed in `INSTALLED_APPS`.
"""

