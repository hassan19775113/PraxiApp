# PraxiApp UI Modernisierung - Zusammenfassung

## Überblick

Das UI-Design wurde komplett modernisiert mit einem hellen, ruhigen, freundlichen Designsystem speziell für medizinisches Personal.

## Neue Dateien

### Designsystem
1. **`praxi_backend/static/css/design-tokens-modern.css`**
   - Design-Tokens mit neuen Farben (Soft Azure, Calm Mint, Soft Green, Soft Amber, Soft Coral)
   - Typografie (Inter), Spacing, Shadows, etc.

2. **`praxi_backend/static/css/components-modern.css`**
   - Komponenten: Buttons, Cards, Forms, Tables, Badges, Accordion, Modal, Tooltips, KPI Cards

3. **`praxi_backend/static/css/base-modern.css`**
   - Basis-Styles: Body, Header, Layout, Sections, Grids

### JavaScript
4. **`praxi_backend/static/js/appointment-calendar.js`**
   - FullCalendar Integration
   - Drag & Drop für Termine
   - Event-Handling (Click, Drop, Resize, Select)

5. **`praxi_backend/static/js/appointment-dialog.js`**
   - Modal-Dialog für Termine
   - Autocomplete für Patient/Arzt/Raum/Ressource
   - Keine IDs sichtbar - nur sprechende Namen

### Backend Utils
6. **`praxi_backend/dashboard/utils.py`**
   - `get_patient_display_name()` - Holt Patientennamen (Name + Geburtsdatum)
   - `get_patient_names_batch()` - Batch-Lookup für mehrere Patienten

## Nächste Schritte (zu implementieren)

### 1. Base Template aktualisieren
**Datei:** `praxi_backend/dashboard/templates/dashboard/base_dashboard.html`

Änderungen:
- Neue CSS-Dateien einbinden (design-tokens-modern.css, base-modern.css, components-modern.css)
- FullCalendar CDN einbinden
- JavaScript-Dateien einbinden (appointment-calendar.js, appointment-dialog.js)

```html
<!-- In <head> -->
<link rel="stylesheet" href="{% static 'css/design-tokens-modern.css' %}">
<link rel="stylesheet" href="{% static 'css/base-modern.css' %}">
<link rel="stylesheet" href="{% static 'css/components-modern.css' %}">

<!-- FullCalendar CSS & JS -->
<link href='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/main.min.css' rel='stylesheet' />
<script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/main.min.js'></script>
<script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/locales/de.js'></script>

<!-- In <body> vor schließendem Tag -->
<script src="{% static 'js/appointment-calendar.js' %}"></script>
<script src="{% static 'js/appointment-dialog.js' %}"></script>
```

### 2. Backend Views erweitern
**Datei:** `praxi_backend/dashboard/appointment_calendar_views.py`

Erweitern Sie `_event_payload()` um Patientennamen:

```python
from praxi_backend.dashboard.utils import get_patient_display_name, get_patient_names_batch

def _event_payload(*, appt: Appointment, tz, start_min: int, cfg: _CalendarConfig) -> dict:
    # ... existierender Code ...
    
    # Patientennamen hinzufügen
    patient_name = get_patient_display_name(appt.patient_id)
    
    return {
        # ... existierende Felder ...
        "patient_name": patient_name,  # NEU
        # ...
    }
```

**Datei:** `praxi_backend/appointments/views.py` oder Serializer

Erweitern Sie `AppointmentSerializer` um `patient_name`:

```python
class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    # ... andere Felder ...
    
    def get_patient_name(self, obj):
        from praxi_backend.dashboard.utils import get_patient_display_name
        return get_patient_display_name(obj.patient_id)
```

### 3. Kalender-Template erstellen
**Datei:** `praxi_backend/dashboard/templates/dashboard/appointments_calendar_modern.html`

Neues Template mit FullCalendar:

