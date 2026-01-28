# Migrationsplan (DEPRECATED)

Dieses Dokument beschreibt einen alten Plan für eine Dual-DB-Architektur.
Die Codebase nutzt inzwischen **eine** Datenbank (`default`).

## 0) Voraussetzungen

1) System-DB existiert (Default-Name ist `praxiapp_system`, anpassbar über `SYS_DB_NAME`).
2) Zugangsdaten/Host/Port sind korrekt gesetzt.

Empfohlene ENV Vars (Beispiele):

- System-DB:
  - `SYS_DB_NAME=praxiapp_system`
  - `SYS_DB_USER=postgres`
  - `SYS_DB_PASSWORD=`
  - `SYS_DB_HOST=localhost`
  - `SYS_DB_PORT=5432`


Hinweis: `MED_DB_*` Variablen werden nicht mehr verwendet.

## 1) Vorab-Check (read-only)

- `python manage.py check`
- Optional: `python manage.py shell -c "from django.db import connections; connections['default'].cursor().execute('SELECT 1'); print('ok')"`

## 2) Migrationen

WICHTIG: Migrationen werden **nur** auf `default` angewendet.

- `python manage.py migrate --database=default`

Falls die System-DB noch nicht existiert:
- DB einmalig anlegen (z.B. via `createdb praxiapp_system` oder über pgAdmin), dann erst migrieren.

Erwartung:
- Django legt/aktualisiert nur Systemtabellen + `core_*` Tabellen in der System-DB.
- Auf `medical` darf *nichts* migriert werden.

## 3) Superuser (nur System-DB)

- `python manage.py createsuperuser`

## 4) Rollen seed (optional, später)

- Minimal: Roles `doctor`, `assistant`, `admin`, `billing` in `core_role` anlegen.

## 5) Legacy-Patienten (Import)

- Patient-Stammdaten werden über `praxi_backend.patients` verwaltet.
- Import aus Alt-Systemen erfolgt über Management Commands im `patients` App.
