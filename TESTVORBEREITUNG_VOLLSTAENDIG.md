# Vollständige Testvorbereitung - Browser-Tests

## Übersicht

Dieses Dokument dient als vollständige Anleitung für manuelle Browser-Tests aller Funktionen und Masken des PraxiApp-Systems.

---

## 1. Liste aller Masken/Seiten

### 1.1 Dashboard (Haupt-Dashboard)

**URL:** `/praxi_backend/dashboard/` oder `http://localhost:8000/praxi_backend/dashboard/`  
**Template:** `praxi_backend/dashboard/templates/dashboard/index_modern.html`  
**View:** `praxi_backend.dashboard.views.DashboardView`  
**CSS-Dateien:**
- `design-tokens-modern.css`
- `base-modern.css`
- `components-modern.css`
- `pages/haupt_dashboard.css` (falls verwendet)

**JS-Dateien:**
- Keine spezifischen JS-Dateien (Diagramme über Chart.js im Template)

**Funktionen:**
- KPI-Karten anzeigen
- Statistische Diagramme in Accordion
- Status-Badges
- Navigation zu anderen Seiten

---

### 1.2 Patientenliste

**URL:** `/praxi_backend/dashboard/patients/` oder `http://localhost:8000/praxi_backend/dashboard/patients/`  
**Template:** `praxi_backend/dashboard/templates/dashboard/patients_list.html`  
**View:** `praxi_backend.dashboard.patient_views.PatientOverviewView`  
**CSS-Dateien:**
- `design-tokens-modern.css`
- `base-modern.css`
- `components-modern.css`
- `pages/patients_list.css`

**JS-Dateien:**
- Inline-Script im Template (Such- und Filterfunktion)

**Funktionen:**
- Patienten-Tabelle anzeigen
- Suche nach Patientennamen
- Filter nach Status und Risiko
- Patienten-Detailansicht (Link)

---

### 1.3 Terminplanung (FullCalendar)

**URL:** `/praxi_backend/dashboard/appointments/` oder `http://localhost:8000/praxi_backend/dashboard/appointments/`  
**Template:** `praxi_backend/dashboard/templates/dashboard/appointments_calendar_fullcalendar.html`  
**View:** `praxi_backend.dashboard.appointment_calendar_fullcalendar_view.AppointmentCalendarFullCalendarView`  
**CSS-Dateien:**
- `design-tokens-modern.css`
- `base-modern.css`
- `components-modern.css`
- `pages/appointments_calendar_modern.css`
- FullCalendar CSS (CDN)

**JS-Dateien:**
- FullCalendar JS (CDN)
- `static/js/appointment-calendar.js`
- `static/js/appointment-dialog.js`
- Inline-Script im Template

**Funktionen:**
- Kalender-Ansicht (Tag, Woche, Monat)
- Termine anzeigen
- Termin per Drag & Drop verschieben
- Termin per Resize (Größe ändern) anpassen
- Termin anklicken (Detail-Dialog)
- Doppelklick für neuen Termin
- "Neuer Termin" Button
- Kalender aktualisieren

---

### 1.4 Termin-Dialog (Modal)

**URL:** Wird dynamisch geöffnet (keine direkte URL)  
**Template:** Wird dynamisch in `appointment-dialog.js` erstellt  
**View:** Keine (JavaScript-Modal)  
**CSS-Dateien:**
- `components-modern.css` (Modal-Styles)

**JS-Dateien:**
- `static/js/appointment-dialog.js`

**Funktionen:**
- Neuen Termin anlegen
- Termin bearbeiten
- Patient auswählen (Autocomplete)
- Arzt auswählen (Autocomplete)
- Raum auswählen (Autocomplete)
- Ressourcen auswählen (Checkboxes)
- Terminart auswählen (Dropdown)
- Datum, Zeit, Dauer eingeben
- Notizen eingeben
- Speichern
- Abbrechen

---

### 1.5 Scheduling-Dashboard