```html
{% extends "dashboard/base_dashboard.html" %}
{% load static %}

{% block title %}Terminplanung{% endblock %}
{% block nav_active_scheduling %}prx-header__link--active{% endblock %}

{% block page_css %}
<link rel="stylesheet" href="{% static 'css/pages/appointments_calendar_modern.css' %}">
{% endblock %}

{% block content %}
<section class="prx-section">
    <div class="prx-section__header">
        <div>
            <h1 class="prx-section__title">
                <span class="fluent-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M7 10h5v5H7v-5zm0 7h5v2H7v-2zM3 5h2V3h2v2h8V3h2v2h2a1 1 0 0 1 1 1v3H2V6a1 1 0 0 1 1-1z"/>
                    </svg>
                </span>
                Terminplanung
            </h1>
        </div>
        <button class="prx-btn prx-btn--primary" onclick="window.openAppointmentDialog()">
            <span class="fluent-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                </svg>
            </span>
            Neuer Termin
        </button>
    </div>
    
    <div class="prx-card">
        <div class="prx-card__body" style="padding: 0;">
            <div id="appointmentCalendar"></div>
        </div>
    </div>
</section>

<script>
document.addEventListener('DOMContentLoaded', function() {
    window.appointmentCalendar = new AppointmentCalendar('appointmentCalendar', {
        apiBaseUrl: '/api/appointments/calendar/',
        initialView: 'timeGridWeek',
        locale: 'de'
    });
    
    window.appointmentDialogInstance = new AppointmentDialog();
});
</script>
{% endblock %}
```

### 4. CSS für Kalender
**Datei:** `praxi_backend/static/css/pages/appointments_calendar_modern.css`

```css
/* FullCalendar Anpassungen */
#appointmentCalendar {
    padding: var(--spacing-5);
}

.fc {
    font-family: var(--font-family);
}

.fc-header-toolbar {
    margin-bottom: var(--spacing-4);
}

.fc-button {
    background: var(--color-surface) !important;
    border-color: var(--color-border) !important;
    color: var(--color-text) !important;
    border-radius: var(--radius-md) !important;
    padding: var(--spacing-2) var(--spacing-3) !important;
    font-weight: var(--font-weight-medium) !important;
}

.fc-button:hover {
    background: var(--color-bg) !important;
}

.fc-button-primary:not(:disabled).fc-button-active {
    background: var(--color-primary-azure) !important;
    border-color: var(--color-primary-azure) !important;
}

.fc-event {
    border-radius: var(--radius-sm) !important;
    border: none !important;
    padding: 2px 4px !important;
}

.fc-event:hover {
    opacity: 0.9;
}
```

### 5. Views erweitern für API
**Datei:** Neue View oder erweitern Sie bestehende Calendar-Views

Für die FullCalendar-API benötigen Sie einen Endpoint, der Events im FullCalendar-Format liefert.

### 6. Accordion für Diagramme
Die Accordion-Komponente ist bereits in `components-modern.css` definiert. Verwenden Sie sie in Dashboard-Templates:

```html
<div class="prx-accordion">
    <div class="prx-accordion__item">
        <div class="prx-accordion__header" onclick="this.parentElement.classList.toggle('prx-accordion__item--open')">
            <h3 class="prx-accordion__title">Statistiken</h3>
            <svg class="prx-accordion__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
        </div>
        <div class="prx-accordion__content">
            <div class="prx-accordion__body">
                <!-- Diagramm hier -->
            </div>
        </div>
    </div>
</div>
```

## Designsystem-Farben

### Primärfarben
- **Soft Azure:** #4A90E2 (Hauptfarbe)
- **Calm Mint:** #7ED6C1
- **Soft Green:** #6FCF97
- **Soft Amber:** #F2C94C
- **Soft Coral:** #EB5757

### Neutrale Farben
- **Hintergrund:** #F7F9FB
- **Karten:** #FFFFFF
- **Linien:** #E5E9F0
- **Text dunkel:** #2D3A45
- **Text hell:** #7A8A99

## Wichtige Features

1. **Keine IDs sichtbar** - Alle IDs werden in Hidden-Feldern gespeichert, nur sprechende Namen werden angezeigt
2. **Drag & Drop** - Termine können per Drag & Drop verschoben werden
3. **Autocomplete** - Patient/Arzt/Raum-Suche mit Autocomplete
4. **Modernes Design** - Helles, ruhiges, medizinisches Design
5. **Responsive** - Mobile-freundlich

## Integration

1. Neue CSS-Dateien in Base-Template einbinden
2. JavaScript-Dateien einbinden
3. Backend Views erweitern (Patientennamen)
4. Neue Kalender-Templates erstellen
5. API-Endpoints anpassen (falls nötig)

## Hinweise

- FullCalendar erfordert eine spezielle Event-Format (siehe `appointment-calendar.js`)
- Patientennamen werden über Utility-Funktionen geholt (siehe `dashboard/utils.py`)
- Das Designsystem ist vollständig in CSS-Variablen definiert (einfach anpassbar)
- Alle Komponenten sind modular und wiederverwendbar

