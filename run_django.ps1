# ---------------------------------------------
# run_django.ps1
# Startet die lokale Django-App auf Port 8000
# mit korrekten Environment-Variablen
# ---------------------------------------------

Write-Host "Starte lokale Django-Entwicklungsumgebung..." -ForegroundColor Cyan

# Pfad zur virtuellen Umgebung
$venv = "D:/PraxiApp/.venv/Scripts/python.exe"

# Django Settings
$env:DJANGO_SETTINGS_MODULE = "praxi_backend.settings.dev"

# Lokale Postgres-Datenbank
$env:DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/praxiapp_system"

# Optional: Debug aktivieren
$env:DEBUG = "True"

# Django starten
Write-Host "Starte Django-Server auf http://127.0.0.1:8000 ..." -ForegroundColor Green
& $venv "django/manage.py" runserver 0.0.0.0:8000