**URL:** `/praxi_backend/dashboard/scheduling/` oder `http://localhost:8000/praxi_backend/dashboard/scheduling/`  
**Template:** `praxi_backend/dashboard/templates/dashboard/scheduling.html`  
**View:** `praxi_backend.dashboard.scheduling_views.SchedulingDashboardView`  
**CSS-Dateien:**
- `design-tokens-modern.css`
- `base-modern.css`
- `components-modern.css`
- `pages/haupt_dashboard.css`

**JS-Dateien:**
- Chart.js (CDN, für Diagramme)
- Inline-Script im Template (Funnel-Visualisierung)

**Funktionen:**
- Efficiency Score anzeigen
- KPI-Karten (Completion Rate, Stornoquote, No-Show Rate, etc.)
- Buchungs-Funnel (Diagramm)
- Trend-Charts
- Kapazitätsauslastung (Ärzte, Räume)
- Peak-Load Analyse (Heatmap)

---

### 1.6 Operations-Dashboard

**URL:** `/praxi_backend/dashboard/operations/` oder `http://localhost:8000/praxi_backend/dashboard/operations/`  
**Template:** `praxi_backend/dashboard/templates/dashboard/operations.html`  
**View:** `praxi_backend.dashboard.operations_views.OperationsDashboardView`  
**CSS-Dateien:**
- `design-tokens-modern.css`
- `base-modern.css`
- `components-modern.css`
- `pages/haupt_dashboard.css`

**JS-Dateien:**
- Chart.js (CDN, für Diagramme)
- Inline-Scripts im Template

**Funktionen:**
- KPI-Karten (Operationen, Abgeschlossen, In Bearbeitung, etc.)
- Patient Flow Pipeline (Diagramm)
- Stündliche Verteilung (Chart)
- Flow Times
- Bottleneck-Analyse
- Dokumentationsstatus

---

### 1.7 Doctors-Dashboard

**URL:** `/praxi_backend/dashboard/doctors/` oder `http://localhost:8000/praxi_backend/dashboard/doctors/`  
**Template:** `praxi_backend/dashboard/templates/dashboard/doctors.html`  
**View:** `praxi_backend.dashboard.doctor_views.DoctorDashboardView`  
**CSS-Dateien:**
- `design-tokens-modern.css`
- `base-modern.css`
- `components-modern.css`
- `pages/haupt_dashboard.css`

**JS-Dateien:**
- Chart.js (CDN, für Diagramme)
- Inline-Scripts im Template

**Funktionen:**
- Aggregierte Statistiken (KPI-Karten)
- Arzt-Profile
- Terminvolumen (Chart)
- Auslastung (Chart)
- Stundenplan-Übersicht

---

### 1.8 Ressourcen & Räume

**URL:** `/praxi_backend/dashboard/resources/` oder `http://localhost:8000/praxi_backend/dashboard/resources/`  
**Template:** `praxi_backend/dashboard/templates/dashboard/resources.html`  
**View:** `praxi_backend.dashboard.resources_views.ResourcesDashboardView`  
**CSS-Dateien:**
- `design-tokens-modern.css`
- `base-modern.css`
- `components-modern.css`
- `pages/resources.css`

**JS-Dateien:**
- Keine spezifischen JS-Dateien

**Funktionen:**
- Räume anzeigen (Karten-Layout)
- Geräte anzeigen (Karten-Layout)
- Status-Anzeige (Aktiv/Inaktiv)
- Farbcodierung

---

### 1.9 Admin-Panel (Django Admin)

**URL:** `/admin/` oder `http://localhost:8000/admin/`  
**Template:** Django Admin Templates  
**View:** Django Admin Views  
**CSS-Dateien:**
- Django Admin CSS

**JS-Dateien:**
- Django Admin JS

**Funktionen:**
- Datenbank-Verwaltung
- Benutzer-Verwaltung
- Model-Verwaltung

---

### 1.10 API-Endpunkte (für Testing)

