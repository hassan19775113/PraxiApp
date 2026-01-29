/**
 * PraxiApp Appointment Calendar - FullCalendar Integration
 * 
 * Outlook-ähnlicher Kalender mit Drag & Drop
 */

class AppointmentCalendar {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.calendar = null;
        this.options = {
            apiBaseUrl: options.apiBaseUrl || '/api/calendar/week/',
            initialView: options.initialView || 'timeGridWeek',
            locale: options.locale || 'de',
            ...options
        };
        
        this.patientNamesCache = {};
        this.doctorNamesCache = {};
        this.resourceNamesCache = {};
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error('Calendar container not found:', this.containerId);
            return;
        }
        
        // FullCalendar wird über CDN geladen, hier prüfen wir ob es verfügbar ist
        // FullCalendar 6.x wird als globales Objekt geladen (index.global.min.js)
        // Prüfe verschiedene mögliche Variablennamen
        var fc = null;
        if (typeof FullCalendar !== 'undefined') {
            fc = FullCalendar;
        } else if (typeof window.FullCalendar !== 'undefined') {
            fc = window.FullCalendar;
        } else if (typeof fc !== 'undefined') {
            fc = fc;
        } else if (typeof window.fc !== 'undefined') {
            fc = window.fc;
        }
        
        if (!fc) {
            console.error('FullCalendar is not loaded. Please include FullCalendar scripts.');
            console.error('Available global variables:', Object.keys(window).filter(k => k.toLowerCase().includes('calendar')));
            return;
        }
        
        // Verwende FullCalendar-Referenz
        this.FullCalendar = fc;
        
        this.setupCalendar();
        this.setupEventHandlers();
    }
    
    setupCalendar() {
        const calendarEl = this.container;
        
        console.log('[AppointmentCalendar] Initializing FullCalendar...');
        
        this.calendar = new this.FullCalendar.Calendar(calendarEl, {
            initialView: this.options.initialView,
            locale: this.options.locale,
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            height: 'auto',
            allDaySlot: false,
            slotMinTime: '06:00:00',
            slotMaxTime: '20:00:00',
            slotDuration: '00:15:00',
            slotLabelInterval: '01:00:00',
            weekends: true,
            editable: true,           // Termine können verschoben werden
            droppable: true,           // Drag & Drop aktiviert
            selectable: true,          // Zeitbereich auswählbar
            selectMirror: true,        // Vorschau beim Ziehen
            dayMaxEvents: true,        // "Mehr"-Link bei vielen Terminen
            eventStartEditable: true,  // Startzeit editierbar
            eventDurationEditable: true, // Dauer editierbar (Resize)
            eventDisplay: 'block',     // Block-Darstellung
            events: (info, successCallback, failureCallback) => {
                this.fetchEvents(info.start, info.end, successCallback, failureCallback);
            },
            eventClick: (info) => {
                console.log('[AppointmentCalendar] Event clicked:', info.event);
                this.handleEventClick(info);
            },
            eventDrop: (info) => {
                console.log('[AppointmentCalendar] Event dropped:', info.event);
                this.handleEventDrop(info);
            },
            eventResize: (info) => {
                console.log('[AppointmentCalendar] Event resized:', info.event);
                this.handleEventResize(info);
            },
            select: (info) => {
                console.log('[AppointmentCalendar] Time selected:', info);
                this.handleSelect(info);
            },
            eventDidMount: (info) => {
                this.customizeEvent(info);
            }
        });
        
        this.calendar.render();
        console.log('[AppointmentCalendar] Calendar rendered successfully');
    }
    
    async fetchEvents(start, end, successCallback, failureCallback) {
        try {
            // FullCalendar erwartet ISO-Strings für start/end
            // API erwartet date-Parameter im Format YYYY-MM-DD
            const startStr = start.toISOString().split('T')[0];
            
            // API-Endpunkt: /api/appointments/calendar/week/?date=YYYY-MM-DD
            const url = `${this.options.apiBaseUrl}?date=${startStr}`;
            
            console.log('[AppointmentCalendar] Fetching events from:', url);
            
            const response = await fetch(url, {
                headers: {
                    'Accept': 'application/json',
                    'Authorization': this.getAuthHeader()
                }
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('[AppointmentCalendar] API Error:', response.status, errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const data = await response.json();
            console.log('[AppointmentCalendar] Received data:', data);
            
            // API gibt {appointments: [...], operations: [...], ...} zurück
            const events = this.transformEvents(data.appointments || []);
            
            console.log('[AppointmentCalendar] Transformed events:', events.length);
            
            // Cache Patientennamen
            if (data.appointments) {
                this.cachePatientNames(data.appointments);
            }
            
            successCallback(events);
        } catch (error) {
            console.error('[AppointmentCalendar] Error fetching events:', error);
            // Zeige leere Liste bei Fehler, damit Kalender nicht blockiert
            successCallback([]);
        }
    }
    
    transformEvents(appointments) {
        if (!appointments || !Array.isArray(appointments)) {
            console.warn('[AppointmentCalendar] No appointments array found');
            return [];
        }
        
        return appointments.map(appt => {
            // Verwende patient_name aus API (bereits formatiert)
            const patientName = appt.patient_name || this.patientNamesCache[appt.patient_id] || `Patient #${appt.patient_id}`;
            const doctorName = appt.doctor_name || appt.doctor?.name || (typeof appt.doctor === 'object' && appt.doctor ? `${appt.doctor.first_name || ''} ${appt.doctor.last_name || ''}`.trim() : 'Unbekannt');
            const typeName = appt.type?.name || (typeof appt.type === 'object' && appt.type ? appt.type.name : 'Termin');
            
            // Farbe: Typ > Arzt > Standard
            let color = '#4A90E2'; // Soft Azure (Standard)
            if (appt.type?.color) {
                color = appt.type.color;
            } else if (appt.doctor?.calendar_color) {
                color = appt.doctor.calendar_color;
            } else if (appt.appointment_color) {
                color = appt.appointment_color;
            }
            
            // Titel: Patient + Arzt (optional)
            const title = `${patientName}${doctorName !== 'Unbekannt' ? ` - ${doctorName}` : ''}`;
            
            return {
                id: String(appt.id),
                title: title,
                start: appt.start_time,
                end: appt.end_time,
                backgroundColor: color,
                borderColor: color,
                textColor: '#FFFFFF',
                editable: true,
                startEditable: true,
                durationEditable: true,
                extendedProps: {
                    patient_id: appt.patient_id,
                    patient_name: patientName,
                    doctor_id: appt.doctor?.id || (typeof appt.doctor === 'number' ? appt.doctor : null),
                    doctor_name: doctorName,
                    type_id: appt.type?.id || (typeof appt.type === 'object' && appt.type ? appt.type.id : null),
                    type_name: typeName,
                    status: appt.status,
                    notes: appt.notes || '',
                    resources: appt.resources || [],
                    room_name: appt.room_name || null,
                    resource_names: appt.resource_names || []
                }
            };
        });
    }
    
    cachePatientNames(appointments) {
        const patientIds = [...new Set(appointments.map(a => a.patient_id))];
        const missingIds = patientIds.filter(id => !this.patientNamesCache[id]);
        
        if (missingIds.length > 0) {
            // Namen werden vom Backend mitgeliefert (siehe erweiterte Views)
            // Hier nur als Cache speichern
            appointments.forEach(appt => {
                if (appt.patient_name) {
                    this.patientNamesCache[appt.patient_id] = appt.patient_name;
                }
            });
        }
    }
    
    customizeEvent(info) {
        // Custom Event Styling
        const eventEl = info.el;
        const event = info.event;
        const props = event.extendedProps;
        
        // Tooltip mit Details
        eventEl.setAttribute('title', `${props.patient_name}\n${props.doctor_name}\n${props.type_name}`);
        
        // Event-Content anpassen (optional)
        const titleEl = eventEl.querySelector('.fc-event-title');
        if (titleEl) {
            titleEl.textContent = props.patient_name;
        }
    }
    
    handleEventClick(info) {
        // Öffne Termin-Dialog zum Bearbeiten
        const event = info.event;
        const props = event.extendedProps;
        
        if (window.openAppointmentDialog) {
            window.openAppointmentDialog({
                id: event.id,
                patient_id: props.patient_id,
                patient_name: props.patient_name,
                doctor_id: props.doctor_id,
                doctor_name: props.doctor_name,
                type_id: props.type_id,
                type_name: props.type_name,
                start_time: event.start.toISOString(),
                end_time: event.end.toISOString(),
                status: props.status,
                notes: props.notes,
                resources: props.resources
            });
        }
    }
    
    handleEventDrop(info) {
        // Termin verschieben (Drag & Drop)
        const event = info.event;
        const newStart = event.start;
        
        // Alte Start- und Endzeit aus dem Event (vor dem Drop)
        // FullCalendar speichert die ursprüngliche Position in info.oldEvent
        const oldEvent = info.oldEvent || event;
        const oldStart = oldEvent.start;
        const oldEnd = oldEvent.end;
        
        // Berechne neue Endzeit basierend auf alter Dauer
        const duration = oldEnd && oldStart ? (oldEnd.getTime() - oldStart.getTime()) : 30 * 60000; // Default 30 Min
        const newEnd = new Date(newStart.getTime() + duration);
        
        console.log('[AppointmentCalendar] Moving appointment:', {
            id: event.id,
            from: oldStart.toISOString(),
            to: newStart.toISOString()
        });
        
        this.updateAppointment(event.id, {
            start_time: newStart.toISOString(),
            end_time: newEnd.toISOString()
        }).then(() => {
            console.log('[AppointmentCalendar] Appointment moved successfully');
            // Erfolg - Event bleibt an neuer Position
            // Zeige kurze Erfolgsmeldung (optional)
            this.showNotification('Termin erfolgreich verschoben', 'success');
        }).catch((error) => {
            console.error('[AppointmentCalendar] Error moving appointment:', error);
            // Fehler - Event zurückverschieben
            info.revert();
            this.showNotification('Termin konnte nicht verschoben werden. Bitte prüfen Sie die Zeiten.', 'error');
        });
    }
    
    handleEventResize(info) {
        // Termin-Größe ändern (Dauer ändern durch Resize)
        const event = info.event;
        const newStart = event.start;
        const newEnd = event.end;
        
        console.log('[AppointmentCalendar] Resizing appointment:', {
            id: event.id,
            start: newStart.toISOString(),
            end: newEnd.toISOString()
        });
        
        this.updateAppointment(event.id, {
            start_time: newStart.toISOString(),
            end_time: newEnd.toISOString()
        }).then(() => {
            console.log('[AppointmentCalendar] Appointment resized successfully');
            this.showNotification('Termindauer erfolgreich geändert', 'success');
        }).catch((error) => {
            console.error('[AppointmentCalendar] Error resizing appointment:', error);
            info.revert();
            this.showNotification('Termin konnte nicht geändert werden.', 'error');
        });
    }
    
    handleSelect(selectionInfo) {
        // Neue Termin erstellen (wird durch Doppelklick oder Zeitbereich-Auswahl ausgelöst)
        const start = selectionInfo.start;
        const end = selectionInfo.end || new Date(start.getTime() + 30 * 60000); // Default 30 Min
        
        console.log('[AppointmentCalendar] Selection:', { start, end });
        
        if (window.openAppointmentDialog) {
            window.openAppointmentDialog({
                start_time: start.toISOString(),
                end_time: end.toISOString()
            });
        } else {
            console.warn('[AppointmentCalendar] openAppointmentDialog not available');
        }
        
        this.calendar.unselect();
    }
    
    async updateAppointment(appointmentId, data) {
        const url = `/api/appointments/${appointmentId}/`;
        const response = await fetch(url, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': this.getAuthHeader()
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Update failed');
        }
        
        return response.json();
    }
    
    getAuthHeader() {
        // JWT Token aus localStorage oder Cookie
        const token = localStorage.getItem('access_token');
        return token ? `Bearer ${token}` : '';
    }
    
    setupEventHandlers() {
        // Refresh-Button
        const refreshBtn = document.querySelector('[data-calendar-refresh]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.calendar.refetchEvents();
            });
        }
    }
    
    refresh() {
        if (this.calendar) {
            this.calendar.refetchEvents();
        }
    }
    
    gotoDate(date) {
        if (this.calendar) {
            this.calendar.gotoDate(date);
        }
    }
    
    changeView(viewName) {
        if (this.calendar) {
            this.calendar.changeView(viewName);
        }
    }
    
    showNotification(message, type = 'info') {
        // Einfache Benachrichtigung (kann später durch Toast-Komponente ersetzt werden)
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#6FCF97' : type === 'error' ? '#EB5757' : '#4A90E2'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            font-size: 14px;
            font-weight: 500;
            animation: slideIn 0.3s ease-out;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Global export
window.AppointmentCalendar = AppointmentCalendar;

