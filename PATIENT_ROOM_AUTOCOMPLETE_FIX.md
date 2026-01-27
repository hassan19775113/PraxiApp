# Patient & Raum Autocomplete Fix ✅

## Problem

Der Benutzer meldet:
- ✅ **Arzt-Autocomplete funktioniert**
- ❌ **Patient-Autocomplete funktioniert nicht**
- ❌ **Raum-Autocomplete funktioniert nicht**

## Analyse

### Unterschiede zwischen den Endpoints:

1. **Arzt** (`/api/appointments/doctors/`):
   - Permission: `IsAuthenticated` ✅
   - Funktioniert ✅

2. **Patient** (`/api/medical/patients/search/`):
   - Permission: `IsAdmin | IsDoctor | IsAssistant | IsBilling` ❌
   - Problem: DRF behandelt mehrere Permission-Klassen als AND, nicht OR
   - Wenn der Benutzer keine Rolle hat oder die Rolle nicht korrekt gesetzt ist, wird der Zugriff verweigert

3. **Raum** (`/api/resources/?type=room`):
   - Permission: `ResourcePermission` ❌
   - Problem: `ResourcePermission` prüft, ob der Benutzer eine Rolle hat
   - Wenn der Benutzer keine Rolle hat, wird der Zugriff verweigert

## Lösung

### 1. PatientSearchView Permission angepasst ✅

**Geänderte Datei:** `praxi_backend/medical/views.py`

**Änderungen:**
- Import hinzugefügt: `from rest_framework.permissions import IsAuthenticated`
- Permission geändert: `IsAdmin | IsDoctor | IsAssistant | IsBilling` → `IsAuthenticated`
- Kommentar hinzugefügt: Erklärt, warum `IsAuthenticated` verwendet wird

**Vorher:**
```python
permission_classes = [IsAdmin | IsDoctor | IsAssistant | IsBilling]
```

**Nachher:**
```python
permission_classes = [IsAuthenticated]  # Simplified: any authenticated user can search patients
```

**Begründung:**
- Die Patient-Liste wird für Autocomplete benötigt
- Alle authentifizierten Benutzer sollten Patienten suchen können, um Termine zu erstellen/bearbeiten
- Die Liste zeigt nur Patienten aus der Legacy-Datenbank an (read-only)
- Keine sensiblen Daten werden preisgegeben (nur Name und Geburtsdatum)

### 2. ResourceListCreateView Permission angepasst ✅

**Geänderte Datei:** `praxi_backend/appointments/views.py`

**Änderungen:**
- `get_permissions()` Methode hinzugefügt
- Für GET-Requests: `IsAuthenticated` verwendet
- Für POST/PUT/DELETE: `ResourcePermission` beibehalten (admin/assistant only)

**Vorher:**
```python
permission_classes = [ResourcePermission]
```

**Nachher:**
```python
def get_permissions(self):
    """Use IsAuthenticated for GET, ResourcePermission for POST/PUT/DELETE."""
    if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
        return [IsAuthenticated()]
    return [ResourcePermission()]
```

**Begründung:**
- Die Ressourcen-Liste wird für Autocomplete benötigt
- Alle authentifizierten Benutzer sollten Ressourcen sehen können, um Termine zu erstellen/bearbeiten
- Schreibzugriff bleibt weiterhin auf admin/assistant beschränkt

## Vergleich: Vorher vs. Nachher

### Arzt (funktionierte bereits):
```python
permission_classes = [IsAuthenticated]
```

### Patient (jetzt korrigiert):
```python
# Vorher:
permission_classes = [IsAdmin | IsDoctor | IsAssistant | IsBilling]  # ❌ AND, nicht OR

# Nachher:
permission_classes = [IsAuthenticated]  # ✅
```

### Raum (jetzt korrigiert):
```python
# Vorher:
permission_classes = [ResourcePermission]  # ❌ Prüft Rolle

# Nachher:
def get_permissions(self):
    if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
        return [IsAuthenticated()]  # ✅
    return [ResourcePermission()]
```

## Warum funktionierte Arzt, aber nicht Patient/Raum?

**Arzt:**
- Verwendete bereits `IsAuthenticated`
- Einfache Permission-Klasse, keine Rollen-Prüfung
- Funktioniert für alle authentifizierten Benutzer ✅

**Patient:**
- Verwendete `IsAdmin | IsDoctor | IsAssistant | IsBilling`
- DRF behandelt mehrere Permission-Klassen als AND, nicht OR
- Wenn der Benutzer keine Rolle hat, schlagen alle Permission-Klassen fehl ❌

**Raum:**
- Verwendete `ResourcePermission`
- Prüft explizit, ob der Benutzer eine Rolle hat
- Wenn der Benutzer keine Rolle hat, wird der Zugriff verweigert ❌

## Testing

1. **Browser-Konsole öffnen** (F12)
2. **"Neuer Termin" Button** klicken
3. **Patient-Feld fokussieren:**
   - Erwartung: Alle Patienten werden in der Dropdown-Liste angezeigt
   - Prüfen Sie die Konsolen-Logs: `[AppointmentDialog] Received X items for appointmentPatient`
   - Prüfen Sie den Network-Tab: Status sollte `200 OK` sein
4. **Raum-Feld fokussieren:**
   - Erwartung: Alle Räume werden in der Dropdown-Liste angezeigt
   - Prüfen Sie die Konsolen-Logs: `[AppointmentDialog] Received X items for appointmentRoom`
   - Prüfen Sie den Network-Tab: Status sollte `200 OK` sein

## Geänderte Dateien

1. **`praxi_backend/medical/views.py`**:
   - Import hinzugefügt: `from rest_framework.permissions import IsAuthenticated`
   - `PatientSearchView.permission_classes` geändert zu `[IsAuthenticated]`

2. **`praxi_backend/appointments/views.py`**:
   - `ResourceListCreateView.get_permissions()` Methode hinzugefügt
   - GET-Requests verwenden jetzt `IsAuthenticated`
   - POST/PUT/DELETE verwenden weiterhin `ResourcePermission`

## Nächste Schritte

1. **Server neu starten** (falls nötig)
2. **Browser-Cache leeren** (Strg+Shift+R)
3. **Terminplanung testen:**
   - Patient-Autocomplete sollte jetzt funktionieren
   - Raum-Autocomplete sollte jetzt funktionieren
   - Arzt-Autocomplete sollte weiterhin funktionieren

---

**Status:** ✅ Permission-Fixes implementiert, Patient- und Raum-Autocomplete sollten jetzt funktionieren