**Basis-URL:** `/api/` oder `http://localhost:8000/api/`

**Wichtige Endpunkte:**
- `/api/appointments/` - Termine (GET, POST)
- `/api/appointments/<id>/` - Termin-Details (GET, PATCH, DELETE)
- `/api/appointments/calendar/week/` - Kalender-Wochenansicht (GET)
- `/api/appointments/doctors/` - Ärzte-Liste (GET)
- `/api/resources/` - Ressourcen (GET, POST)
- `/api/appointment-types/` - Terminarten (GET)

---

## 2. Test-URLs (Vollständige Liste)

### 2.1 Dashboard-URLs

```
http://localhost:8000/dashboard/
http://localhost:8000/dashboard/api/
```

### 2.2 Patienten-URLs

```
http://localhost:8000/praxi_backend/dashboard/patients/              → PatientDashboardView (Übersicht)
http://localhost:8000/praxi_backend/dashboard/patients/overview/     → PatientOverviewView (Liste)
http://localhost:8000/praxi_backend/dashboard/patients/<patient_id>/ → PatientDashboardView (Detail)
http://localhost:8000/praxi_backend/dashboard/patients/api/          → PatientAPIView
http://localhost:8000/praxi_backend/dashboard/patients/api/<patient_id>/ → PatientAPIView (Detail)
```

### 2.3 Terminplanung-URLs

```
http://localhost:8000/praxi_backend/dashboard/appointments/
http://localhost:8000/praxi_backend/dashboard/appointments/fullcalendar/
http://localhost:8000/praxi_backend/dashboard/appointments/legacy/day/
http://localhost:8000/praxi_backend/dashboard/appointments/legacy/week/
http://localhost:8000/praxi_backend/dashboard/appointments/legacy/month/
```

### 2.4 Scheduling-URLs

```
http://localhost:8000/praxi_backend/dashboard/scheduling/
http://localhost:8000/praxi_backend/dashboard/scheduling/api/
```

### 2.5 Operations-URLs

```
http://localhost:8000/praxi_backend/dashboard/operations/
http://localhost:8000/praxi_backend/dashboard/operations/api/
```

### 2.6 Doctors-URLs

```
http://localhost:8000/praxi_backend/dashboard/doctors/
http://localhost:8000/praxi_backend/dashboard/doctors/<doctor_id>/
http://localhost:8000/praxi_backend/dashboard/doctors/api/
http://localhost:8000/praxi_backend/dashboard/doctors/api/<doctor_id>/
```

### 2.7 Ressourcen-URLs

```
http://localhost:8000/praxi_backend/dashboard/resources/
```

### 2.8 Admin-URLs

```
http://localhost:8000/admin/
```

---

## 3. Testdaten-Vorbereitung

### 3.1 Django Management Command erstellen

Ich erstelle einen Management Command, um Testdaten zu generieren.

### 3.2 Management Command: create_test_data

**Empfohlen:** Verwenden Sie das Management Command `create_test_data`:

```bash
python manage.py create_test_data
```

Dies erstellt automatisch:
- **5 Ärzte:** Dr. Anna Müller, Dr. Thomas Schmidt, Dr. Sarah Weber, Dr. Michael Fischer, Dr. Lisa Wagner
- **5 Terminarten:** Konsultation, Nachsorge, Operation, Vorsorge, Beratung
- **9 Ressourcen:** 4 Räume, 3 Geräte, 2 Personal
- **~70 Termine:** Für die nächsten 2 Wochen (Mo-Fr), verschiedene Status

**Testdaten-Details:**

**Ärzte:**
- Username: `dr_mueller`, `dr_schmidt`, `dr_weber`, `dr_fischer`, `dr_wagner`
- Passwort: `test123` (für alle)
- Jeder Arzt hat eine `calendar_color`

