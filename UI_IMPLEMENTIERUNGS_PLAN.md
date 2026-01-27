# PraxiApp UI - Vollständige Implementierungsplan

## Status-Analyse

### ✅ Bereits vorhanden:
1. Design-Tokens (`design-tokens-modern.css`) - Vollständig
2. Base-Modern CSS (`base-modern.css`) - Vollständig
3. Components-Modern CSS (`components-modern.css`) - Grundkomponenten vorhanden
4. Dashboard Template (`index_modern.html`) - Modernisiert
5. Appointment Calendar Template (`appointments_calendar_fullcalendar.html`) - Modernisiert
6. Appointment Calendar JS (`appointment-calendar.js`) - Vollständig
7. Appointment Dialog JS (`appointment-dialog.js`) - Vollständig
8. Backend API-Endpoints - Alle vorhanden (AppointmentSerializer mit Namen-Feldern)

### ⚠️ Muss modernisiert/ergänzt werden:
1. **Dashboard View** - Verwendet `index.html`, sollte `index_modern.html` verwenden
2. **Patientenliste Template** (`patients.html`) - Muss modernisiert werden
3. **Scheduling Template** (`scheduling.html`) - Muss modernisiert werden
4. **Operations Template** (`operations.html`) - Muss modernisiert werden
5. **Doctors Template** (`doctors.html`) - Muss modernisiert werden
6. **Ressourcen-View/Template** - Fehlt komplett
7. **Accordion-Komponente** - Muss in components-modern.css ergänzt werden
8. **FullCalendar-Styles** - Muss in `appointments_calendar_modern.css` ergänzt werden
9. **Patientenliste-Tabelle** - Moderne Tabelle mit Suchfeld
10. **Ressourcen-Kartenlayout** - Muss erstellt werden

## Implementierungsreihenfolge

1. **Komponenten vervollständigen** (CSS)
   - Accordion-Komponente hinzufügen
   - Tabellen-Styles modernisieren
   - FullCalendar-Styles vervollständigen

2. **Templates modernisieren**
   - Dashboard View auf index_modern.html umstellen
   - Patientenliste modernisieren
   - Scheduling modernisieren
   - Operations modernisieren
   - Doctors modernisieren

3. **Neue Views/Templates erstellen**
   - Ressourcen-View erstellen
   - Ressourcen-Template erstellen

4. **JavaScript ergänzen**
   - Patientenliste-Suche
   - Ressourcen-Interaktionen

5. **Konsistenz-Prüfung**
   - Alle Templates auf Designsystem prüfen
   - Keine IDs im UI
   - Alle APIs verbunden

