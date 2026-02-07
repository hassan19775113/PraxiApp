/**
 * Modern Calendar Component - Entry Point
 * 
 * Initialisiert die Kalender-Komponente im Container #appointmentCalendar
 */

import { ModernCalendar } from './calendar.js';

// Warte bis DOM bereit ist
function initCalendar() {
    const container = document.getElementById('appointmentCalendar');
    
    if (!container) {
        console.error('[Modern Calendar] Container #appointmentCalendar not found');
        return;
    }
    
    // Initialisiere Kalender
    const calendar = new ModernCalendar('appointmentCalendar', {
        apiUrl: '/api/appointments/',
        initialView: 'week',
        locale: 'de',
    });
    
    // Globale Referenz für Debugging
    window.modernCalendar = calendar;
    
    console.log('[Modern Calendar] Initialized');
}

// Initialisierung
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCalendar);
} else {
    initCalendar();
}


