/**
 * Appointment Modal Dialog
 * 
 * Modal-Komponente für das Erstellen und Bearbeiten von Terminen
 */

export class AppointmentModal {
    constructor(onSave, onDelete) {
        this.onSave = onSave;
        this.onDelete = onDelete;
        this.currentAppointment = null;
        this.modal = null;
        
        // Cache für Dropdown-Daten
        this.appointmentTypes = [];
        this.doctors = [];
        this.patients = [];
        this.allDoctors = []; // Alle Ärzte (vor Filterung)
        this.allPatients = []; // Alle Patienten (vor Filterung)
        this.allRooms = []; // Alle Räume (vor Filterung)
        this.isLoadingData = false;
        this.isCheckingAvailability = false;
        
        this.init();
    }

    getAuthHeaders() {
        try {
            const token = localStorage.getItem('access_token');
            return token ? { 'Authorization': `Bearer ${token}` } : {};
        } catch (e) {
            return {};
        }
    }
    
    init() {
        this.createModal();
        this.setupEventHandlers();
        // Lade initiale Daten (Dropdown-Optionen)
        this.loadDropdownData();
    }
    
    createModal() {
        const modalHTML = `
            <div class="calendar-modal-backdrop" id="calendarModalBackdrop" style="display: none;">
                <div class="calendar-modal">
                    <div class="calendar-modal__header">
                        <h2 class="calendar-modal__title" id="calendarModalTitle">Neuer Termin</h2>
                        <button class="calendar-modal__close" id="calendarModalClose" type="button" aria-label="Schließen">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                    <div class="calendar-modal__body">
                        <form id="calendarModalForm">
                            <div class="calendar-form-group">
                                <label class="calendar-label" for="modalTitle">Titel *</label>
                                <select
                                    id="modalTitle"
                                    class="calendar-input"
                                    name="appointment_type_id"
                                    required
                                >
                                    <option value="">Lade Terminarten...</option>
                                </select>
                            </div>
                            
                            <div class="calendar-form-group">
                                <label class="calendar-label" for="modalDoctor">Arzt *</label>
                                <select
                                    id="modalDoctor"
                                    class="calendar-input"
                                    name="doctor_id"
                                    required
                                >
                                    <option value="">Lade Ärzte...</option>
                                </select>
                            </div>
                            
                            <div class="calendar-form-group">
                                <label class="calendar-label" for="modalPatient">Patient *</label>
                                <select
                                    id="modalPatient"
                                    class="calendar-input"
                                    name="patient_id"
                                    required
                                >
                                    <option value="">Lade Patienten...</option>
                                </select>
                            </div>
                            
                            <div class="calendar-form-row">
                                <div class="calendar-form-group">
                                    <label class="calendar-label" for="modalDate">Datum *</label>
                                    <input
                                        type="date"
                                        id="modalDate"
                                        class="calendar-input"
                                        name="date"
                                        required
                                    />
                                </div>
                                
                                <div class="calendar-form-group">
                                    <label class="calendar-label" for="modalStartTime">Startzeit *</label>
                                    <input
                                        type="time"
                                        id="modalStartTime"
                                        class="calendar-input"
                                        name="startTime"
                                        required
                                    />
                                </div>
                                
                                <div class="calendar-form-group">
                                    <label class="calendar-label" for="modalEndTime">Endzeit *</label>
                                    <input
                                        type="time"
                                        id="modalEndTime"
                                        class="calendar-input"
                                        name="endTime"
                                        required
                                    />
                                </div>
                            </div>
                            
                            <div class="calendar-form-group">
                                <label class="calendar-label" for="modalDescription">Beschreibung</label>
                                <textarea
                                    id="modalDescription"
                                    class="calendar-textarea"
                                    name="description"
                                    rows="4"
                                    placeholder="Optionale Notizen..."
                                ></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="calendar-modal__footer">
                        <button type="button" class="calendar-btn calendar-btn--secondary" id="calendarModalCancel">Abbrechen</button>
                        <button type="button" class="calendar-btn calendar-btn--danger" id="calendarModalDelete" style="display: none;">Löschen</button>
                        <button type="button" class="calendar-btn calendar-btn--primary" id="calendarModalSave">Speichern</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('calendarModalBackdrop');
    }
    
    setupEventHandlers() {
        const closeBtn = document.getElementById('calendarModalClose');
        const cancelBtn = document.getElementById('calendarModalCancel');
        const saveBtn = document.getElementById('calendarModalSave');
        const deleteBtn = document.getElementById('calendarModalDelete');
        const backdrop = this.modal;
        
        const close = () => this.close();
        
        closeBtn?.addEventListener('click', close);
        cancelBtn?.addEventListener('click', close);
        deleteBtn?.addEventListener('click', () => {
            if (this.currentAppointment && confirm('Möchten Sie diesen Termin wirklich löschen?')) {
                this.onDelete?.(this.currentAppointment.id);
                this.close();
            }
        });
        
        backdrop?.addEventListener('click', (e) => {
            if (e.target === backdrop) close();
        });
        
        saveBtn?.addEventListener('click', () => this.save());
        
        // Event-Listener für Datum/Zeit-Änderungen (Verfügbarkeitsprüfung)
        const dateField = document.getElementById('modalDate');
        const startTimeField = document.getElementById('modalStartTime');
        const endTimeField = document.getElementById('modalEndTime');
        
        const checkAvailability = () => this.checkAvailability();
        
        dateField?.addEventListener('change', checkAvailability);
        startTimeField?.addEventListener('change', checkAvailability);
        endTimeField?.addEventListener('change', checkAvailability);
    }
    
    /**
     * Öffnet das Modal für Bearbeitung oder Erstellung eines Termins
     * 
     * @param {Object|null} appointment - Das zu bearbeitende Appointment-Objekt oder null für neuen Termin
     * @param {Object|null} defaultTimes - Optionale Standard-Zeiten für neuen Termin {start: Date, end: Date}
     */
    async open(appointment = null, defaultTimes = null) {
        // Debug: Logge den Aufruf zur Fehlerdiagnose
        console.log('[AppointmentModal] open() called with:', {
            hasAppointment: !!appointment,
            appointmentId: appointment?.id,
            appointmentTitle: appointment?.title,
            defaultTimes: defaultTimes
        });
        
        // Speichere das aktuelle Appointment für Save/Delete-Operationen
        this.currentAppointment = appointment;
        
        const form = document.getElementById('calendarModalForm');
        const title = document.getElementById('calendarModalTitle');
        const deleteBtn = document.getElementById('calendarModalDelete');
        
        // Validiere, dass Modal-Elemente existieren
        if (!form || !title || !deleteBtn) {
            console.error('[AppointmentModal] Modal elements not found. Form:', !!form, 'Title:', !!title, 'DeleteBtn:', !!deleteBtn);
            alert('Fehler: Termin-Dialog-Elemente konnten nicht gefunden werden.');
            return;
        }
        
        // Stelle sicher, dass Dropdown-Daten geladen sind
        if (this.appointmentTypes.length === 0 || this.doctors.length === 0 || this.patients.length === 0) {
            console.log('[AppointmentModal] Dropdown data not loaded yet, loading now...');
            await this.loadDropdownData();
        }
        
        if (appointment) {
            // BEARBEITUNGS-MODUS: Vorhandenen Termin bearbeiten
            console.log('[AppointmentModal] Opening in EDIT mode for appointment:', appointment.id);
            title.textContent = 'Termin bearbeiten';
            deleteBtn.style.display = 'block';

            // Reset Dropdowns auf volle Listen, damit der Arzt gesetzt werden kann
            this.updateDropdownsWithAllOptions();
            
            // Fülle alle Felder mit den Appointment-Daten
            this.fillModalFields(appointment);
        } else {
            // ERSTELLUNGS-MODUS: Neuen Termin anlegen
            console.log('[AppointmentModal] Opening in CREATE mode');
            title.textContent = 'Neuer Termin';
            deleteBtn.style.display = 'none';
            
            // Leere alle Felder
            this.clearModalFields();
            
            // Setze Standard-Datum/Zeit
            if (defaultTimes && defaultTimes.start && defaultTimes.end) {
                // Verwende übergebene Standard-Zeiten (z.B. von Doppelklick auf Zeit-Slot)
                const start = new Date(defaultTimes.start);
                const end = new Date(defaultTimes.end);
                this.setDateTimeFields(start, end);
            } else {
                // Standard: Heute, 9:00 - 9:30
                const today = new Date();
                const defaultStart = new Date(today);
                defaultStart.setHours(9, 0, 0, 0);
                const defaultEnd = new Date(defaultStart);
                defaultEnd.setHours(9, 30, 0, 0);
                this.setDateTimeFields(defaultStart, defaultEnd);
            }
            
            // Prüfe Verfügbarkeit für Standard-Zeiten
            // Warte kurz, damit Dropdowns geladen sind
            setTimeout(() => {
                this.checkAvailability();
            }, 500);
        }
        
        // Zeige Modal mit Animation
        this.modal.style.display = 'flex';
        setTimeout(() => {
            this.modal.classList.add('calendar-modal-backdrop--open');
        }, 10);
    }
    
    /**
     * Füllt alle Modal-Felder mit Appointment-Daten
     * 
     * Diese Funktion wird aufgerufen, wenn ein vorhandener Termin bearbeitet wird.
     * Sie extrahiert alle Daten aus dem Appointment-Objekt und füllt die entsprechenden
     * Formularfelder im Modal.
     * 
     * @param {Object} appointment - Das Appointment-Objekt mit allen Daten
     */
    fillModalFields(appointment) {
        if (!appointment) {
            console.warn('[AppointmentModal] fillModalFields: appointment is null/undefined');
            return;
        }
        
        console.log('[AppointmentModal] fillModalFields called with:', {
            id: appointment.id,
            title: appointment.title,
            appointmentTypeId: appointment.appointmentTypeId,
            doctorName: appointment.doctorName,
            doctorId: appointment.doctorId,
            patientName: appointment.patientName,
            patientId: appointment.patientId,
            start: appointment.start,
            end: appointment.end,
            description: appointment.description
        });
        
        // Dropdown-Felder: Verwende IDs wenn verfügbar, sonst versuche Name-Matching
        if (appointment.appointmentTypeId) {
            this.setFieldValue('modalTitle', appointment.appointmentTypeId);
        } else if (appointment.title) {
            // Versuche Name-Matching für Appointment Type
            const matchingType = this.appointmentTypes.find(t => t.name === appointment.title);
            if (matchingType) {
                this.setFieldValue('modalTitle', matchingType.id);
            }
        }
        
        const doctorIdValue = appointment.doctorId ?? appointment.doctor;
        if (doctorIdValue) {
            this.setFieldValue('modalDoctor', doctorIdValue);
        } else if (appointment.doctorName) {
            // Versuche Name-Matching für Doctor
            const matchingDoctor = this.doctors.find(d => d.name === appointment.doctorName);
            if (matchingDoctor) {
                this.setFieldValue('modalDoctor', matchingDoctor.id);
            }
        }
        
        if (appointment.patientId) {
            this.setFieldValue('modalPatient', appointment.patientId);
        } else if (appointment.patientName) {
            // Versuche Name-Matching für Patient
            const matchingPatient = this.patients.find(p => {
                const displayName = `${p.first_name || ''} ${p.last_name || ''}`.trim();
                return displayName === appointment.patientName;
            });
            if (matchingPatient) {
                this.setFieldValue('modalPatient', matchingPatient.id);
            }
        }
        
        // Beschreibung
        this.setFieldValue('modalDescription', appointment.description || '');
        
        // Datum/Zeit-Felder: Konvertiere ISO-String oder Date-Objekt zu Date
        let start, end;
        
        // Parse Start-Datum
        if (appointment.start instanceof Date) {
            start = appointment.start;
        } else if (typeof appointment.start === 'string') {
            start = new Date(appointment.start);
        } else {
            console.error('[AppointmentModal] Invalid start date type:', typeof appointment.start, appointment.start);
            start = new Date();
        }
        
        // Parse End-Datum
        if (appointment.end instanceof Date) {
            end = appointment.end;
        } else if (typeof appointment.end === 'string') {
            end = new Date(appointment.end);
        } else {
            console.error('[AppointmentModal] Invalid end date type:', typeof appointment.end, appointment.end);
            end = new Date(start.getTime() + 30 * 60000); // Default: 30 Minuten später
        }
        
        // Validiere, dass die Datum-Objekte gültig sind
        if (isNaN(start.getTime())) {
            console.error('[AppointmentModal] Invalid start date after parsing:', appointment.start);
            start = new Date();
        }
        if (isNaN(end.getTime())) {
            console.error('[AppointmentModal] Invalid end date after parsing:', appointment.end);
            end = new Date(start.getTime() + 30 * 60000);
        }
        
        console.log('[AppointmentModal] Parsed dates - Start:', start, 'End:', end);
        
        // Setze Datum/Zeit-Felder
        this.setDateTimeFields(start, end);
        
        // Debug: Validiere, dass alle Felder gesetzt wurden
        setTimeout(() => {
            const titleValue = document.getElementById('modalTitle')?.value;
            const doctorValue = document.getElementById('modalDoctor')?.value;
            const patientValue = document.getElementById('modalPatient')?.value;
            console.log('[AppointmentModal] Fields after fill:', {
                title: titleValue,
                doctor: doctorValue,
                patient: patientValue
            });
        }, 100);
    }
    
    /**
     * Setzt Datum- und Zeit-Felder im Modal
     * 
     * Konvertiert Date-Objekte in die Formate, die von HTML5 input-Elementen erwartet werden:
     * - input[type=date] erwartet YYYY-MM-DD
     * - input[type=time] erwartet HH:MM
     * 
     * @param {Date} start - Start-Datum/Zeit
     * @param {Date} end - End-Datum/Zeit
     */
    setDateTimeFields(start, end) {
        if (!start || !end || isNaN(start.getTime()) || isNaN(end.getTime())) {
            console.error('[AppointmentModal] setDateTimeFields: Invalid dates', { start, end });
            return;
        }
        
        // Datum: YYYY-MM-DD Format für input[type=date]
        // WICHTIG: Verwende lokale Zeit, nicht UTC (toISOString() würde UTC verwenden)
        const year = start.getFullYear();
        const month = String(start.getMonth() + 1).padStart(2, '0');
        const day = String(start.getDate()).padStart(2, '0');
        const dateStr = `${year}-${month}-${day}`;
        this.setFieldValue('modalDate', dateStr);
        
        // Startzeit: HH:MM Format für input[type=time]
        const startHours = String(start.getHours()).padStart(2, '0');
        const startMinutes = String(start.getMinutes()).padStart(2, '0');
        const startTimeStr = `${startHours}:${startMinutes}`;
        this.setFieldValue('modalStartTime', startTimeStr);
        
        // Endzeit: HH:MM Format für input[type=time]
        const endHours = String(end.getHours()).padStart(2, '0');
        const endMinutes = String(end.getMinutes()).padStart(2, '0');
        const endTimeStr = `${endHours}:${endMinutes}`;
        this.setFieldValue('modalEndTime', endTimeStr);
        
        console.log('[AppointmentModal] setDateTimeFields:', {
            date: dateStr,
            startTime: startTimeStr,
            endTime: endTimeStr
        });
    }
    
    /**
     * Setzt den Wert eines Formularfeldes
     * 
     * @param {string} fieldId - Die ID des Feldes
     * @param {string} value - Der Wert, der gesetzt werden soll
     */
    setFieldValue(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = value || '';
        } else {
            console.warn(`[AppointmentModal] Field not found: ${fieldId}`);
        }
    }
    
    /**
     * Leert alle Modal-Felder
     */
    clearModalFields() {
        const form = document.getElementById('calendarModalForm');
        if (form) {
            form.reset();
        }
        
        // Explizit alle Felder leeren (falls reset() nicht ausreicht)
        this.setFieldValue('modalTitle', '');
        this.setFieldValue('modalDoctor', '');
        this.setFieldValue('modalPatient', '');
        this.setFieldValue('modalDescription', '');
        this.setFieldValue('modalDate', '');
        this.setFieldValue('modalStartTime', '');
        this.setFieldValue('modalEndTime', '');
    }
    
    /**
     * Lädt alle Dropdown-Daten von den API-Endpunkten
     */
    async loadDropdownData() {
        if (this.isLoadingData) {
            console.log('[AppointmentModal] Already loading dropdown data, skipping...');
            return;
        }
        
        this.isLoadingData = true;
        console.log('[AppointmentModal] Loading dropdown data...');
        
        try {
            // Lade alle Datensätze parallel
            await Promise.all([
                this.loadAppointmentTypes(),
                this.loadDoctors(),
                this.loadPatients(),
                this.loadRooms()
            ]);
            
            console.log('[AppointmentModal] Dropdown data loaded successfully');
        } catch (error) {
            console.error('[AppointmentModal] Error loading dropdown data:', error);
        } finally {
            this.isLoadingData = false;
        }
    }
    
    /**
     * Lädt Appointment Types von der API
     */
    async loadAppointmentTypes() {
        try {
            const response = await fetch('/api/appointment-types/?active=true', {
                headers: {
                    'Accept': 'application/json',
                    ...this.getAuthHeaders(),
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`Failed to load appointment types: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // DRF gibt manchmal data.results zurück (bei Pagination), manchmal direkt data
            let types = [];
            if (Array.isArray(data)) {
                types = data;
            } else if (data && Array.isArray(data.results)) {
                types = data.results;
            }
            
            this.appointmentTypes = types;
            console.log(`[AppointmentModal] Loaded ${types.length} appointment types`);
            
            // Fülle Dropdown
            const select = document.getElementById('modalTitle');
            if (select) {
                select.innerHTML = '<option value="">Bitte wählen...</option>';
                types.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type.id;
                    option.textContent = type.name;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('[AppointmentModal] Error loading appointment types:', error);
            const select = document.getElementById('modalTitle');
            if (select) {
                select.innerHTML = '<option value="">Fehler beim Laden</option>';
            }
        }
    }
    
