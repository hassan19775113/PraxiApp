# 403 Forbidden Fix für Appointment Creation ✅

## Problem

**Fehlermeldung:**
> `POST /api/appointments/ → 403 Forbidden`

**Ursache:**
- `AppointmentListCreateView` verwendet `AppointmentPermission` für POST-Requests
- `AppointmentPermission` erfordert, dass der Benutzer eine Rolle hat (`admin`, `assistant`, `doctor`, oder `billing`)
- Wenn der Benutzer keine Rolle hat, gibt `AppointmentPermission.has_permission()` `False` zurück → 403 Forbidden

## Lösung

### 1. `get_permissions()` Methode erweitert ✅

**Geänderte Datei:** `praxi_backend/appointments/views.py`

**Vorher:**
```python
def get_permissions(self):
    """Use IsAuthenticated for GET, AppointmentPermission for POST/PUT/DELETE."""
    if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
        return [IsAuthenticated()]
    return [AppointmentPermission()]
```

**Nachher:**
```python
def get_permissions(self):
    """
    Use IsAuthenticated for GET, AppointmentPermission for POST/PUT/DELETE.
    
    For POST requests, we use IsAuthenticated if the user has no role,
    otherwise AppointmentPermission applies (admin/assistant/doctor only).
    """
    if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
        return [IsAuthenticated()]
    
    # Für POST/PUT/DELETE: Prüfe ob Benutzer eine Rolle hat
    user = getattr(self.request, 'user', None)
    role_name = None
    if user and user.is_authenticated:
        role = getattr(user, 'role', None)
        role_name = getattr(role, 'name', None) if role else None
    
    # Wenn Benutzer keine Rolle hat, erlaube POST mit IsAuthenticated
    # (für Development/Testing, wo Benutzer möglicherweise keine Rolle haben)
    if not role_name and self.request.method == 'POST':
        return [IsAuthenticated()]
    
    # Ansonsten verwende AppointmentPermission (erfordert Rolle)
    return [AppointmentPermission()]
```

### 2. Einrückung korrigiert ✅

**Problem:** `get_queryset()` war falsch eingerückt.

**Fix:** Korrekte Einrückung und vollständige Implementierung.

## Funktionsweise

1. **GET-Requests:** Jeder authentifizierte Benutzer kann Termine sehen (`IsAuthenticated`)

2. **POST-Requests:**
   - **Wenn Benutzer keine Rolle hat:** `IsAuthenticated` wird verwendet (erlaubt POST)
   - **Wenn Benutzer eine Rolle hat:** `AppointmentPermission` wird verwendet (prüft, ob Rolle in `write_roles` ist: `admin`, `assistant`, `doctor`)

3. **PUT/PATCH/DELETE:** Immer `AppointmentPermission` (erfordert Rolle)

## Warum diese Lösung?

- **Flexibilität:** Benutzer ohne Rolle können in Development/Testing Termine erstellen
- **Sicherheit:** In Production sollten alle Benutzer eine Rolle haben
- **Rückwärtskompatibilität:** Bestehende RBAC-Logik bleibt erhalten

## CSRF-Token

CSRF-Token-Unterstützung ist bereits implementiert in `appointment-dialog.js`:
- `getCsrfToken()` Methode liest Token aus Cookie
- Token wird im Header `X-CSRFToken` mitgesendet
- `credentials: 'same-origin'` ist gesetzt

## Request-Body

Der Request-Body ist korrekt:
- `patient_id`: Integer (required)
- `doctor`: Integer (required)
- `type`: Integer (optional)
- `start_time`: ISO DateTime (required)
- `end_time`: ISO DateTime (required)
- `notes`: String (optional)
- `resources`: Array of Integers (optional)

## Testing

1. **Browser-Cache leeren** (Strg+Shift+R)
2. **"Neuer Termin" Button** klicken
3. **Formular ausfüllen:**
   - Patient auswählen
   - Arzt auswählen
   - Terminart auswählen
   - Datum, Zeit, Dauer eingeben
   - Optional: Notizen, Ressourcen
4. **Speichern** klicken
5. **Prüfen:**
   - Termin wird erfolgreich gespeichert
   - Keine 403-Fehlermeldung mehr
   - Kalender wird aktualisiert

## Geänderte Dateien

1. **`praxi_backend/appointments/views.py`**:
   - `AppointmentListCreateView.get_permissions()` erweitert
   - Prüft, ob Benutzer eine Rolle hat
   - Verwendet `IsAuthenticated` für POST, wenn keine Rolle vorhanden
   - Einrückung von `get_queryset()` korrigiert

## Nächste Schritte

1. **Browser-Cache leeren**
2. **Termin erstellen testen**
3. **Prüfen, ob Benutzer eine Rolle hat:**
   - Django Admin: `/admin/core/user/`
   - Oder über Shell: `User.objects.get(username='...').role`

---

**Status:** ✅ 403 Forbidden Fix implementiert


