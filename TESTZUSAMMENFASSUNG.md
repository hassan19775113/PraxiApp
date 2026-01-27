# Testvorbereitung - Zusammenfassung

## ✅ Erstellt

### 1. Dokumentation

- **`TESTVORBEREITUNG_VOLLSTAENDIG.md`**: Vollständige Testvorbereitungs-Dokumentation
  - Liste aller Masken/Seiten mit URLs, Templates, Views, CSS/JS-Dateien
  - Alle Test-URLs (mit korrektem Prefix `/praxi_backend/dashboard/`)
  - Detaillierte Funktionstest-Anleitungen
  - Technische Tests (Templates, CSS, JS, API-Endpoints)
  - Checkliste für vollständige Tests
  - Fehlerbehebung und Lösungen

- **`TEST_QUICKSTART.md`**: Schnellstart-Anleitung (5 Minuten)
  - Server starten
  - Testdaten erstellen
  - Haupt-URLs
  - Wichtigste Funktionen

### 2. Management Command

- **`praxi_backend/dashboard/management/commands/create_test_data.py`**: Erstellt Testdaten
  - 5 Ärzte (mit calendar_color)
  - 5 Terminarten
  - 9 Ressourcen (4 Räume, 3 Geräte, 2 Personal-Ersatz als Geräte)
  - ~70 Termine für die nächsten 2 Wochen (Mo-Fr)

**Verwendung:**
```bash
python manage.py create_test_data
```

**Option:**
```bash
python manage.py create_test_data --clear  # Löscht zuerst Testdaten
```

---

## 📋 Wichtige URLs

**Basis-URL:** `http://localhost:8000`

**Dashboard-URLs (Prefix: `/praxi_backend/dashboard/`):**
- `/praxi_backend/dashboard/` - Haupt-Dashboard
- `/praxi_backend/dashboard/patients/overview/` - Patientenliste (PatientOverviewView)
- `/praxi_backend/dashboard/appointments/` - Terminplanung (FullCalendar)
- `/praxi_backend/dashboard/scheduling/` - Scheduling-Dashboard
- `/praxi_backend/dashboard/operations/` - Operations-Dashboard
- `/praxi_backend/dashboard/doctors/` - Doctors-Dashboard
- `/praxi_backend/dashboard/resources/` - Ressourcen & Räume
- `/admin/` - Django Admin

**API-URLs (Prefix: `/api/`):**
- `/api/appointments/` - Termine (GET, POST)
- `/api/appointments/doctors/` - Ärzte-Liste (GET)
- `/api/resources/` - Ressourcen (GET)
- `/api/auth/login/` - JWT Login (POST)

---

## 🧪 Testdaten

**Management Command erstellt:**
- **Ärzte:** 5 Ärzte (Username: `dr_mueller`, `dr_schmidt`, `dr_weber`, `dr_fischer`, `dr_wagner`, Passwort: `test123`)
- **Terminarten:** 5 Typen (Konsultation, Nachsorge, Operation, Vorsorge, Beratung)
- **Ressourcen:** 9 Ressourcen (4 Räume, 3 Geräte, 2 Personal-Ersatz)
- **Termine:** ~70 Termine (verteilt über 2 Wochen, Mo-Fr, verschiedene Status)

**Alternative:** Django Admin (`/admin/`) für manuelle Daten-Erstellung

---

## 🔍 Test-Schritte

### 1. Vorbereitung
```bash
# Server starten
python manage.py runserver

# Testdaten erstellen (in neuem Terminal)
python manage.py create_test_data
```

### 2. Browser-Tests

1. **Dashboard öffnen:** `http://localhost:8000/praxi_backend/dashboard/`
2. **Patientenliste testen:** `http://localhost:8000/praxi_backend/dashboard/patients/`
   - Suche testen
   - Filter testen
3. **Terminplanung testen:** `http://localhost:8000/praxi_backend/dashboard/appointments/`
   - Kalender-Ansicht wechseln (Tag, Woche, Monat)
   - Termin per Drag & Drop verschieben
   - Termin per Resize (Größe ändern) anpassen
   - Termin anklicken (Detail-Dialog)
   - Doppelklick für neuen Termin
4. **Termin-Dialog testen:**
   - Autocomplete (Patient, Arzt, Raum)
   - Termin anlegen/bearbeiten
   - Validierung
5. **Weitere Dashboards:** Scheduling, Operations, Doctors, Ressourcen

### 3. Technische Tests

- **Browser-Konsole (F12):** Keine JavaScript-Fehler
- **Network-Tab:** CSS/JS-Dateien werden geladen (Status 200)
- **API-Calls:** API-Endpoints erreichbar (Status 200)
- **HTML-Inspector:** Keine IDs im sichtbaren Text

---

## ⚠️ Bekannte Einschränkungen

1. **Resource.TYPE_STAFF:** Nicht verfügbar im Model → Personal wird als `TYPE_DEVICE` erstellt
2. **Patienten-IDs:** Termine verwenden Dummy-IDs (1-10), falls keine Patienten in `medical` DB vorhanden
3. **Authentifizierung:** `staff_member_required` Decorator auf Views → Superuser-Login erforderlich

---

## 📚 Vollständige Dokumentation

Siehe: **`TESTVORBEREITUNG_VOLLSTAENDIG.md`** für:
- Detaillierte Anleitungen für jede Maske
- Funktionstest-Schritte
- Technische Tests
- Fehlerbehebung
- Checkliste

---

**Erstellt:** $(date)  
**Version:** 1.0

