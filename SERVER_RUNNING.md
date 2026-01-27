# PraxiApp Server - Läuft ✅

## Server-Status

**Status:** Development Server aktiv  
**URL:** http://localhost:8000  
**Zeit:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Verfügbare URLs:

### Dashboard & UI:
- **Haupt-Dashboard:** http://localhost:8000/praxi_backend/dashboard/
- **Patientenliste:** http://localhost:8000/praxi_backend/dashboard/patients/
- **Terminplanung (Kalender):** http://localhost:8000/praxi_backend/dashboard/appointments/
- **Ärzte:** http://localhost:8000/praxi_backend/dashboard/doctors/
- **Operationen:** http://localhost:8000/praxi_backend/dashboard/operations/
- **Scheduling:** http://localhost:8000/praxi_backend/dashboard/scheduling/
- **Ressourcen:** http://localhost:8000/praxi_backend/dashboard/resources/

### Admin:
- **PraxiApp Admin:** http://localhost:8000/praxi_backend/
- **Django Admin:** http://localhost:8000/admin/

### API:
- **API Root:** http://localhost:8000/api/
- **Appointments:** http://localhost:8000/api/appointments/
- **Calendar:** http://localhost:8000/api/calendar/week/
- **Patients:** http://localhost:8000/api/patients/
- **Doctors:** http://localhost:8000/api/appointments/doctors/

## Wichtige Features:

### ✅ Terminplanung (Kalender)
- **Moderner FullCalendar** mit Drag & Drop
- **Termine anzeigen, bearbeiten, neu anlegen**
- **Verschieben per Drag & Drop**
- **Dauer ändern per Resize**
- **Wochen-, Tages- und Monatsansicht**

### ✅ Patientenliste
- **Moderne Tabelle** mit Such- und Filterfunktion
- **Keine IDs sichtbar** - nur sprechende Namen

### ✅ Design System
- **Fluent UI inspiriert**
- **Ruhige Pastellfarben**
- **Moderne Komponenten**

## Server stoppen:

```powershell
# Prozess beenden
Get-Process python | Where-Object {$_.Path -like "*\.venv*"} | Stop-Process -Force
```

## Logs anzeigen:

Der Server läuft im Hintergrund. Logs werden in der Konsole ausgegeben, wo der Server gestartet wurde.

## Nächste Schritte:

1. Öffne http://localhost:8000/praxi_backend/dashboard/ im Browser
2. Teste die verschiedenen Masken und Funktionen
3. Prüfe die Browser-Konsole (F12) auf Fehler
4. Teste die Terminplanung mit Drag & Drop

---

**Status:** Server läuft und ist bereit für Tests 🚀
