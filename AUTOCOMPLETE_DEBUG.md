# Autocomplete Debugging Guide 🔍

## Problem
Der Benutzer meldet, dass die Autocomplete-Funktionalität nicht funktioniert.

## Implementierte Verbesserungen

### 1. Erweiterte Debug-Logs ✅
- Alle API-Aufrufe werden jetzt geloggt
- Response-Status wird angezeigt
- Anzahl der geladenen Items wird geloggt
- Fehler werden detailliert ausgegeben

### 2. Verbesserte Fehlerbehandlung ✅
- API-Fehler werden jetzt angezeigt (nicht nur ignoriert)
- Fehlermeldungen in der Dropdown-Liste
- Prüfung ob alle DOM-Elemente existieren

### 3. Detaillierte Konsolen-Ausgaben ✅
- `[AppointmentDialog] Loading items for...` - Zeigt welches Feld geladen wird
- `[AppointmentDialog] Fetching from: ...` - Zeigt die API-URL
- `[AppointmentDialog] Response status: ...` - Zeigt HTTP-Status
- `[AppointmentDialog] Received X items` - Zeigt Anzahl der Items
- `[AppointmentDialog] Dropdown displayed` - Bestätigt dass Dropdown angezeigt wird

## Debugging-Schritte

### 1. Browser-Konsole öffnen (F12)
Prüfen Sie die Konsolen-Ausgaben:

**Erwartete Logs beim Fokus auf Patient-Feld:**
```
[AppointmentDialog] Focus event on appointmentPatient
[AppointmentDialog] Loading items for appointmentPatient, query: ""
[AppointmentDialog] Fetching from: /api/medical/patients/search/
[AppointmentDialog] Response status: 200 OK
[AppointmentDialog] Received 50 items for appointmentPatient
[AppointmentDialog] Dropdown displayed for appointmentPatient
```

**Mögliche Fehler:**
```
[AppointmentDialog] API error (403): {"detail": "You do not have permission..."}
[AppointmentDialog] API error (404): Not Found
[AppointmentDialog] Autocomplete error: TypeError: ...
```

### 2. Network-Tab prüfen
1. Öffnen Sie den Network-Tab (F12 → Network)
2. Fokussieren Sie ein Feld (Patient, Arzt, Raum)
3. Prüfen Sie die API-Requests:
   - **URL:** Sollte korrekt sein (z.B. `/api/medical/patients/search/`)
   - **Status:** Sollte `200 OK` sein
   - **Response:** Sollte JSON mit Patienten/Ärzten/Räumen enthalten

### 3. Mögliche Probleme und Lösungen

#### Problem: 403 Forbidden
**Ursache:** Keine Berechtigung für den API-Endpoint
**Lösung:** 
- Prüfen Sie, ob der Benutzer eingeloggt ist
- Prüfen Sie die Permissions in `praxi_backend/medical/views.py`

#### Problem: 404 Not Found
**Ursache:** API-Endpoint existiert nicht
**Lösung:**
- Prüfen Sie die URL-Struktur in `praxi_backend/medical/urls.py`
- Prüfen Sie die URL-Mappings in `praxi_backend/urls.py`

#### Problem: Dropdown wird nicht angezeigt
**Ursache:** CSS-Probleme oder JavaScript-Fehler
**Lösung:**
- Prüfen Sie die CSS-Klassen in `components-modern.css`
- Prüfen Sie ob `dropdown.style.display = 'block'` aufgerufen wird
- Prüfen Sie die Dropdown-Position (sollte relativ zum Input sein)

#### Problem: Keine Items in der Dropdown-Liste
**Ursache:** API gibt leere Liste zurück
**Lösung:**
- Prüfen Sie die Datenbank (gibt es Patienten/Ärzte/Räume?)
- Prüfen Sie die API-Response im Network-Tab
- Prüfen Sie die Filter-Logik in `PatientSearchView`

## Test-Checkliste

- [ ] Browser-Konsole öffnen (F12)
- [ ] "Neuer Termin" Button klicken
- [ ] Patient-Feld fokussieren
- [ ] Prüfen: Werden Logs angezeigt?
- [ ] Prüfen: Wird API-Request gesendet?
- [ ] Prüfen: Ist Response-Status 200?
- [ ] Prüfen: Werden Items in der Dropdown-Liste angezeigt?
- [ ] Wiederholen für Arzt-Feld
- [ ] Wiederholen für Raum-Feld

## Nächste Schritte

1. **Browser-Konsole öffnen** und die Logs prüfen
2. **Network-Tab öffnen** und die API-Requests prüfen
3. **Fehlermeldungen notieren** und mir mitteilen
4. **Screenshots** der Browser-Konsole und Network-Tab senden

---

**Status:** ✅ Debug-Logs hinzugefügt, Fehlerbehandlung verbessert

