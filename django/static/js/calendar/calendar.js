/**
 * Modern Outlook-Style Calendar Component
 * 
 * Eine moderne, Outlook-inspirierte Kalender-Komponente mit:
 * - Monats-, Wochen- und Tagesansicht
 * - Drag & Drop (optional)
 * - Responsive Layout
 * - Fluent UI Design
 */

import { AppointmentModal } from './modal.js';

export class ModernCalendar {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = {
            apiUrl: options.apiUrl || '/api/appointments/',
            initialView: options.initialView || 'week',
            locale: options.locale || 'de',
            dayStartHour: options.dayStartHour ?? 7,
            dayEndHour: options.dayEndHour ?? 18,
            ...options,
        };
        
        this.currentDate = new Date();
        this.currentView = this.options.initialView;
        this.appointments = [];
        this.modal = null;
        this.dayStartHour = this.options.dayStartHour;
        this.dayEndHour = this.options.dayEndHour;
        
        if (!this.container) {
            console.error(`Calendar container not found: ${containerId}`);
            return;
        }
        
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
        this.modal = new AppointmentModal(
            (appointment) => this.handleSave(appointment),
            (id) => this.handleDelete(id)
        );
        
        this.render();
        this.loadAppointments();
    }
    
    render() {
        this.container.innerHTML = '';
        this.container.className = 'modern-calendar';
        
        // Toolbar
        const toolbar = this.createToolbar();
        this.container.appendChild(toolbar);
        
        // Calendar Grid
        const grid = this.createCalendarGrid();
        this.container.appendChild(grid);
        
        // View-Specific Rendering
        this.renderView();
    }
    
    createToolbar() {
        const toolbar = document.createElement('div');
        toolbar.className = 'calendar-toolbar';
        
        toolbar.innerHTML = `
            <div class="calendar-toolbar__left">
                <button class="calendar-btn calendar-btn--icon" id="calendarPrev" aria-label="Vorherige">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M15 18l-6-6 6-6"/>
                    </svg>
                </button>
                <button class="calendar-btn calendar-btn--icon" id="calendarToday" aria-label="Heute">
                    Heute
                </button>
                <button class="calendar-btn calendar-btn--icon" id="calendarNext" aria-label="Nächste">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 18l6-6-6-6"/>
                    </svg>
                </button>
                <h2 class="calendar-toolbar__title" id="calendarTitle">Kalender</h2>
            </div>
            <div class="calendar-toolbar__right">
                <div class="calendar-view-switcher">
                    <button class="calendar-view-btn ${this.currentView === 'day' ? 'active' : ''}" data-view="day">Tag</button>
                    <button class="calendar-view-btn ${this.currentView === 'week' ? 'active' : ''}" data-view="week">Woche</button>
                    <button class="calendar-view-btn ${this.currentView === 'month' ? 'active' : ''}" data-view="month">Monat</button>
                </div>
                <button class="calendar-btn calendar-btn--primary" id="calendarNewAppointment">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 5v14M5 12h14"/>
                    </svg>
                    Neuer Termin
                </button>
            </div>
        `;
        
        // Event Handlers
        toolbar.querySelector('#calendarPrev')?.addEventListener('click', () => this.navigate(-1));
        toolbar.querySelector('#calendarNext')?.addEventListener('click', () => this.navigate(1));
        toolbar.querySelector('#calendarToday')?.addEventListener('click', () => this.goToToday());
        toolbar.querySelector('#calendarNewAppointment')?.addEventListener('click', () => this.openNewAppointment());
        
        toolbar.querySelectorAll('.calendar-view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const view = e.target.dataset.view;
                this.switchView(view);
            });
        });
        
        return toolbar;
    }
    
    createCalendarGrid() {
        const grid = document.createElement('div');
        grid.className = `calendar-grid calendar-grid--${this.currentView}`;
        grid.id = 'calendarGrid';
        return grid;
    }
    
    renderView() {
        const grid = document.getElementById('calendarGrid');
        if (!grid) return;
        
        grid.innerHTML = '';
        
        switch (this.currentView) {
            case 'day':
                this.renderDayView(grid);
                break;
            case 'week':
                this.renderWeekView(grid);
                break;
            case 'month':
                this.renderMonthView(grid);
                break;
        }
        
        this.updateTitle();
        this.renderAppointments();
    }
    
    renderDayView(container) {
        const date = new Date(this.currentDate);
        const hours = Array.from({ length: this.dayEndHour - this.dayStartHour }, (_, i) => i + this.dayStartHour);
        
        container.innerHTML = `
            <div class="calendar-day-header">
                <div class="calendar-time-column"></div>
                <div class="calendar-day-column">
                    <div class="calendar-day-name">${this.formatDayName(date)}</div>
                    <div class="calendar-day-date">${this.formatDate(date)}</div>
                </div>
            </div>
            <div class="calendar-day-body">
                <div class="calendar-time-column">
                    ${hours.map(h => `
                        <div class="calendar-time-slot">
                            <span class="calendar-time-label">${String(h).padStart(2, '0')}:00</span>
                        </div>
                    `).join('')}
                </div>
                <div class="calendar-day-column">
                    <div class="calendar-day-timeline" data-date="${this.formatDateISO(date)}">
                        ${hours.map((h, i) => `
                            <div class="calendar-hour-slot" data-hour="${h}" data-minute="0"></div>
                            ${i < 23 ? `<div class="calendar-hour-slot calendar-hour-slot--half" data-hour="${h}" data-minute="30"></div>` : ''}
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        // Double-click handler für neue Termine
        container.querySelectorAll('.calendar-hour-slot').forEach(slot => {
            slot.addEventListener('dblclick', (e) => {
                const hour = parseInt(e.currentTarget.dataset.hour);
                const minute = parseInt(e.currentTarget.dataset.minute || 0);
                const start = new Date(date);
                start.setHours(hour, minute, 0, 0);
                const end = new Date(start);
                end.setMinutes(end.getMinutes() + 30);
                
                this.openNewAppointment({ start, end });
            });
        });
    }
    
    renderWeekView(container) {
        const weekStart = this.getWeekStart(this.currentDate);
        const days = Array.from({ length: 7 }, (_, i) => {
            const day = new Date(weekStart);
            day.setDate(day.getDate() + i);
            return day;
        });
        
        const hours = Array.from({ length: this.dayEndHour - this.dayStartHour }, (_, i) => i + this.dayStartHour);
        
        container.innerHTML = `
            <div class="calendar-week-header">
                <div class="calendar-time-column"></div>
                ${days.map(day => `
                    <div class="calendar-day-column">
                        <div class="calendar-day-name">${this.formatDayName(day)}</div>
                        <div class="calendar-day-date">${this.formatDate(day)}</div>
                    </div>
                `).join('')}
            </div>
            <div class="calendar-week-body">
                <div class="calendar-time-column">
                    ${hours.map(h => `
                        <div class="calendar-time-slot">
                            <span class="calendar-time-label">${String(h).padStart(2, '0')}:00</span>
                        </div>
                    `).join('')}
                </div>
                ${days.map(day => `
                    <div class="calendar-day-column">
                        <div class="calendar-day-timeline" data-date="${this.formatDateISO(day)}">
                            ${hours.map((h, i) => `
                                <div class="calendar-hour-slot" data-hour="${h}" data-minute="0"></div>
                                ${i < 23 ? `<div class="calendar-hour-slot calendar-hour-slot--half" data-hour="${h}" data-minute="30"></div>` : ''}
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        // Double-click handler
        container.querySelectorAll('.calendar-hour-slot').forEach(slot => {
            slot.addEventListener('dblclick', (e) => {
                const dateStr = e.currentTarget.closest('.calendar-day-timeline').dataset.date;
                const hour = parseInt(e.currentTarget.dataset.hour);
                const minute = parseInt(e.currentTarget.dataset.minute || 0);
                const start = new Date(dateStr);
                start.setHours(hour, minute, 0, 0);
                const end = new Date(start);
                end.setMinutes(end.getMinutes() + 30);
                
                this.openNewAppointment({ start, end });
            });
        });
    }
    
    renderMonthView(container) {
        const monthStart = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), 1);
        const monthEnd = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 1, 0);
        const weekStart = this.getWeekStart(monthStart);
        
        const weeks = [];
        let currentDate = new Date(weekStart);
        
        while (currentDate <= monthEnd || weeks.length < 6) {
            const week = Array.from({ length: 7 }, (_, i) => {
                const day = new Date(currentDate);
                day.setDate(currentDate.getDate() + i);
                return day;
            });
            weeks.push(week);
            currentDate.setDate(currentDate.getDate() + 7);
            
            if (weeks.length >= 6 && week[0].getMonth() !== monthStart.getMonth()) {
                break;
            }
        }
        
        const dayNames = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
        
        container.innerHTML = `
            <div class="calendar-month-header">
                ${dayNames.map(name => `<div class="calendar-month-day-name">${name}</div>`).join('')}
            </div>
            <div class="calendar-month-body">
                ${weeks.map(week => `
                    <div class="calendar-month-week">
                        ${week.map(day => {
                            const isCurrentMonth = day.getMonth() === monthStart.getMonth();
                            const isToday = this.isToday(day);
                            return `
                                <div class="calendar-month-day ${!isCurrentMonth ? 'calendar-month-day--other' : ''} ${isToday ? 'calendar-month-day--today' : ''}" 
                                     data-date="${this.formatDateISO(day)}">
                                    <div class="calendar-month-day-number">${day.getDate()}</div>
                                    <div class="calendar-month-day-events"></div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `).join('')}
            </div>
        `;
        
        // Double-click handler
        container.querySelectorAll('.calendar-month-day').forEach(dayEl => {
            dayEl.addEventListener('dblclick', (e) => {
                const dateStr = e.currentTarget.dataset.date;
                const start = new Date(dateStr);
                start.setHours(9, 0, 0, 0);
                const end = new Date(start);
                end.setHours(9, 30, 0, 0);
                
                this.openNewAppointment({ start, end });
            });
        });
    }
    
    renderAppointments() {
        // Clear existing appointments
        document.querySelectorAll('.calendar-appointment').forEach(el => el.remove());

        const titleQuery = (this.options.titleQuery || '').toLowerCase();
        const matchesTitle = (appointment) => {
            if (!titleQuery) return true;
            const title = (appointment.title || '').toLowerCase();
            return title.includes(titleQuery);
        };

        if (this.currentView === 'month') {
            this.appointments.forEach(appointment => {
                if (!matchesTitle(appointment)) return;
                const element = this.createAppointmentElement(appointment);
                const slot = this.findAppointmentSlot(appointment);
                if (slot) {
                    element.style.position = 'relative';
                    element.style.top = 'auto';
                    element.style.height = 'auto';
                    element.style.left = '0';
                    element.style.right = '0';
                    element.style.width = 'auto';
                    slot.appendChild(element);
                }
            });
            return;
        }

        const grouped = new Map();
        this.appointments.forEach(appointment => {
            if (!matchesTitle(appointment)) return;
            const start = new Date(appointment.start);
            const end = new Date(appointment.end);
            if (isNaN(start.getTime()) || isNaN(end.getTime())) {
                return;
            }
            const dateKey = this.formatDateISO(start);
            if (!grouped.has(dateKey)) grouped.set(dateKey, []);
            grouped.get(dateKey).push({ appointment, start, end });
        });

        grouped.forEach((items, dateKey) => {
            items.sort((a, b) => a.start - b.start || a.end - b.end);

            const columns = [];
            items.forEach(item => {
                let placed = false;
                for (let i = 0; i < columns.length; i++) {
                    if (item.start >= columns[i]) {
                        columns[i] = item.end;
                        item.column = i;
                        placed = true;
                        break;
                    }
                }
                if (!placed) {
                    item.column = columns.length;
                    columns.push(item.end);
                }
            });

            const totalCols = Math.max(1, columns.length);
            const gap = totalCols > 1 ? 2 : 0;
            const width = totalCols > 1 ? (100 - gap * (totalCols - 1)) / totalCols : 100;

            items.forEach(item => {
                const element = this.createAppointmentElement(item.appointment);
                const slot = document.querySelector(`.calendar-day-timeline[data-date="${dateKey}"]`);
                if (!slot) return;
                const left = item.column * (width + gap);
                element.style.left = `${left}%`;
                element.style.width = `${width}%`;
                element.style.right = 'auto';
                slot.appendChild(element);
            });
        });
    }
    
    createAppointmentElement(appointment) {
        // WICHTIG: appointment.start/end sind ISO-Strings
        // new Date() konvertiert automatisch UTC → lokale Zeit
        // KEINE zusätzliche Konvertierung!
        const start = new Date(appointment.start);
        const end = new Date(appointment.end);
        const duration = (end - start) / (1000 * 60); // Minuten
        
        const element = document.createElement('div');
        element.className = 'calendar-appointment';
        element.dataset.appointmentId = appointment.id;
        element.style.backgroundColor = appointment.doctorColor || '#4A90E2';
        
        // Position und Größe berechnen
        const top = this.calculateAppointmentTop(start);
        const height = this.calculateAppointmentHeight(duration);
        element.style.top = `${top}%`;
        element.style.height = `${height}%`;
        
        element.innerHTML = `
            <div class="calendar-appointment__title">${appointment.title || 'Termin'}</div>
            <div class="calendar-appointment__meta">
                <span class="calendar-appointment__doctor">${appointment.doctorName}</span>
                <span class="calendar-appointment__patient">${appointment.patientName}</span>
            </div>
            <div class="calendar-appointment__time">${this.formatTime(start)} - ${this.formatTime(end)}</div>
        `;
        
        // Double-click zum Bearbeiten
        // WICHTIG: Verwende eine Closure, um sicherzustellen, dass das korrekte Appointment-Objekt verwendet wird
        // Das Appointment-Objekt wird hier direkt im Closure gespeichert, nicht über this.appointments
        element.addEventListener('dblclick', (e) => {
            e.stopPropagation(); // Verhindere Event-Bubbling
            e.preventDefault(); // Verhindere Standard-Verhalten
            
            // Debug: Logge das Appointment-Objekt zur Fehlerdiagnose
            console.log('[ModernCalendar] Double-click on appointment:', {
                id: appointment.id,
                title: appointment.title,
                doctorName: appointment.doctorName,
                patientName: appointment.patientName,
                start: appointment.start,
                end: appointment.end,
                description: appointment.description,
                fullObject: appointment
            });
            
            // Validiere, dass das Appointment-Objekt vollständig ist
            if (!appointment || !appointment.id) {
                console.error('[ModernCalendar] Invalid appointment object:', appointment);
                alert('Fehler: Termin-Daten konnten nicht geladen werden.');
                return;
            }
            
            // Öffne Modal mit vollständigem Appointment-Objekt
            // Das Modal erkennt automatisch, dass es sich um eine Bearbeitung handelt (appointment !== null)
            if (this.modal && typeof this.modal.open === 'function') {
                this.modal.open(appointment);
            } else {
                console.error('[ModernCalendar] Modal not initialized or open method not available');
                alert('Fehler: Termin-Dialog konnte nicht geöffnet werden.');
            }
        });
        
        return element;
    }
    
    findAppointmentSlot(appointment) {
        // WICHTIG: appointment.start ist ISO-String
        // new Date() konvertiert automatisch UTC → lokale Zeit
        // formatDateISO() verwendet lokale Zeit (getFullYear(), getMonth(), getDate())
        const start = new Date(appointment.start);
        const dateStr = this.formatDateISO(start);
        
        if (this.currentView === 'month') {
            const dayEl = document.querySelector(`.calendar-month-day[data-date="${dateStr}"]`);
            return dayEl?.querySelector('.calendar-month-day-events');
        } else {
            const timeline = document.querySelector(`.calendar-day-timeline[data-date="${dateStr}"]`);
            return timeline;
        }
    }
    
    calculateAppointmentTop(startDate) {
        const hours = startDate.getHours();
        const minutes = startDate.getMinutes();
        const visibleMinutes = (this.dayEndHour - this.dayStartHour) * 60;
        if (visibleMinutes <= 0) return 0;
        const minutesFromStart = (hours * 60 + minutes) - (this.dayStartHour * 60);
        const clamped = Math.max(0, Math.min(visibleMinutes, minutesFromStart));
        return (clamped / visibleMinutes) * 100;
    }
    
    calculateAppointmentHeight(durationMinutes) {
        const visibleMinutes = (this.dayEndHour - this.dayStartHour) * 60;
        if (visibleMinutes <= 0) return 0;
        return (durationMinutes / visibleMinutes) * 100;
    }
    
    navigate(direction) {
        const amount = this.currentView === 'month' ? { months: direction } :
                      this.currentView === 'week' ? { weeks: direction } :
                      { days: direction };
        
        if (amount.months) {
            this.currentDate.setMonth(this.currentDate.getMonth() + amount.months);
        } else if (amount.weeks) {
            this.currentDate.setDate(this.currentDate.getDate() + (amount.weeks * 7));
        } else {
            this.currentDate.setDate(this.currentDate.getDate() + amount.days);
        }
        
        this.renderView();
        this.loadAppointments();
    }
    
    goToToday() {
        this.currentDate = new Date();
        this.renderView();
        this.loadAppointments();
    }
    
    switchView(view) {
        this.currentView = view;
        this.render();
        this.loadAppointments();
    }
    
    updateTitle() {
        const titleEl = document.getElementById('calendarTitle');
        if (!titleEl) return;
        
        let title = '';
        if (this.currentView === 'month') {
            title = this.formatMonthYear(this.currentDate);
        } else if (this.currentView === 'week') {
            const weekStart = this.getWeekStart(this.currentDate);
            const weekEnd = new Date(weekStart);
            weekEnd.setDate(weekEnd.getDate() + 6);
            title = `${this.formatDate(weekStart)} - ${this.formatDate(weekEnd)}`;
        } else {
            title = this.formatDate(this.currentDate);
        }
        
        titleEl.textContent = title;
    }
    
    /**
     * Öffnet das Modal für einen neuen Termin
     * 
     * @param {Object|null} defaultTimes - Optionale Standard-Zeiten {start: Date, end: Date}
     */
    openNewAppointment(defaultTimes = null) {
        // Für neuen Termin: null übergeben (Modal erkennt Erstellungs-Modus)
        // Optional: Standard-Zeiten übergeben (z.B. von Doppelklick auf Zeit-Slot)
        this.modal.open(null, defaultTimes);
    }
    
    /**
     * Behandelt das Speichern eines Termins (Create oder Update)
     * 
     * Sendet das Appointment an das Backend und aktualisiert die lokale Liste.
     * 
     * @param {Object} appointment - Das zu speichernde Appointment-Objekt
     */
    async handleSave(appointment) {
        if (!appointment) {
            console.error('[ModernCalendar] handleSave: appointment is null/undefined');
            return;
        }
        
        try {
            // Prüfe ob es ein Update oder Create ist
            const existingIndex = this.appointments.findIndex(a => a.id === appointment.id);
            const isUpdate = existingIndex !== -1;
            
            // Bereite Backend-Payload vor
            const payload = {
                patient_id: appointment.patientId,
                doctor: appointment.doctorId,
                type: appointment.appointmentTypeId,
                start_time: appointment.start, // ISO-String
                end_time: appointment.end, // ISO-String
                notes: appointment.description || '',
            };
            
            // Optional: resource_ids falls vorhanden
            if (appointment.resourceIds && appointment.resourceIds.length > 0) {
                payload.resource_ids = appointment.resourceIds;
            }
            
            console.log(`[ModernCalendar] ${isUpdate ? 'Updating' : 'Creating'} appointment:`, payload);
            
            // API-Aufruf
            const url = isUpdate 
                ? `${this.options.apiUrl}${appointment.id}/`
                : this.options.apiUrl;
            
            const method = isUpdate ? 'PATCH' : 'POST';
            
            // CSRF-Token holen
            const csrfToken = this.getCsrfToken();
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken,
                    ...this.getAuthHeaders(),
                },
                credentials: 'same-origin',
                body: JSON.stringify(payload),
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const savedAppointment = await response.json();
            console.log('[ModernCalendar] Appointment saved to backend:', savedAppointment);
            
            // Transformiere gespeichertes Appointment zu internem Format
            const transformed = this.transformAppointments([savedAppointment])[0];
            
            if (isUpdate) {
                // UPDATE: Aktualisiere vorhandenen Termin
                this.appointments[existingIndex] = transformed;
            } else {
                // CREATE: Füge neuen Termin hinzu
                this.appointments.push(transformed);
            }
            
            // Rendere Kalender neu, um Änderungen anzuzeigen
            this.renderAppointments();
            
            // Lade Appointments neu, um sicherzustellen, dass alles synchronisiert ist
            await this.loadAppointments();
            
        } catch (error) {
            console.error('[ModernCalendar] Error saving appointment:', error);
            alert(`Fehler beim Speichern des Termins: ${error.message}`);
        }
    }
    
    /**
     * Holt CSRF-Token aus Cookies
     */
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
        return cookieValue || '';
    }
    
    /**
     * Behandelt das Löschen eines Termins
     * 
     * Sendet DELETE-Request an das Backend und entfernt den Termin aus der lokalen Liste.
     * 
     * @param {string|number} id - Die ID des zu löschenden Termins
     */
    async handleDelete(id) {
        if (!id) {
            console.error('[ModernCalendar] handleDelete: id is null/undefined');
            return;
        }
        
        try {
            console.log('[ModernCalendar] Deleting appointment:', id);
            
            // CSRF-Token holen
            const csrfToken = this.getCsrfToken();
            
            // API-Aufruf
            const response = await fetch(`${this.options.apiUrl}${id}/`, {
                method: 'DELETE',
                headers: {
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken,
                    ...this.getAuthHeaders(),
                },
                credentials: 'same-origin',
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            console.log('[ModernCalendar] Appointment deleted from backend:', id);
            
            // Entferne aus lokaler Liste
            this.appointments = this.appointments.filter(a => a.id != id);
            
            // Rendere Kalender neu
            this.renderAppointments();

            if (typeof this.options.onAppointmentsLoaded === 'function') {
                this.options.onAppointmentsLoaded(this.appointments);
            }
            
            // Lade Appointments neu, um sicherzustellen, dass alles synchronisiert ist
            await this.loadAppointments();
            
        } catch (error) {
            console.error('[ModernCalendar] Error deleting appointment:', error);
            alert(`Fehler beim Löschen des Termins: ${error.message}`);
        }
    }
    
    /**
     * Lädt Appointments von der Backend-API
     * 
     * WICHTIG: Timestamp-Konvertierung
     * - Backend gibt UTC-Timestamps zurück (z.B. "2026-01-07T08:00:00Z")
     * - JavaScript's new Date() konvertiert automatisch in lokale Zeitzone
     * - KEINE zusätzliche manuelle Zeitzonen-Konvertierung!
     */
    async loadAppointments() {
        try {
        // Bestimme Datumsbereich basierend auf aktueller Ansicht
        let params = null;
        const debugEl = document.getElementById('calendarRangeDebug');
        if (this.currentView === 'day') {
            params = new URLSearchParams({
                date: this.formatDateISO(this.currentDate),
            });
        } else if (this.currentView === 'week') {
            const weekStart = this.getWeekStart(this.currentDate);
            const weekEnd = new Date(weekStart);
            weekEnd.setDate(weekEnd.getDate() + 6);
            params = new URLSearchParams({
                start_date: this.formatDateISO(weekStart),
                end_date: this.formatDateISO(weekEnd),
            });
        } else if (this.currentView === 'month') {
            const monthStart = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), 1);
            const monthEnd = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 1, 0);
            const gridStart = this.getWeekStart(monthStart);
            const gridEnd = new Date(monthEnd);
            const day = gridEnd.getDay(); // 0 = So
            const addDays = day === 0 ? 0 : (7 - day);
            gridEnd.setDate(gridEnd.getDate() + addDays);
            params = new URLSearchParams({
                start_date: this.formatDateISO(gridStart),
                end_date: this.formatDateISO(gridEnd),
            });
        }
        
        if (params && !params.has('limit')) {
            params.set('limit', '5000');
        }
        if (params && this.options.doctorId) {
            params.set('doctor_id', String(this.options.doctorId));
        }
        
        // API-Aufruf mit Datums-Filter
        const url = params
            ? `${this.options.apiUrl}?${params.toString()}`
            : this.options.apiUrl;
            
            console.log('[ModernCalendar] Loading appointments from:', url);
            if (debugEl && params) {
                debugEl.textContent = `Range: ${params.get('start_date') || '-'} bis ${params.get('end_date') || '-'} | View: ${this.currentView}`;
            }
            
            const response = await fetch(url, {
                headers: {
                    'Accept': 'application/json',
                    ...this.getAuthHeaders(),
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // DRF gibt manchmal data.results zurück (bei Pagination), manchmal direkt data
            let appointments = [];
            if (Array.isArray(data)) {
                appointments = data;
            } else if (data && Array.isArray(data.results)) {
                appointments = data.results;
            }
            
            console.log(`[ModernCalendar] Loaded ${appointments.length} appointments from API`);
            
            // Transformiere API-Response zu internem Format
            this.appointments = this.transformAppointments(appointments);
            
            // Rendere Kalender neu
            this.renderAppointments();
        } catch (error) {
            console.error('[ModernCalendar] Error loading appointments:', error);
            // Bei Fehler: Leere Liste anzeigen
            this.appointments = [];
            this.renderAppointments();
        }
    }
    
    /**
     * Transformiert API-Response zu internem Appointment-Format
     * 
     * WICHTIG: Timestamp-Konvertierung
     * - API gibt start_time/end_time als ISO-Strings zurück (z.B. "2026-01-07T08:00:00Z")
     * - new Date() konvertiert automatisch in lokale Zeitzone
     * - KEINE zusätzliche Konvertierung!
     */
    transformAppointments(apiAppointments) {
        return apiAppointments.map(apiAppt => {
            // Konvertiere ISO-Strings zu Date-Objekten
            // WICHTIG: new Date() konvertiert automatisch UTC → lokale Zeit
            // KEINE zusätzliche manuelle Konvertierung!
            const start = new Date(apiAppt.start_time);
            const end = new Date(apiAppt.end_time);
            
            // Validiere, dass Datum-Objekte gültig sind
            if (isNaN(start.getTime()) || isNaN(end.getTime())) {
                console.error('[ModernCalendar] Invalid date in appointment:', apiAppt);
                return null;
            }
            
            const doctorName = apiAppt.doctor_name || apiAppt.doctor?.name || '';
            const doctorId = apiAppt.doctor?.id ?? apiAppt.doctor;
            const doctorKey = doctorName || (doctorId != null ? String(doctorId) : '');

            const fallbackColor = this.getDoctorColor(doctorKey);
            const apiDoctorColor = apiAppt.doctor_color;
            const doctorColor = apiDoctorColor && apiDoctorColor !== '#1E90FF'
                ? apiDoctorColor
                : fallbackColor;

            return {
                id: apiAppt.id,
                // Speichere als ISO-String für Konsistenz
                start: start.toISOString(),
                end: end.toISOString(),
                // Anzeigenamen
                title: apiAppt.type?.name || 'Termin',
                doctorName: doctorName,
                patientName: apiAppt.patient_name || '',
                description: apiAppt.notes || '',
                // IDs für Backend
                appointmentTypeId: apiAppt.type?.id,
                doctorId: doctorId,
                patientId: apiAppt.patient_id,
                // Farben
                doctorColor: doctorColor,
                appointmentColor: apiAppt.appointment_color,
            };
        }).filter(appt => appt !== null); // Entferne ungültige Appointments
    }
    
    getDoctorColor(doctorName) {
        // Einfache Hash-Funktion für konsistente Farben
        const colors = ['#A8C7F4', '#A7D8CF', '#BFE6C8', '#F3E3B1', '#E7C3D3', '#C9D8F2', '#B7C9E6'];
        let hash = 0;
        for (let i = 0; i < doctorName.length; i++) {
            hash = doctorName.charCodeAt(i) + ((hash << 5) - hash);
        }
        return colors[Math.abs(hash) % colors.length];
    }
    
    getWeekStart(date) {
        const d = new Date(date);
        const day = d.getDay();
        const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Montag als Start
        return new Date(d.setDate(diff));
    }
    
    isToday(date) {
        const today = new Date();
        return date.getDate() === today.getDate() &&
               date.getMonth() === today.getMonth() &&
               date.getFullYear() === today.getFullYear();
    }
    
    formatDate(date) {
        return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });
    }
    
    /**
     * Formatiert ein Date-Objekt zu YYYY-MM-DD (lokale Zeit)
     * 
     * WICHTIG: Verwendet lokale Zeit, nicht UTC!
     * toISOString() würde UTC verwenden, was zu falschen Datumswerten führen kann.
     */
    formatDateISO(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    formatDayName(date) {
        return date.toLocaleDateString('de-DE', { weekday: 'short' });
    }
    
    formatMonthYear(date) {
        return date.toLocaleDateString('de-DE', { month: 'long', year: 'numeric' });
    }
    
    formatTime(date) {
        return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
    }
}