**Terminarten:**
- Konsultation (30 min, #4A90E2)
- Nachsorge (20 min, #7ED6C1)
- Operation (60 min, #EB5757)
- Vorsorge (45 min, #6FCF97)
- Beratung (25 min, #F2C94C)

**Ressourcen:**
- Räume: Behandlungsraum 1, Behandlungsraum 2, OP-Saal 1, Sprechzimmer
- Geräte: Röntgengerät, Ultraschall, EKG-Gerät
- Personal: MFA Müller, MFA Schmidt

**Termine:**
- Verteilung über 2 Wochen (Mo-Fr)
- 5-8 Termine pro Tag
- Zeiten: 8:00 - 17:00 Uhr
- Verschiedene Status: scheduled, confirmed, completed, cancelled
- Zufällige Zuordnung von Ärzten, Terminarten, Ressourcen

### 3.3 Manuelle Testdaten (über Django Admin)

**Alternative:** Falls Sie manuell Daten erstellen möchten:

**Voraussetzung:** Superuser-Login im Django Admin (`http://localhost:8000/admin/`)

**Benötigte Testdaten:**

1. **Benutzer/Rollen:**
   - Admin-User (Superuser)
   - Arzt-User (mit Rolle "doctor")
   - MFA-User (mit Rolle "assistant")

2. **Ärzte:**
   - Mindestens 3-5 Ärzte mit verschiedenen Namen
   - Jeder Arzt sollte einen `calendar_color` haben

3. **Terminarten:**
   - Verschiedene Terminarten (z.B. "Konsultation", "Operation", "Nachsorge")
   - Jede mit einer `color`

4. **Ressourcen:**
   - Mindestens 3-5 Räume (type='room')
   - Mindestens 3-5 Geräte (type='device')
   - Mindestens 2-3 Personal (type='staff')
   - Jede Ressource sollte einen `color` haben

5. **Patienten:**
   - Patienten kommen aus der `medical` Datenbank
   - Sollten bereits vorhanden sein (Legacy-DB)
   - Falls keine Patienten vorhanden: Verwenden Sie Dummy-IDs (1-10) im Management Command

6. **Termine:**
   - Mindestens 10-20 Termine für verschiedene Tage
   - Verschiedene Ärzte, Räume, Ressourcen
   - Verschiedene Status (scheduled, confirmed, completed, cancelled)

---

## 4. Funktionstests - Detaillierte Anleitung

### 4.1 Dashboard testen

**URL:** `http://localhost:8000/praxi_backend/dashboard/`

**Zu testen:**
1. ✅ KPI-Karten werden angezeigt
2. ✅ KPI-Karten haben gleiche Höhe
3. ✅ Accordion-Diagramme können geöffnet/geschlossen werden
4. ✅ Diagramme werden korrekt gerendert (Chart.js)
5. ✅ Navigation funktioniert (Header-Links)
6. ✅ Keine IDs sichtbar (nur sprechende Namen)

**Schritte:**
1. Seite öffnen
2. Prüfen, ob KPI-Karten angezeigt werden
3. Auf Accordion-Header klicken, um Diagramme zu öffnen
4. Prüfen, ob Diagramme korrekt angezeigt werden
5. Navigation-Links testen

---

### 4.2 Patientenliste testen

**URL:** `http://localhost:8000/praxi_backend/dashboard/patients/overview/`

**Zu testen:**
1. ✅ Patienten-Tabelle wird angezeigt
2. ✅ Suchfeld funktioniert
3. ✅ Filter (Status, Risiko) funktioniert
4. ✅ Hover-Effekte auf Tabellenzeilen
5. ✅ Keine IDs sichtbar (nur Patientennamen)
6. ✅ Patienten-Detail-Link funktioniert

**Schritte:**
1. Seite öffnen
2. In Suchfeld tippen (z.B. "Müller")
3. Status-Filter auswählen
4. Risiko-Filter auswählen
5. Über Tabellenzeilen hovern
6. Auf "Details anzeigen" Button klicken

---

### 4.3 Terminplanung (FullCalendar) testen

**URL:** `http://localhost:8000/praxi_backend/dashboard/appointments/`

**Zu testen:**
1. ✅ Kalender wird geladen
2. ✅ Termine werden angezeigt
3. ✅ Ansicht wechseln (Tag, Woche, Monat)
4. ✅ Drag & Drop: Termin verschieben
5. ✅ Resize: Termin-Größe ändern
6. ✅ Klick: Termin-Detail-Dialog öffnet
7. ✅ Doppelklick: Neuer Termin-Dialog öffnet
8. ✅ "Neuer Termin" Button funktioniert
9. ✅ Farbcodierung (nach Arzt oder Raum)
10. ✅ Keine IDs sichtbar (nur Patientennamen)

**Schritte:**

**Ansicht wechseln:**
1. Seite öffnen
2. Auf Ansicht-Buttons klicken (Tag, Woche, Monat)

**Termin verschieben (Drag & Drop):**
1. Termin mit Maus anklicken und halten
2. Zu neuem Zeitpunkt ziehen
3. Loslassen
4. Prüfen, ob Termin gespeichert wurde (Seite neu laden)

**Termin-Größe ändern (Resize):**
1. Auf unteren Rand eines Termins hovern (Cursor ändert sich)
2. Nach unten ziehen (Dauer verlängern) oder nach oben (Dauer verkürzen)
3. Loslassen
4. Prüfen, ob Termin gespeichert wurde

**Termin bearbeiten:**
1. Auf Termin klicken (einfacher Klick)
2. Dialog sollte sich öffnen
3. Daten ändern
4. "Speichern" klicken

**Neuer Termin:**
1. Auf "Neuer Termin" Button klicken ODER
2. Doppelklick auf leeren Kalenderbereich
3. Dialog sollte sich öffnen
4. Daten eingeben
5. "Speichern" klicken

---

### 4.4 Termin-Dialog testen

**Zu testen:**
1. ✅ Dialog öffnet sich korrekt
2. ✅ Patient-Autocomplete funktioniert
3. ✅ Arzt-Autocomplete funktioniert
4. ✅ Raum-Autocomplete funktioniert
5. ✅ Terminart-Dropdown funktioniert
6. ✅ Ressourcen-Checkboxes funktionieren
7. ✅ Datum/Zeit/Dauer-Eingabe funktioniert
8. ✅ Validierung funktioniert (Pflichtfelder)
9. ✅ Speichern funktioniert
10. ✅ Abbrechen funktioniert
11. ✅ Keine IDs sichtbar (nur sprechende Namen)

**Schritte:**

**Autocomplete testen:**
1. Dialog öffnen (Button oder Doppelklick)
2. In Patient-Feld tippen (z.B. "Müller")
3. Dropdown sollte sich öffnen
4. Patient auswählen
5. Wiederholen für Arzt und Raum

**Termin anlegen:**
1. Dialog öffnen
2. Alle Felder ausfüllen:
   - Patient (aus Autocomplete)
   - Arzt (aus Autocomplete)
   - Raum (aus Autocomplete)
   - Terminart (aus Dropdown)
   - Ressourcen (Checkboxes)
   - Datum (Date-Picker)
   - Startzeit (Time-Picker)
   - Dauer (Nummer)
   - Notizen (Textarea)
3. "Speichern" klicken
4. Prüfen, ob Termin im Kalender erscheint

**Validierung testen:**
1. Dialog öffnen
2. Nur einige Felder ausfüllen (nicht alle Pflichtfelder)
3. "Speichern" klicken
4. Validierungsfehler sollten angezeigt werden

---

### 4.5 Scheduling-Dashboard testen

**URL:** `http://localhost:8000/praxi_backend/dashboard/scheduling/`

**Zu testen:**
1. ✅ KPI-Karten werden angezeigt
2. ✅ Efficiency Score wird angezeigt
3. ✅ Buchungs-Funnel wird angezeigt
4. ✅ Trend-Charts werden angezeigt
5. ✅ Kapazitätsauslastung (Ärzte, Räume) wird angezeigt
6. ✅ Peak-Load Heatmap wird angezeigt
7. ✅ Accordion-Diagramme können geöffnet/geschlossen werden

**Schritte:**
1. Seite öffnen
2. Prüfen, ob alle KPI-Karten angezeigt werden
3. Auf Accordion-Header klicken, um Diagramme zu öffnen
4. Prüfen, ob Diagramme korrekt gerendert werden

---

### 4.6 Operations-Dashboard testen

**URL:** `http://localhost:8000/praxi_backend/dashboard/operations/`

**Zu testen:**
1. ✅ KPI-Karten werden angezeigt
2. ✅ Patient Flow Pipeline wird angezeigt
3. ✅ Stündliche Verteilung wird angezeigt
4. ✅ Flow Times werden angezeigt
5. ✅ Bottleneck-Analyse wird angezeigt
6. ✅ Dokumentationsstatus wird angezeigt

**Schritte:**
1. Seite öffnen
2. Prüfen, ob alle KPI-Karten angezeigt werden
3. Auf Accordion-Header klicken, um Diagramme zu öffnen
4. Prüfen, ob Diagramme korrekt gerendert werden

---

### 4.7 Doctors-Dashboard testen

**URL:** `http://localhost:8000/praxi_backend/dashboard/doctors/`

**Zu testen:**
1. ✅ Aggregierte Statistiken (KPI-Karten) werden angezeigt
2. ✅ Arzt-Profile werden angezeigt
3. ✅ Terminvolumen-Chart wird angezeigt
4. ✅ Auslastung-Chart wird angezeigt
5. ✅ Stundenplan-Übersicht wird angezeigt

**Schritte:**
1. Seite öffnen
2. Prüfen, ob alle KPI-Karten angezeigt werden
3. Auf Accordion-Header klicken, um Diagramme zu öffnen
4. Prüfen, ob Diagramme korrekt gerendert werden

---

### 4.8 Ressourcen & Räume testen

**URL:** `http://localhost:8000/praxi_backend/dashboard/resources/`

**Zu testen:**
1. ✅ Räume-Karten werden angezeigt
2. ✅ Geräte-Karten werden angezeigt
3. ✅ Status-Badges werden angezeigt (Aktiv/Inaktiv)
4. ✅ Farbcodierung wird angezeigt
5. ✅ Hover-Effekte funktionieren

**Schritte:**
1. Seite öffnen
2. Prüfen, ob Räume-Karten angezeigt werden
3. Prüfen, ob Geräte-Karten angezeigt werden
4. Über Karten hovern (Hover-Effekt)
5. Prüfen, ob Status-Badges korrekt angezeigt werden

---

## 5. Technische Tests

### 5.1 Templates prüfen

**Zu prüfen:**
- ✅ Alle Templates sind vorhanden
- ✅ Alle Templates erweitern `base_dashboard.html`
- ✅ Alle Templates laden CSS-Dateien korrekt
- ✅ Alle Templates laden JS-Dateien korrekt

**Prüfung:**
1. Browser-Entwicklertools öffnen (F12)
2. Tab "Network" öffnen
3. Seite neu laden
4. Prüfen, ob alle CSS-Dateien geladen werden (Status 200)
5. Prüfen, ob alle JS-Dateien geladen werden (Status 200)

---

### 5.2 CSS-Dateien prüfen

**Zu prüfen:**
- ✅ `design-tokens-modern.css` wird geladen
- ✅ `base-modern.css` wird geladen
- ✅ `components-modern.css` wird geladen
- ✅ Page-spezifische CSS-Dateien werden geladen

**Prüfung:**
1. Browser-Entwicklertools öffnen (F12)
2. Tab "Network" → Filter "CSS"
3. Seite neu laden
4. Prüfen, ob alle CSS-Dateien Status 200 haben

---

### 5.3 JS-Dateien prüfen

**Zu prüfen:**
- ✅ `appointment-calendar.js` wird geladen
- ✅ `appointment-dialog.js` wird geladen
- ✅ FullCalendar JS wird geladen (CDN)
- ✅ Chart.js wird geladen (CDN, falls verwendet)

**Prüfung:**
1. Browser-Entwicklertools öffnen (F12)
2. Tab "Network" → Filter "JS"
3. Seite neu laden
4. Prüfen, ob alle JS-Dateien Status 200 haben
5. Tab "Console" prüfen (keine Fehler)

---

### 5.4 API-Endpoints prüfen

**Zu prüfen:**
- ✅ API-Endpoints sind erreichbar
- ✅ API-Endpoints liefern JSON
- ✅ API-Endpoints haben keine CORS-Fehler

**Prüfung:**
1. Browser-Entwicklertools öffnen (F12)
2. Tab "Network" → Filter "XHR" oder "Fetch"
3. Seite neu laden oder Aktion ausführen (z.B. Termin laden)
4. Prüfen, ob API-Calls Status 200 haben
5. Response prüfen (JSON-Format)

**Wichtige API-Endpoints:**
- `/api/appointments/calendar/week/` - Kalender-Daten
- `/api/appointments/doctors/` - Ärzte-Liste
- `/api/resources/` - Ressourcen-Liste
- `/api/appointments/` - Termine (GET, POST)

---

### 5.5 IDs im UI prüfen

**Zu prüfen:**
- ✅ Keine IDs sind im UI sichtbar
- ✅ Nur sprechende Namen werden angezeigt
- ✅ IDs werden nur intern verwendet

**Prüfung:**
1. Seite öffnen
2. HTML-Quelltext prüfen (Rechtsklick → "Untersuchen")
3. Prüfen, ob IDs in sichtbarem Text vorkommen
4. Prüfen, ob nur sprechende Namen (Patientennamen, Arzennamen, etc.) angezeigt werden

---

## 6. Mögliche Fehler und Lösungen

### 6.1 Kalender lädt keine Termine

**Symptom:** Kalender ist leer, keine Termine sichtbar

**Ursachen:**
- Keine Testdaten vorhanden
- API-Endpunkt nicht erreichbar
- Fehler in Browser-Konsole

**Lösung:**
1. Browser-Konsole prüfen (F12 → Console)
2. API-Endpunkt prüfen: `/api/appointments/calendar/week/?date=2024-01-01`
3. Testdaten erstellen (über Django Admin oder Management Command)

---

### 6.2 Autocomplete funktioniert nicht

**Symptom:** Dropdown öffnet sich nicht beim Tippen

**Ursachen:**
- API-Endpunkt nicht erreichbar
- JavaScript-Fehler
- CORS-Problem

**Lösung:**
1. Browser-Konsole prüfen (F12 → Console)
2. Network-Tab prüfen (API-Calls)
3. API-Endpunkt manuell testen: `/api/appointments/doctors/`

---

### 6.3 Drag & Drop funktioniert nicht

**Symptom:** Termin kann nicht verschoben werden

**Ursachen:**
- FullCalendar JS nicht geladen
- JavaScript-Fehler
- API-Endpunkt für Update nicht erreichbar

**Lösung:**
1. Browser-Konsole prüfen (F12 → Console)
2. Prüfen, ob FullCalendar JS geladen wurde
3. Network-Tab prüfen (API-Calls beim Drag & Drop)

---

### 6.4 CSS-Dateien werden nicht geladen

**Symptom:** Styles fehlen, Seite sieht nicht modernisiert aus

**Ursachen:**
- CSS-Dateien nicht gefunden (404)
- Cache-Problem
- Pfad falsch

**Lösung:**
1. Browser-Entwicklertools öffnen (F12 → Network → CSS)
2. Prüfen, ob CSS-Dateien Status 404 haben
3. Cache leeren (Strg+F5)
4. Pfade in Templates prüfen

---

### 6.5 Keine Testdaten vorhanden

**Symptom:** Seiten sind leer, keine Daten sichtbar

**Lösung:**
1. Django Admin öffnen: `http://localhost:8000/admin/`
2. Testdaten manuell erstellen:
   - Ärzte
   - Terminarten
   - Ressourcen
   - Termine
3. ODER Management Command ausführen (falls vorhanden)

---

## 7. Checkliste für vollständige Tests

### 7.1 Vorbereitung

- [ ] Django Server läuft (`python manage.py runserver`)
- [ ] Superuser-Login erstellt
- [ ] Browser-Entwicklertools geöffnet (F12)
- [ ] Testdaten erstellt (Ärzte, Terminarten, Ressourcen, Termine)

### 7.2 Dashboard

- [ ] Dashboard lädt korrekt
- [ ] KPI-Karten werden angezeigt
- [ ] Accordion-Diagramme funktionieren
- [ ] Navigation funktioniert
- [ ] Keine IDs sichtbar

### 7.3 Patientenliste

- [ ] Patientenliste lädt korrekt
- [ ] Suchfeld funktioniert
- [ ] Filter funktionieren
- [ ] Hover-Effekte funktionieren
- [ ] Keine IDs sichtbar

### 7.4 Terminplanung

- [ ] Kalender lädt korrekt
- [ ] Termine werden angezeigt
- [ ] Ansicht wechseln funktioniert
- [ ] Drag & Drop funktioniert
- [ ] Resize funktioniert
- [ ] Klick öffnet Dialog
- [ ] Doppelklick öffnet Dialog
- [ ] Keine IDs sichtbar

### 7.5 Termin-Dialog

- [ ] Dialog öffnet sich
- [ ] Autocomplete funktioniert (Patient, Arzt, Raum)
- [ ] Dropdowns funktionieren
- [ ] Checkboxes funktionieren
- [ ] Validierung funktioniert
- [ ] Speichern funktioniert
- [ ] Keine IDs sichtbar

### 7.6 Scheduling-Dashboard

- [ ] Dashboard lädt korrekt
- [ ] KPI-Karten werden angezeigt
- [ ] Diagramme werden angezeigt
- [ ] Accordion funktioniert

### 7.7 Operations-Dashboard

- [ ] Dashboard lädt korrekt
- [ ] KPI-Karten werden angezeigt
- [ ] Diagramme werden angezeigt
- [ ] Accordion funktioniert

### 7.8 Doctors-Dashboard

- [ ] Dashboard lädt korrekt
- [ ] KPI-Karten werden angezeigt
- [ ] Diagramme werden angezeigt
- [ ] Accordion funktioniert

### 7.9 Ressourcen & Räume

- [ ] Seite lädt korrekt
- [ ] Räume-Karten werden angezeigt
- [ ] Geräte-Karten werden angezeigt
- [ ] Hover-Effekte funktionieren

### 7.10 Technische Tests

- [ ] Alle CSS-Dateien werden geladen
- [ ] Alle JS-Dateien werden geladen
- [ ] Keine JavaScript-Fehler in Konsole
- [ ] API-Endpoints sind erreichbar
- [ ] Keine IDs im UI sichtbar

---

## 8. Test-Startbefehl

Um den Server zu starten:

```bash
python manage.py runserver
```

Dann Browser öffnen:
```
http://localhost:8000/praxi_backend/dashboard/
```

---

## 9. Hinweise

- **Authentifizierung:** Stellen Sie sicher, dass Sie als Superuser oder mit entsprechender Rolle eingeloggt sind
- **Testdaten:** Erstellen Sie ausreichend Testdaten, um alle Funktionen testen zu können
- **Browser-Konsole:** Prüfen Sie regelmäßig die Browser-Konsole auf Fehler
- **Network-Tab:** Nutzen Sie den Network-Tab, um API-Calls und Ressourcen-Ladung zu prüfen
- **Cache:** Bei Problemen Cache leeren (Strg+F5)

---

**Erstellt:** $(date)  
**Version:** 1.0
