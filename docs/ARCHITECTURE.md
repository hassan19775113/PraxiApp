# Architektur (PraxiApp Backend)

## Systemkontext

PraxiApp ist ein Backend für Praxisprozesse mit folgenden Hauptkomponenten:

- **REST API** (DRF) für Termin-/OP-/Ressourcen-/PatientFlow-Operationen
- **Dashboard UI** (server-rendered Django Templates) für Staff
- **Single-Datenbank-Architektur**:
  - `default`: Django-managed Systemdaten + fachliche Planungsdaten (PostgreSQL)
- **RBAC** (rollenbasiert) und **Audit Logging**

## Komponentenübersicht

### Django Project

- Root URLs: `praxi_backend/urls.py`
  - `/api/` inkludiert `core`, `appointments`, `patients`
  - `/praxi_backend/dashboard/` (Dashboard)
  - `/praxi_backend/` (Custom Admin)

### Apps

#### `praxi_backend.core`

- Modelle: `Role`, `User`, `AuditLog`
- Auth:
  - JWT Login/Refresh/Me
- Utility:
  - `log_patient_action(user, action, patient_id=None, meta=None)`

#### `praxi_backend.appointments`

- Terminplanung:
  - `Appointment`, `AppointmentType`
  - `PracticeHours`, `DoctorHours`, `DoctorAbsence`, `DoctorBreak`
  - `Resource` (room/device), `AppointmentResource`
- OP-Planung:
  - `Operation`, `OperationType`, `OperationDevice`
  - OP Dashboard / Timeline / Stats
- Patientenfluss:
  - `PatientFlow` (Statuskette; appointment oder operation)

Scheduling-Engine:
- `praxi_backend/appointments/scheduling.py`
  - scannt Tage, erzeugt Zeitslots in 5-Minuten-Schritten
  - blockiert bei Konflikten:
    - existierende Termine
    - Pausen/Abwesenheiten
    - Ressourcenbelegung (auch OP-Raum/OP-Geräte)

#### `praxi_backend.patients` (Managed)

- Tabelle: `patients`
- Zweck: Patient-Stammdaten als managed Model (`Patient`) im Default-DB

#### `praxi_backend.dashboard`

- Staff-only Views (z. B. Kalenderdarstellungen)
- primär HTML-rendering; Ajax API für KPI-Refresh

## Datenmodell-Kernelemente

### Patientenreferenz

- `patient_id: int` ist die **kanonische** Referenz auf den Patienten.
- Keine ForeignKey-Kopplung in Appointments/Operations (Kompatibilität).

### Ressourcen

- `Resource.type ∈ {room, device}`
- Termine nutzen Ressourcen via `AppointmentResource` (M2M)
- OPs nutzen OP-Raum (FK) + OP-Geräte (M2M via `OperationDevice`)

### PatientFlow

- Ein Flow gehört zu genau einem Kontext:
  - entweder `appointment` oder `operation` (beide optional, aber fachlich i. d. R. genau eins)

## Querschnitt: RBAC

- Viele Permissions folgen dem Muster `read_roles`/`write_roles`.
- Typische Regeln:
  - billing: read-only
  - doctor: eingeschränkt (eigene Records; teils nur GET)

## Querschnitt: Audit Logging

- Audit schreibt in `core.AuditLog` (System-DB `default`).
- Logging soll keine PHI enthalten (nur `patient_id` + Action + Meta ohne PII).

## Deployment-Architektur

- DEV: `praxi_backend.settings.dev`, PostgreSQL (localhost), optional Docker-Compose dev Stack
- PROD: `praxi_backend.settings.prod`, PostgreSQL + Redis, Nginx + Gunicorn, WhiteNoise für static

Siehe auch `DEPLOYMENT.md`.
