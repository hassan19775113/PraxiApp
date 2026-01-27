# CSRF Token Fix ✅

## Problem

**Fehlermeldung:**
> "Fehler beim Speichern: CSRF Failed: CSRF token missing."

**Ursache:**
- In Development-Mode ist `SessionAuthentication` aktiviert (für Browsable API)
- Bei SessionAuthentication erfordert Django REST Framework CSRF-Token für POST/PATCH/DELETE-Requests
- Die JavaScript-Funktion `save()` sendet keine CSRF-Token mit

## Lösung

### 1. getCsrfToken() Methode hinzugefügt ✅

**Geänderte Datei:** `praxi_backend/static/js/appointment-dialog.js`

**Neue Methode:**
```javascript
getCsrfToken() {
    // CSRF-Token aus Cookie holen (für SessionAuthentication in Development)
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

### 2. save() Methode aktualisiert ✅

**Geänderte Datei:** `praxi_backend/static/js/appointment-dialog.js`

**Vorher:**
```javascript
const response = await fetch(url, {
    method: method,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': this.getAuthHeader()
    },
    body: JSON.stringify(data)
});
```

**Nachher:**
```javascript
// Headers vorbereiten
const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
};

// JWT Token hinzufügen (falls vorhanden)
const authHeader = this.getAuthHeader();
if (authHeader) {
    headers['Authorization'] = authHeader;
}

// CSRF Token hinzufügen (für SessionAuthentication in Development)
const csrfToken = this.getCsrfToken();
if (csrfToken) {
    headers['X-CSRFToken'] = csrfToken;
}

const response = await fetch(url, {
    method: method,
    headers: headers,
    body: JSON.stringify(data),
    credentials: 'same-origin'  // Wichtig für Cookies (CSRF)
});
```

## Warum CSRF-Token?

### Development-Mode:
- `SessionAuthentication` ist aktiviert (für Browsable API)
- SessionAuthentication erfordert CSRF-Token für POST/PATCH/DELETE-Requests
- Django setzt CSRF-Token automatisch als Cookie (`csrftoken`)

### Production-Mode:
- Nur `JWTAuthentication` aktiviert
- CSRF-Token nicht erforderlich (JWT-Token reicht)

## Funktionsweise

1. **CSRF-Token aus Cookie holen:**
   - Django setzt CSRF-Token automatisch als Cookie `csrftoken`
   - Die `getCsrfToken()` Methode liest das Token aus dem Cookie

2. **CSRF-Token zu Headers hinzufügen:**
   - Django REST Framework erwartet CSRF-Token im Header `X-CSRFToken`
   - Das Token wird nur hinzugefügt, wenn es vorhanden ist (optional)

3. **Credentials mitgeben:**
   - `credentials: 'same-origin'` ist wichtig, damit Cookies mitgesendet werden
   - Ermöglicht CSRF-Token-Validierung auf dem Server

## Testing

1. **Browser-Konsole öffnen** (F12)
2. **"Neuer Termin" Button** klicken
3. **Formular ausfüllen** und speichern
4. **Prüfen:**
   - Erwartung: Termin wird erfolgreich gespeichert
   - Keine CSRF-Fehlermeldung mehr
   - Kalender wird aktualisiert

## Geänderte Dateien

1. **`praxi_backend/static/js/appointment-dialog.js`**:
   - `getCsrfToken()` Methode hinzugefügt
   - `save()` Methode aktualisiert, um CSRF-Token zu verwenden
   - `credentials: 'same-origin'` hinzugefügt

## Nächste Schritte

1. **Browser-Cache leeren** (Strg+Shift+R)
2. **Termin erstellen:**
   - "Neuer Termin" Button klicken
   - Formular ausfüllen
   - Speichern klicken
3. **Prüfen:**
   - Termin wird erfolgreich gespeichert
   - Keine CSRF-Fehlermeldung mehr

---

**Status:** ✅ CSRF-Token-Unterstützung implementiert


