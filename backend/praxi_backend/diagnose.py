import os
import socket
import subprocess
import sys

import psycopg
from dotenv import load_dotenv

print("\nPraxiApp Diagnose gestartet...\n")

# ---------------------------------------------------------
# 1. .env laden
# ---------------------------------------------------------
print("Schritt 1: Prüfe .env...")

if not os.path.exists(".env"):
    print("FEHLER: .env Datei fehlt!")
else:
    print("OK: .env gefunden")

load_dotenv()

required_vars = [
    "SYS_DB_NAME",
    "SYS_DB_USER",
    "SYS_DB_PASSWORD",
    "SYS_DB_HOST",
    "SYS_DB_PORT",
]

missing = [v for v in required_vars if not os.environ.get(v)]

if missing:
    print("FEHLER: Fehlende Variablen in .env:", missing)
else:
    print("OK: Alle benötigten Variablen vorhanden")

# ---------------------------------------------------------
# 2. PostgreSQL Verbindung testen
# ---------------------------------------------------------
print("\nSchritt 2: Teste PostgreSQL Verbindung...")

try:
    conn = psycopg.connect(
        dbname=os.environ.get("SYS_DB_NAME"),
        user=os.environ.get("SYS_DB_USER"),
        password=os.environ.get("SYS_DB_PASSWORD"),
        host=os.environ.get("SYS_DB_HOST"),
        port=os.environ.get("SYS_DB_PORT"),
        connect_timeout=3,
    )
    print("OK: Verbindung erfolgreich!")
    conn.close()
except Exception as e:
    print("FEHLER: Verbindung fehlgeschlagen:")
    print(e)

# ---------------------------------------------------------
# 3. Port 5432 prüfen
# ---------------------------------------------------------
print("\nSchritt 3: Prüfe Port 5432...")


host = os.environ.get("SYS_DB_HOST") or "127.0.0.1"
port = int(os.environ.get("SYS_DB_PORT") or "5432")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex((host, port))

if result == 0:
    print(f"OK: Port {port} ist offen ({host}:{port})")
else:
    print(f"FEHLER: Port {port} ist geschlossen — PostgreSQL läuft nicht ({host}:{port})")

sock.close()

# ---------------------------------------------------------
# 4. Django Struktur prüfen
# ---------------------------------------------------------
print("\nSchritt 4: Prüfe Django Struktur...")

if not os.path.exists("manage.py"):
    print("FEHLER: manage.py fehlt — falsches Verzeichnis?")
else:
    print("OK: manage.py gefunden")

apps = ["appointments", "core", "patients", "dashboard", "praxi_backend"]

for app in apps:
    if os.path.exists(app):
        print(f"OK: App gefunden: {app}")
    else:
        print(f"WARN: App fehlt: {app}")

# ---------------------------------------------------------
# 5. Migrationen testen
# ---------------------------------------------------------
print("\nSchritt 5: Teste Django (showmigrations)...")

try:
    result = subprocess.run(
        [sys.executable, "manage.py", "showmigrations"], capture_output=True, text=True
    )
    if result.returncode == 0:
        print("OK: Django ist funktionsfähig")
    else:
        print("FEHLER: Django showmigrations returncode != 0")
        print(result.stdout)
        print(result.stderr)
except Exception as e:
    print("FEHLER: Fehler beim Ausführen von Django:")
    print(e)

print("\nDiagnose abgeschlossen.\n")
