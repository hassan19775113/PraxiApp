/**
 * PraxiApp Appointment Dialog
 * 
 * Modal-Dialog zum Erstellen/Bearbeiten von Terminen
 * Keine IDs sichtbar - nur sprechende Namen
 */

class AppointmentDialog {
    constructor(options = {}) {
        this.options = {
            apiBaseUrl: options.apiBaseUrl || '/api/',
            ...options
        };
        this.modal = null;
        this.currentData = null;
        this.autocompleteInstances = {};
        
        this.init();
    }
    
    init() {
        this.createModal();
        this.setupEventHandlers();
    }
    
    createModal() {
        const modalHTML = `
            <div class="prx-modal-backdrop" id="appointmentDialogBackdrop" style="display: none; visibility: hidden;">
                <div class="prx-modal">
                    <div class="prx-modal__header">
                        <h2 class="prx-modal__title" id="appointmentDialogTitle">Neuer Termin</h2>
                        <button class="prx-modal__close" id="appointmentDialogClose" type="button" aria-label="Schließen">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                    <div class="prx-modal__body">
                        <form id="appointmentDialogForm">
                            <!-- Patient -->
                            <div class="prx-input-group prx-mb-4">
                                <label class="prx-label" for="appointmentPatient">Patient *</label>
                                <div class="prx-autocomplete">
                                    <input
                                        type="text"
                                        id="appointmentPatient"
                                        class="prx-input"
                                        placeholder="Patient suchen (Name, Geburtsdatum)..."
                                        autocomplete="off"
                                        required
                                    />
                                    <input type="hidden" id="appointmentPatientId" name="patient_id" />
                                    <div class="prx-autocomplete__dropdown" id="appointmentPatientDropdown" style="display: none;"></div>
                                </div>
                            </div>
                            
                            <!-- Arzt -->
                            <div class="prx-input-group prx-mb-4">
                                <label class="prx-label" for="appointmentDoctor">Arzt / Ärztin *</label>
                                <div class="prx-autocomplete">
                                    <input
                                        type="text"
                                        id="appointmentDoctor"
                                        class="prx-input"
                                        placeholder="Arzt suchen (Name, Fachrichtung)..."
                                        autocomplete="off"
                                        required
                                    />
                                    <input type="hidden" id="appointmentDoctorId" name="doctor" />
                                    <div class="prx-autocomplete__dropdown" id="appointmentDoctorDropdown" style="display: none;"></div>
                                </div>
                            </div>
                            
                            <!-- Raum -->
                            <div class="prx-input-group prx-mb-4">
                                <label class="prx-label" for="appointmentRoom">Raum</label>
                                <div class="prx-autocomplete">
                                    <input
                                        type="text"
                                        id="appointmentRoom"
                                        class="prx-input"
                                        placeholder="Raum suchen..."
                                        autocomplete="off"
                                    />
                                    <input type="hidden" id="appointmentRoomId" name="resources" />
                                    <div class="prx-autocomplete__dropdown" id="appointmentRoomDropdown" style="display: none;"></div>
                                </div>
                            </div>
                            
                            <!-- Terminart -->
                            <div class="prx-input-group prx-mb-4">
                                <label class="prx-label" for="appointmentType">Terminart *</label>
                                <select id="appointmentType" class="prx-select" name="type" required>
                                    <option value="">Bitte wählen...</option>
                                </select>
                            </div>
                            
                            <!-- Datum -->
                            <div class="prx-input-group prx-mb-4">
                                <label class="prx-label" for="appointmentDate">Datum *</label>
                                <input
                                    type="date"
                                    id="appointmentDate"
                                    class="prx-input"
                                    name="date"
                                    required
                                />
                            </div>
                            
                            <!-- Zeit Start -->
                            <div class="prx-input-group prx-mb-4">
                                <label class="prx-label" for="appointmentStartTime">Startzeit *</label>
                                <input
                                    type="time"
                                    id="appointmentStartTime"
                                    class="prx-input"
                                    name="start_time"
                                    required
                                />
                            </div>
                            
                            <!-- Dauer -->
                            <div class="prx-input-group prx-mb-4">
                                <label class="prx-label" for="appointmentDuration">Dauer (Minuten) *</label>
                                <input
                                    type="number"
                                    id="appointmentDuration"
                                    class="prx-input"
                                    name="duration"
                                    min="5"
                                    step="5"
                                    value="30"
                                    required
                                />
                            </div>
                            
                            <!-- Ressourcen (Multi-Select) -->
                            <div class="prx-input-group prx-mb-4">
                                <label class="prx-label">Ressourcen (Geräte, Personal, Material)</label>
                                <div id="appointmentResources" class="prx-resources-select">
                                    <!-- Wird dynamisch gefüllt -->
                                </div>
                            </div>
                            
                            <!-- Notizen -->
                            <div class="prx-input-group prx-mb-4">
                                <label class="prx-label" for="appointmentNotes">Notizen</label>
                                <textarea
                                    id="appointmentNotes"
                                    class="prx-textarea"
                                    name="notes"
                                    rows="4"
                                    placeholder="Optionale Notizen..."
                                ></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="prx-modal__footer">
                        <button type="button" class="prx-btn prx-btn--secondary" id="appointmentDialogCancel">Abbrechen</button>
                        <button type="button" class="prx-btn prx-btn--primary" id="appointmentDialogSave">Speichern</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('appointmentDialogBackdrop');
        
        this.setupAutocompletes();
        this.loadInitialData();
    }
    
    setupAutocompletes() {
        // Patient Autocomplete
        this.setupAutocomplete('appointmentPatient', 'appointmentPatientId', 'appointmentPatientDropdown', 
            '/api/medical/patients/search/', (item) => {
                const birthStr = item.birth_date ? new Date(item.birth_date).toLocaleDateString('de-DE') : '';
                return `${item.last_name}, ${item.first_name}${birthStr ? ` (${birthStr})` : ''}`;
            }, (item) => item.id);
        
        // Arzt Autocomplete
        this.setupAutocomplete('appointmentDoctor', 'appointmentDoctorId', 'appointmentDoctorDropdown',
            '/api/appointments/doctors/', (item) => {
                return item.name || `${item.first_name || ''} ${item.last_name || ''}`.trim();
            }, (item) => item.id);
        
        // Raum Autocomplete
        this.setupAutocomplete('appointmentRoom', 'appointmentRoomId', 'appointmentRoomDropdown',
            '/api/resources/?type=room', (item) => item.name, (item) => item.id);
    }
    
    setupAutocomplete(inputId, hiddenId, dropdownId, apiUrl, formatItem, getValue) {
        const input = document.getElementById(inputId);
        const hidden = document.getElementById(hiddenId);
        const dropdown = document.getElementById(dropdownId);
        
        // Prüfe ob alle Elemente existieren
        if (!input || !hidden || !dropdown) {
            console.error(`[AppointmentDialog] Autocomplete setup failed: Missing elements for ${inputId}`);
            return;
        }
        
        let timeout = null;
        let allItems = []; // Cache für alle Items
        
        // Funktion zum Laden und Anzeigen der Items
        const loadAndShowItems = async (query = '') => {
            try {
                console.log(`[AppointmentDialog] Loading items for ${inputId}, query: "${query}"`);
                
                // URL zusammenstellen: Wenn query leer ist, alle Items laden
                let url = apiUrl;
                if (query.trim().length > 0) {
                    url = `${apiUrl}${apiUrl.includes('?') ? '&' : '?'}q=${encodeURIComponent(query)}`;
                } else {
                    // Alle Items laden (ohne Filter)
                    url = apiUrl;
                }
                
                console.log(`[AppointmentDialog] Fetching from: ${url}`);
                
                const response = await fetch(url, {
                    headers: {
                        'Accept': 'application/json',
                        'Authorization': this.getAuthHeader()
                    }
                });
                
                console.log(`[AppointmentDialog] Response status: ${response.status} ${response.statusText}`);
                
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error(`[AppointmentDialog] API error (${response.status}):`, errorText);
                    dropdown.innerHTML = `<div class="prx-autocomplete__item">Fehler beim Laden (${response.status})</div>`;
                    dropdown.style.display = 'block';
                    return;
                }
                
                const data = await response.json();
                console.log(`[AppointmentDialog] Raw response data for ${inputId}:`, data);
                
                // DRF gibt manchmal data.results zurück (bei Pagination), manchmal direkt data
                let items = null;
                if (Array.isArray(data)) {
                    items = data;
                } else if (data && Array.isArray(data.results)) {
                    items = data.results;
                } else if (data && typeof data === 'object') {
                    // Versuche, ein Array aus dem Objekt zu extrahieren
                    items = [];
                    console.warn(`[AppointmentDialog] Response is not an array for ${inputId}, trying to extract items`);
                } else {
                    items = [];
                }
                
                // Sicherstellen, dass items ein Array ist
                if (!Array.isArray(items)) {
                    console.error(`[AppointmentDialog] Could not parse response as array for ${inputId}:`, data);
                    items = [];
                }
                
                console.log(`[AppointmentDialog] Parsed ${items.length} items for ${inputId}`);
                
                console.log(`[AppointmentDialog] Received ${items.length} items for ${inputId}`);
                
                // Cache speichern (nur wenn keine Suche)
                if (query.trim().length === 0) {
                    allItems = items;
                }
                
                dropdown.innerHTML = '';
                
                if (items.length === 0) {
                    dropdown.innerHTML = '<div class="prx-autocomplete__item">Keine Ergebnisse</div>';
                } else {
                    items.forEach(item => {
                        const itemEl = document.createElement('div');
                        itemEl.className = 'prx-autocomplete__item';
                        itemEl.textContent = formatItem(item);
                        itemEl.addEventListener('click', () => {
                            input.value = formatItem(item);
                            hidden.value = getValue(item);
                            dropdown.style.display = 'none';
                            console.log(`[AppointmentDialog] Selected item for ${inputId}:`, formatItem(item));
                        });
                        dropdown.appendChild(itemEl);
                    });
                }
                
                dropdown.style.display = 'block';
                console.log(`[AppointmentDialog] Dropdown displayed for ${inputId}`);
            } catch (error) {
                console.error(`[AppointmentDialog] Autocomplete error for ${inputId}:`, error);
                dropdown.innerHTML = `<div class="prx-autocomplete__item">Fehler: ${error.message}</div>`;
                dropdown.style.display = 'block';
            }
        };
        
        // Beim Fokus: Alle Items anzeigen
        input.addEventListener('focus', () => {
            console.log(`[AppointmentDialog] Focus event on ${inputId}`);
            clearTimeout(timeout);
            const query = input.value.trim();
            
            // Wenn bereits Text eingegeben wurde, filtere
            if (query.length > 0) {
                timeout = setTimeout(() => loadAndShowItems(query), 300);
            } else {
                // Wenn leer, zeige alle Items
                loadAndShowItems('');
            }
        });
        
        // Beim Eingeben: Filter anwenden
        input.addEventListener('input', () => {
            clearTimeout(timeout);
            const query = input.value.trim();
            
            if (query.length === 0) {
                // Wenn leer, zeige alle Items
                loadAndShowItems('');
                return;
            }
            
            // Filter mit Verzögerung
            timeout = setTimeout(() => loadAndShowItems(query), 300);
        });
        
        // Click outside to close
        document.addEventListener('click', (e) => {
            if (!input.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });
    }
    
    async loadInitialData() {
        // Terminarten laden
        try {
            console.log('[AppointmentDialog] Loading appointment types...');
            const response = await fetch('/api/appointment-types/?active=true', {
                headers: {
                    'Accept': 'application/json',
                    'Authorization': this.getAuthHeader()
                }
            });
            
            console.log(`[AppointmentDialog] Appointment types response status: ${response.status} ${response.statusText}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`[AppointmentDialog] API error loading appointment types (${response.status}):`, errorText);
                return;
            }
            
            const data = await response.json();
            console.log('[AppointmentDialog] Raw appointment types data:', data);
            
            // DRF gibt manchmal data.results zurück (bei Pagination), manchmal direkt data
            let types = null;
            if (Array.isArray(data)) {
                types = data;
            } else if (data && Array.isArray(data.results)) {
                types = data.results;
            } else {
                types = [];
            }
            
            console.log(`[AppointmentDialog] Parsed ${types.length} appointment types`);
            
            const select = document.getElementById('appointmentType');
            if (!select) {
                console.error('[AppointmentDialog] appointmentType select element not found!');
                return;
            }
            
            select.innerHTML = '<option value="">Bitte wählen...</option>';
            
            if (types.length === 0) {
                console.warn('[AppointmentDialog] No appointment types found!');
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'Keine Terminarten verfügbar';
                option.disabled = true;
                select.appendChild(option);
            } else {
                types.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type.id;
                    option.textContent = type.name;
                    select.appendChild(option);
                });
                console.log(`[AppointmentDialog] Added ${types.length} appointment types to select`);
            }
        } catch (error) {
            console.error('[AppointmentDialog] Error loading appointment types:', error);
        }
        
        // Ressourcen laden
        try {
            const response = await fetch('/api/resources/?active=true', {
                headers: {
                    'Accept': 'application/json',
                    'Authorization': this.getAuthHeader()
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                const container = document.getElementById('appointmentResources');
                container.innerHTML = '';
                
                (data.results || data).forEach(resource => {
                    if (resource.type === 'device' || resource.type === 'staff' || resource.type === 'material') {
                        const checkbox = document.createElement('label');
                        checkbox.className = 'prx-checkbox';
                        checkbox.innerHTML = `
                            <input type="checkbox" name="resources" value="${resource.id}">
                            <span>${resource.name}</span>
                        `;
                        container.appendChild(checkbox);
                    }
                });
            }
        } catch (error) {
            console.error('Error loading resources:', error);
        }
    }
    
    setupEventHandlers() {
        const closeBtn = document.getElementById('appointmentDialogClose');
        const cancelBtn = document.getElementById('appointmentDialogCancel');
        const saveBtn = document.getElementById('appointmentDialogSave');
        const backdrop = this.modal;
        
        const close = () => this.close();
        
        closeBtn.addEventListener('click', close);
        cancelBtn.addEventListener('click', close);
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) close();
        });
        
        saveBtn.addEventListener('click', () => this.save());
    }
    
    open(data = {}) {
        this.currentData = data;
        const form = document.getElementById('appointmentDialogForm');
        const title = document.getElementById('appointmentDialogTitle');
        
        // Titel setzen
        title.textContent = data.id ? 'Termin bearbeiten' : 'Neuer Termin';
        
        // Formular zurücksetzen
        form.reset();
        
        // Daten füllen
        if (data.patient_name) {
            document.getElementById('appointmentPatient').value = data.patient_name;
            document.getElementById('appointmentPatientId').value = data.patient_id || '';
        }
        
        if (data.doctor_name) {
            document.getElementById('appointmentDoctor').value = data.doctor_name;
            document.getElementById('appointmentDoctorId').value = data.doctor_id || '';
        }
        
        if (data.start_time) {
            const start = new Date(data.start_time);
            const year = start.getFullYear();
            const month = String(start.getMonth() + 1).padStart(2, '0');
            const day = String(start.getDate()).padStart(2, '0');
            document.getElementById('appointmentDate').value = `${year}-${month}-${day}`;
            document.getElementById('appointmentStartTime').value = start.toTimeString().slice(0, 5);
            
            if (data.end_time) {
                const end = new Date(data.end_time);
                const duration = Math.round((end - start) / 60000);
                document.getElementById('appointmentDuration').value = duration;
            }
        }
        
        if (data.type_id) {
            document.getElementById('appointmentType').value = data.type_id;
        }
        
        if (data.notes) {
            document.getElementById('appointmentNotes').value = data.notes;
        }
        
        // Modal anzeigen
        this.modal.style.display = 'flex';
        this.modal.style.visibility = 'visible';
        // Force reflow to ensure display change is applied
        void this.modal.offsetHeight;
        setTimeout(() => {
            this.modal.classList.add('prx-modal-backdrop--open');
        }, 10);
    }
    
    close() {
        this.modal.classList.remove('prx-modal-backdrop--open');
        setTimeout(() => {
            this.modal.style.display = 'none';
            this.modal.style.visibility = 'hidden';
            this.currentData = null;
        }, 200);
    }
    
    async save() {
        const form = document.getElementById('appointmentDialogForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        const formData = new FormData(form);
        const data = {
            patient_id: parseInt(formData.get('patient_id')),
            doctor: parseInt(formData.get('doctor')),
            type: parseInt(formData.get('type')),
            notes: formData.get('notes') || '',
            resources: Array.from(formData.getAll('resources')).map(id => parseInt(id))
        };
        
        // Datum + Zeit kombinieren
        const date = formData.get('date');
        const time = formData.get('start_time');
        const duration = parseInt(formData.get('duration'));
        
        const startDateTime = new Date(`${date}T${time}`);
        const endDateTime = new Date(startDateTime.getTime() + duration * 60000);
        
        data.start_time = startDateTime.toISOString();
        data.end_time = endDateTime.toISOString();
        
        try {
            const url = this.currentData?.id 
                ? `/api/appointments/${this.currentData.id}/`
                : '/api/appointments/';
            const method = this.currentData?.id ? 'PATCH' : 'POST';
            
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
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Speichern fehlgeschlagen');
            }
            
            this.close();
            
            // Calendar Refresh Event
            window.dispatchEvent(new CustomEvent('appointmentSaved'));
            
            if (window.appointmentCalendar) {
                window.appointmentCalendar.refresh();
            }
        } catch (error) {
            console.error('Error saving appointment:', error);
            alert('Fehler beim Speichern: ' + error.message);
        }
    }
    
    getAuthHeader() {
        const token = localStorage.getItem('access_token');
        return token ? `Bearer ${token}` : '';
    }
    
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
}

// Global export
window.AppointmentDialog = AppointmentDialog;

// Helper function
window.openAppointmentDialog = function(data) {
    if (!window.appointmentDialogInstance) {
        window.appointmentDialogInstance = new AppointmentDialog();
    }
    window.appointmentDialogInstance.open(data);
};

