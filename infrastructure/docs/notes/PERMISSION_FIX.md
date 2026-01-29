# Permission-Fix für DoctorListView ✅

## Problem

**Fehler:** `HTTP 403 Forbidden` beim Zugriff auf `/api/appointments/doctors/`

**Ursache:** `AppointmentPermission` war zu restriktiv. Sie prüft:
1. Ob der Benutzer authentifiziert ist
2. Ob der Benutzer eine Rolle hat
3. Ob die Rolle in `read_roles` ist

Wenn der Benutzer keine Rolle hat oder die Rolle nicht korrekt gesetzt ist, wird der Zugriff verweigert.

## Lösung

**Geändert:** `DoctorListView` verwendet jetzt `IsAuthenticated` statt `AppointmentPermission`.

**Begründung:**
- Die Arzt-Liste enthält keine sensiblen Daten (nur Namen und Farben)
- Alle authentifizierten Benutzer sollten die Arzt-Liste sehen können, um Termine zu erstellen/bearbeiten
- Die Liste zeigt nur aktive Ärzte mit Rolle 'doctor' an

## Geänderte Dateien

- `praxi_backend/appointments/views.py`:
  - Import hinzugefügt: `from rest_framework.permissions import IsAuthenticated`
  - `DoctorListView.permission_classes` geändert von `[AppointmentPermission]` zu `[IsAuthenticated]`

## Nächste Schritte

1. Server neu starten (falls nötig)
2. Browser-Cache leeren
3. Terminplanung testen - Arzt-Autocomplete sollte jetzt funktionieren

---

**Status:** ✅ Permission-Fix implementiert