    /**
     * Lädt Doctors von der API
     */
    async loadDoctors() {
        try {
            const response = await fetch('/api/appointments/doctors/', {
                headers: {
                    'Accept': 'application/json',
                    ...this.getAuthHeaders(),
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`Failed to load doctors: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // API gibt direkt ein Array zurück
            let doctors = [];
            if (Array.isArray(data)) {
                doctors = data;
            } else if (data && Array.isArray(data.results)) {
                doctors = data.results;
            }
            
            // Speichere alle Ärzte für spätere Filterung
            this.allDoctors = doctors;
            this.doctors = doctors; // Initial: alle Ärzte
            console.log(`[AppointmentModal] Loaded ${doctors.length} doctors`);
            
            // Fülle Dropdown (wird später durch Verfügbarkeitsprüfung gefiltert)
            this.updateDoctorDropdown(doctors);
        } catch (error) {
            console.error('[AppointmentModal] Error loading doctors:', error);
            const select = document.getElementById('modalDoctor');
            if (select) {
                select.innerHTML = '<option value="">Fehler beim Laden</option>';
            }
        }
    }
    
    /**
     * Lädt Patients von der API
     */
    async loadPatients() {
        try {
            const response = await fetch('/api/patients/search/', {
                headers: {
                    'Accept': 'application/json',
                    ...this.getAuthHeaders(),
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`Failed to load patients: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // DRF gibt manchmal data.results zurück (bei Pagination), manchmal direkt data
            let patients = [];
            if (Array.isArray(data)) {
                patients = data;
            } else if (data && Array.isArray(data.results)) {
                patients = data.results;
            }
            
            // Speichere alle Patienten für spätere Filterung
            this.allPatients = patients;
            this.patients = patients; // Initial: alle Patienten
            console.log(`[AppointmentModal] Loaded ${patients.length} patients`);
            
            // Fülle Dropdown (wird später durch Verfügbarkeitsprüfung gefiltert)
            this.updatePatientDropdown(patients);
        } catch (error) {
            console.error('[AppointmentModal] Error loading patients:', error);
            const select = document.getElementById('modalPatient');
            if (select) {
                select.innerHTML = '<option value="">Fehler beim Laden</option>';
            }
        }
    }
    
    /**
     * Lädt Räume von der API
     */
    async loadRooms() {
        try {
            const response = await fetch('/api/resources/?type=room&active=true', {
                headers: {
                    'Accept': 'application/json',
                    ...this.getAuthHeaders(),
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`Failed to load rooms: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            
            let rooms = [];
            if (Array.isArray(data)) {
                rooms = data;
            } else if (data && Array.isArray(data.results)) {
                rooms = data.results;
            }
            
            this.allRooms = rooms;
            console.log(`[AppointmentModal] Loaded ${rooms.length} rooms`);
        } catch (error) {
            console.error('[AppointmentModal] Error loading rooms:', error);
        }
    }
    
    /**
     * Aktualisiert das Patient-Dropdown
     */
    updatePatientDropdown(patients) {
        const select = document.getElementById('modalPatient');
        if (!select) return;
        
        const currentValue = select.value;
        select.innerHTML = '<option value="">Bitte wählen...</option>';
        
        patients.forEach(patient => {
            const option = document.createElement('option');
            option.value = patient.id;
            const displayName = patient.display_name || 
                               `${patient.first_name || ''} ${patient.last_name || ''}`.trim() || 
                               `Patient #${patient.id}`;
            option.textContent = displayName;
            select.appendChild(option);
        });
        
        // Stelle vorherigen Wert wieder her, falls noch verfügbar
        if (currentValue && patients.find(p => p.id == currentValue)) {
            select.value = currentValue;
        } else if (currentValue) {
            // Vorheriger Wert ist nicht mehr verfügbar - Warnung anzeigen
            console.warn(`[AppointmentModal] Previously selected patient ${currentValue} is no longer available`);
        }
    }
    
    /**
     * Erzeugt ein lokales Date-Objekt aus Datum (YYYY-MM-DD) und Zeit (HH:MM)
     * ohne UTC-Parsing-Ambiguität.
     */
    buildLocalDateTime(dateStr, timeStr) {
        if (!dateStr || !timeStr) return null;
        const [year, month, day] = dateStr.split('-').map(Number);
        const [hour, minute] = timeStr.split(':').map(Number);
        if (!year || !month || !day || Number.isNaN(hour) || Number.isNaN(minute)) {
            return null;
        }
        return new Date(year, month - 1, day, hour, minute, 0, 0);
    }

    /**
     * Prüft Verfügbarkeit basierend auf aktuellen Datum/Zeit-Werten
     */
    async checkAvailability() {
        if (this.isCheckingAvailability) {
            return; // Verhindere mehrfache gleichzeitige Aufrufe
        }
        
        const dateField = document.getElementById('modalDate');
        const startTimeField = document.getElementById('modalStartTime');
        const endTimeField = document.getElementById('modalEndTime');
        
        if (!dateField || !startTimeField || !endTimeField) {
            return;
        }
        
        const date = dateField.value;
        const startTime = startTimeField.value;
        const endTime = endTimeField.value;
        
        if (!date || !startTime || !endTime) {
            // Nicht alle Felder ausgefüllt - zeige alle Optionen
            this.updateDropdownsWithAllOptions();
            return;
        }
        
        // Erzeuge lokale Date-Objekte (keine UTC-Ambiguität)
        const startDate = this.buildLocalDateTime(date, startTime);
        const endDate = this.buildLocalDateTime(date, endTime);

        if (!startDate || !endDate) {
            console.warn('[AppointmentModal] Availability skipped: invalid date/time', {
                date,
                startTime,
                endTime,
            });
            this.updateDropdownsWithAllOptions();
            return;
        }

        // Ungültige Zeitspanne -> keine Availability-Query
        if (endDate <= startDate) {
            console.warn('[AppointmentModal] Availability skipped: end <= start', {
                date,
                startTime,
                endTime,
            });
            this.updateDropdownsWithAllOptions();
            return;
        }
        
        // API erwartet ISO-Strings; hier bewusst als lokale Wandzeit ohne UTC-Shift,
        // damit Working-Hours-Prüfung nicht um die Browser-Zeitzone verschoben wird.
        const startISOString = `${date}T${startTime}:00`;
        const endISOString = `${date}T${endTime}:00`;
        
        this.isCheckingAvailability = true;
        
        try {
            // Exclude current appointment ID if editing
            const excludeParam = this.currentAppointment?.id 
                ? `&exclude_appointment_id=${this.currentAppointment.id}` 
                : '';
            
            const url = `/api/availability/?start=${encodeURIComponent(startISOString)}&end=${encodeURIComponent(endISOString)}${excludeParam}`;
            
            console.log('[AppointmentModal] Checking availability:', url);
            
            const response = await fetch(url, {
                headers: {
                    'Accept': 'application/json',
                    ...this.getAuthHeaders(),
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`Failed to check availability: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('[AppointmentModal] Availability response:', data);
            
            // Aktualisiere Dropdowns mit verfügbaren Optionen
            this.updateDropdownsWithAvailability(data);
            
        } catch (error) {
            console.error('[AppointmentModal] Error checking availability:', error);
            // Bei Fehler: zeige alle Optionen
            this.updateDropdownsWithAllOptions();
        } finally {
            this.isCheckingAvailability = false;
        }
    }
    
    /**
     * Aktualisiert Dropdowns mit verfügbaren Optionen
     */
    updateDropdownsWithAvailability(availabilityData) {
        // Ärzte
        let availableDoctors = availabilityData.available_doctors || [];
        if (this.currentAppointment?.doctorId) {
            const hasDoctor = availableDoctors.some(d => d.id == this.currentAppointment.doctorId);
            if (!hasDoctor) {
                const fallbackDoctor = this.allDoctors.find(d => d.id == this.currentAppointment.doctorId);
                if (fallbackDoctor) {
                    availableDoctors = [...availableDoctors, fallbackDoctor];
                }
            }
        }
        this.updateDoctorDropdown(availableDoctors);
        
        // Räume (falls in Zukunft benötigt)
        const availableRooms = availabilityData.available_rooms || [];
        // TODO: Update room dropdown if we add it to the form
        
        // Patienten
        const availablePatients = availabilityData.available_patients || [];
        this.updatePatientDropdown(availablePatients);
    }
    
    /**
     * Aktualisiert Dropdowns mit allen Optionen (keine Filterung)
     */
    updateDropdownsWithAllOptions() {
        this.updateDoctorDropdown(this.allDoctors);
        this.updatePatientDropdown(this.allPatients);
    }
    
    /**
     * Aktualisiert das Arzt-Dropdown
     */
    updateDoctorDropdown(doctors) {
        const select = document.getElementById('modalDoctor');
        if (!select) return;
        
        const currentValue = select.value;
        select.innerHTML = '<option value="">Bitte wählen...</option>';
        
        doctors.forEach(doctor => {
            const option = document.createElement('option');
            option.value = doctor.id;
            option.textContent = doctor.name
                ? `${doctor.name} (ID ${doctor.id})`
                : `Arzt #${doctor.id}`;
            select.appendChild(option);
        });
        
        // Stelle vorherigen Wert wieder her, falls noch verfügbar
        if (currentValue && doctors.find(d => d.id == currentValue)) {
            select.value = currentValue;
        } else if (currentValue) {
            // Vorheriger Wert ist nicht mehr verfügbar - Warnung anzeigen
            console.warn(`[AppointmentModal] Previously selected doctor ${currentValue} is no longer available`);
            select.value = '';
            // Optional: Zeige Warnung an Benutzer
            // alert('Der ausgewählte Arzt ist zu dieser Zeit nicht verfügbar.');
        }

        // Wenn wir im Edit-Modus sind, setze den Arzt erneut, falls möglich
        if (!select.value && this.currentAppointment?.doctorId) {
            const match = doctors.find(d => d.id == this.currentAppointment.doctorId);
            if (match) {
                select.value = String(this.currentAppointment.doctorId);
            }
        }

        // Falls der aktuelle Arzt nicht in der Liste ist, füge ihn temporär hinzu
        if (!select.value && this.currentAppointment?.doctorId) {
            const existing = Array.from(select.options).some(
                opt => opt.value == this.currentAppointment.doctorId
            );
            if (!existing) {
                const option = document.createElement('option');
                option.value = String(this.currentAppointment.doctorId);
                option.textContent = this.currentAppointment.doctorName
                    || `Arzt #${this.currentAppointment.doctorId}`;
                select.appendChild(option);
            }
            select.value = String(this.currentAppointment.doctorId);
        }
    }
    
    close() {
        this.modal.classList.remove('calendar-modal-backdrop--open');
        setTimeout(() => {
            this.modal.style.display = 'none';
            this.currentAppointment = null;
        }, 200);
    }
    
    /**
     * Speichert oder aktualisiert einen Termin
     * 
     * Unterscheidet zwischen:
     * - Update: Wenn this.currentAppointment existiert (Bearbeitung)
     * - Create: Wenn this.currentAppointment null ist (Neuer Termin)
     */
    save() {
        const form = document.getElementById('calendarModalForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        const formData = new FormData(form);
        const date = formData.get('date');
        const startTime = formData.get('startTime');
        const endTime = formData.get('endTime');
        
        // Erstelle Date-Objekte aus Formular-Daten
        const start = this.buildLocalDateTime(date, startTime);
        const end = this.buildLocalDateTime(date, endTime);

        if (!start || !end) {
            alert('Ungültiges Datum oder Uhrzeit.');
            return;
        }
        
        // Validierung: Endzeit muss nach Startzeit liegen
        if (end <= start) {
            alert('Endzeit muss nach der Startzeit liegen.');
            return;
        }
        
        // Hole IDs aus den Dropdowns
        const appointmentTypeId = formData.get('appointment_type_id');
        const doctorId = formData.get('doctor_id');
        const patientId = formData.get('patient_id');
        
        // Validiere, dass alle erforderlichen IDs vorhanden sind
        if (!appointmentTypeId || !doctorId || !patientId) {
            alert('Bitte wählen Sie Titel, Arzt und Patient aus.');
            return;
        }
        
        // Hole Anzeigenamen für die Dropdowns (für Anzeige im Kalender)
        const appointmentType = this.appointmentTypes.find(t => t.id == appointmentTypeId);
        const doctor = this.doctors.find(d => d.id == doctorId);
        const patient = this.patients.find(p => p.id == patientId);
        
        // Erstelle/Update Appointment-Objekt
        const appointment = {
            // ID: Verwende vorhandene ID bei Update, generiere neue bei Create
            id: this.currentAppointment?.id || `appt-${Date.now()}`,
            
            // IDs für Backend-API
            appointmentTypeId: parseInt(appointmentTypeId),
            doctorId: parseInt(doctorId),
            patientId: parseInt(patientId),
            
            // Anzeigenamen (für Kalender-Darstellung)
            title: appointmentType?.name || '',
            doctorName: doctor?.name || '',
            patientName: patient ? `${patient.first_name || ''} ${patient.last_name || ''}`.trim() : '',
            description: formData.get('description') || '',
            
            // Datum/Zeit als ISO-String
            start: start.toISOString(),
            end: end.toISOString(),
        };
        
        // Behalte zusätzliche Eigenschaften vom ursprünglichen Appointment (z.B. doctorColor)
        if (this.currentAppointment) {
            // UPDATE: Behalte zusätzliche Eigenschaften
            if (this.currentAppointment.doctorColor) {
                appointment.doctorColor = this.currentAppointment.doctorColor;
            } else if (doctor?.calendar_color) {
                appointment.doctorColor = doctor.calendar_color;
            }
        } else if (doctor?.calendar_color) {
            // CREATE: Setze doctorColor vom Doctor-Objekt
            appointment.doctorColor = doctor.calendar_color;
        }
        
        // Rufe Callback auf (wird von Calendar-Komponente bereitgestellt)
        this.onSave?.(appointment);
        this.close();
    }
}

