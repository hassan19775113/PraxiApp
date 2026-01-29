# Modern Calendar Component

Eine moderne, Outlook-inspirierte Kalender-Komponente für PraxiApp.

## Features

- ✅ **Monats-, Wochen- und Tagesansicht**
- ✅ **Doppelklick zum Erstellen/Bearbeiten**
- ✅ **Fluent UI / Outlook Design**
- ✅ **Responsive Layout**
- ✅ **Integration mit bestehendem Design-System**
- ✅ **ES6-Module**

## Dateien

- `index.js` - Entry Point
- `calendar.js` - Hauptkomponente
- `calendar.css` - Kalender-Styles
- `modal.js` - Modal-Dialog
- `modal.css` - Modal-Styles
- `mockData.js` - Mock-Daten

## Integration

### 1. CSS einbinden

In `base_dashboard.html` oder im Template:

```html
<link rel="stylesheet" href="{% static 'js/calendar/calendar.css' %}">
<link rel="stylesheet" href="{% static 'js/calendar/modal.css' %}">
```

### 2. JavaScript einbinden

Im Template (z.B. `appointments_calendar_fullcalendar.html`):

```html
<script type="module" src="{% static 'js/calendar/index.js' %}"></script>
```

### 3. Container bereitstellen

```html
<div id="appointmentCalendar"></div>
```

## API-Integration

Aktuell verwendet die Komponente Mock-Daten. Für echte API-Integration:

1. In `calendar.js` die Methode `loadAppointments()` anpassen:

```javascript
async loadAppointments() {
    try {
        const response = await fetch(this.options.apiUrl);
        const data = await response.json();
        this.appointments = this.transformAppointments(data);
        this.renderAppointments();
    } catch (error) {
        console.error('Error loading appointments:', error);
    }
}
```

2. Transform-Funktion hinzufügen:

```javascript
transformAppointments(data) {
    return data.map(item => ({
        id: item.id.toString(),
        start: item.start_time,
        end: item.end_time,
        doctorName: item.doctor_name,
        patientName: item.patient_name,
        title: item.type?.name || 'Termin',
        description: item.notes || '',
        doctorColor: item.doctor_color || this.getDoctorColor(item.doctor_name),
    }));
}
```

## Anpassungen

Die Komponente nutzt CSS-Variablen aus dem Design-System:
- `--color-primary-azure`
- `--color-surface`
- `--spacing-*`
- `--radius-*`
- `--shadow-*`

Alle Styles können über CSS-Variablen angepasst werden.


