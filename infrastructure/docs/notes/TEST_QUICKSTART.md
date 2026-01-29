# Quick Start - Browser-Tests

## Schnellstart (5 Minuten)

### 1. Server starten

```bash
python manage.py runserver
```

### 2. Testdaten erstellen

```bash
python manage.py create_test_data
```

Dies erstellt automatisch:
- ✅ 5 Ärzte
- ✅ 5 Terminarten
- ✅ 9 Ressourcen
- ✅ ~70 Termine

### 3. Browser öffnen

```
http://localhost:8000/dashboard/
```

**Hinweis:** Falls Authentifizierung erforderlich ist:
- Django Admin: `http://localhost:8000/admin/`
- Superuser-Login verwenden

---

## Haupt-URLs zum Testen

```
http://localhost:8000/praxi_backend/dashboard/              → Haupt-Dashboard
http://localhost:8000/praxi_backend/dashboard/patients/overview/     → Patientenliste
http://localhost:8000/praxi_backend/dashboard/appointments/ → Terminplanung (FullCalendar)
http://localhost:8000/praxi_backend/dashboard/scheduling/   → Scheduling-Dashboard
http://localhost:8000/praxi_backend/dashboard/operations/   → Operations-Dashboard
http://localhost:8000/praxi_backend/dashboard/doctors/      → Doctors-Dashboard
http://localhost:8000/praxi_backend/dashboard/resources/    → Ressourcen & Räume
http://localhost:8000/admin/                             → Django Admin
```

---

## Wichtigste Funktionen zum Testen

### Terminplanung
1. **Kalender öffnen:** `/praxi_backend/dashboard/appointments/`
2. **Termin verschieben:** Drag & Drop
3. **Termin-Größe ändern:** Resize (unterer Rand ziehen)
4. **Termin bearbeiten:** Einfachklick
5. **Neuer Termin:** Doppelklick oder Button "Neuer Termin"

### Termin-Dialog
1. **Autocomplete testen:** In Patient/Arzt/Raum-Feld tippen
2. **Termin anlegen:** Alle Felder ausfüllen, "Speichern"

### Patientenliste
1. **Suche testen:** In Suchfeld tippen
2. **Filter testen:** Status/Risiko-Filter auswählen

---

## Vollständige Dokumentation

Siehe: `TESTVORBEREITUNG_VOLLSTAENDIG.md`

---

**Erstellt:** $(date)  
**Version:** 1.0

