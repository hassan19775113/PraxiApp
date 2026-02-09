# PostgreSQL-only checklist

- Install and start PostgreSQL locally (default port 5432).
- Set DATABASE_URL before running Django:
  - Windows PowerShell: `$env:DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DBNAME"`
  - macOS/Linux: `export DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME`
- Verify DATABASE_URL uses PostgreSQL:
  - `python - <<'PY'
import os, dj_database_url
cfg = dj_database_url.config(env="DATABASE_URL")
assert cfg["ENGINE"] == "django.db.backends.postgresql"
print("PostgreSQL confirmed")
PY`
- Run migrations:
  - `python django/manage.py migrate`
- Create a superuser if needed:
  - `python django/manage.py createsuperuser`
- Load local fixtures (optional):
  - `python django/manage.py loaddata path/to/fixture.json`
- Confirm runtime DB engine:
  - `python django/manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE'])"`
- Ensure no local SQLite files exist:
  - `Get-ChildItem -Recurse -Filter "*.sqlite*"` (PowerShell)
