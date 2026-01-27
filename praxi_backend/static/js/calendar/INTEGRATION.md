# Integration der Modern Calendar Component

## Schnellstart

### Option 1: Neue Kalender-Komponente verwenden (empfohlen)

1. **CSS einbinden** in `base_dashboard.html` oder im Template:

```html
{% block page_css %}
<link rel="stylesheet" href="{% static 'js/calendar/calendar.css' %}">
<link rel="stylesheet" href="{% static 'js/calendar/modal.css' %}">
{% endblock %}
```

2. **JavaScript einbinden** im Template:

```html
{% block extra_scripts %}
<script type="module" src="{% static 'js/calendar/index.js' %}"></script>
{% endblock %}
```

3. **Container ist bereits vorhanden** in `appointments_calendar_fullcalendar.html`:

```html
<div id="appointmentCalendar"></div>
```

### Option 2: Als Alternative zu FullCalendar

Falls Sie die neue Komponente als Ersatz für FullCalendar verwenden möchten:

1. Entfernen Sie die FullCalendar-Scripts aus `base_dashboard.html`
2. Fügen Sie die neuen CSS/JS-Dateien hinzu
3. Die Komponente initialisiert sich automatisch

## API-Integration

### Schritt 1: `calendar.js` anpassen

In der Methode `loadAppointments()`:

```javascript
async loadAppointments() {
    try {
        const response = await fetch(this.options.apiUrl);
        if (!response.ok) throw new Error('API request failed');
        
        const data = await response.json();
        this.appointments = this.transformAppointments(data);
        this.renderAppointments();
    } catch (error) {
        console.error('Error loading appointments:', error);
        // Fallback auf Mock-Daten
        const { generateMockAppointments } = await import('./mockData.js');
        this.appointments = generateMockAppointments();
        this.renderAppointments();
    }
}
```

### Schritt 2: Transform-Funktion hinzufügen

```javascript
transformAppointments(data) {
    // Wenn API ein Array zurückgibt
    if (Array.isArray(data)) {
        return data.map(item => this.transformAppointment(item));
    }
    
    // Wenn API ein Objekt mit 'results' zurückgibt
    if (data.results && Array.isArray(data.results)) {
        return data.results.map(item => this.transformAppointment(item));
    }
    
    return [];
}

transformAppointment(item) {
    return {
        id: item.id.toString(),
        start: item.start_time || item.start,
        end: item.end_time || item.end,
        doctorName: item.doctor_name || item.doctor?.name || 'Unbekannt',
        patientName: item.patient_name || item.patient?.name || 'Unbekannt',
        title: item.type?.name || item.title || 'Termin',
        description: item.notes || item.description || '',
        doctorColor: item.doctor_color || item.doctor?.calendar_color || this.getDoctorColor(item.doctor_name),
    };
}
```

### Schritt 3: Save-Funktion anpassen

In der Methode `handleSave()`:

```javascript
async handleSave(appointment) {
    try {
        const isUpdate = appointment.id && this.appointments.find(a => a.id === appointment.id);
        const url = isUpdate 
            ? `${this.options.apiUrl}${appointment.id}/`
            : this.options.apiUrl;
        const method = isUpdate ? 'PATCH' : 'POST';
        
        // Transform für API
        const payload = {
            patient_id: parseInt(appointment.patientId) || 1, // TODO: Aus Formular
            doctor: parseInt(appointment.doctorId) || 1, // TODO: Aus Formular
            start_time: appointment.start,
            end_time: appointment.end,
            notes: appointment.description,
            // ... weitere Felder
        };
        
        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken(),
            },
            credentials: 'same-origin',
            body: JSON.stringify(payload),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Speichern fehlgeschlagen');
        }
        
        const saved = await response.json();
        
        // Update lokale Liste
        if (isUpdate) {
            const index = this.appointments.findIndex(a => a.id === appointment.id);
            this.appointments[index] = this.transformAppointment(saved);
        } else {
            this.appointments.push(this.transformAppointment(saved));
        }
        
        this.renderAppointments();
    } catch (error) {
        console.error('Error saving appointment:', error);
        alert('Fehler beim Speichern: ' + error.message);
    }
}

getCsrfToken() {
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

## Anpassungen

### Farben ändern

Die Komponente nutzt CSS-Variablen. Sie können diese überschreiben:

```css
.modern-calendar {
    --color-primary-azure: #IhreFarbe;
    --color-surface: #IhreFarbe;
}
```

### View-Standard ändern

```javascript
const calendar = new ModernCalendar('appointmentCalendar', {
    initialView: 'month', // 'day', 'week', 'month'
});
```

### Drag & Drop hinzufügen

Für Drag & Drop können Sie eine Bibliothek wie `interact.js` integrieren:

```javascript
import interact from 'interactjs';

// In renderAppointments() nach createAppointmentElement():
interact(element).draggable({
    onmove: (event) => {
        // Drag-Logik
    },
});
```

## Troubleshooting

### Kalender wird nicht angezeigt

1. Prüfen Sie die Browser-Konsole auf Fehler
2. Stellen Sie sicher, dass `#appointmentCalendar` existiert
3. Prüfen Sie, ob CSS/JS-Dateien geladen werden (Network-Tab)

### Module-Fehler

Stellen Sie sicher, dass der Browser ES6-Module unterstützt und `type="module"` gesetzt ist.

### API-Fehler

1. Prüfen Sie die API-URL
2. Prüfen Sie CORS-Einstellungen
3. Prüfen Sie CSRF-Token


