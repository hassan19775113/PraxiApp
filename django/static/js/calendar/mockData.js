/**
 * Mock Appointment Data
 * 
 * Generiert Beispiel-Termine für die Kalender-Komponente
 */

export function generateMockAppointments() {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    const doctors = [
        { id: '1', name: 'Dr. Anna Müller', color: '#4A90E2' },
        { id: '2', name: 'Dr. Thomas Schmidt', color: '#7ED6C1' },
        { id: '3', name: 'Dr. Julia Meier', color: '#6FCF97' },
        { id: '4', name: 'Dr. David Lehmann', color: '#F2C94C' },
    ];
    
    const patients = [
        'Max Mustermann',
        'Maria Schmidt',
        'Peter Weber',
        'Lisa Fischer',
        'Hans Becker',
        'Anna Wagner',
    ];
    
    const appointments = [];
    
    // Generiere Termine für die nächsten 14 Tage
    for (let day = 0; day < 14; day++) {
        const date = new Date(today);
        date.setDate(date.getDate() + day);
        
        // Skip Wochenenden (optional)
        if (date.getDay() === 0 || date.getDay() === 6) continue;
        
        // 3-6 Termine pro Tag
        const numAppointments = Math.floor(Math.random() * 4) + 3;
        
        for (let i = 0; i < numAppointments; i++) {
            const doctor = doctors[Math.floor(Math.random() * doctors.length)];
            const patient = patients[Math.floor(Math.random() * patients.length)];
            
            // Startzeit zwischen 8:00 und 16:00
            const startHour = 8 + Math.floor(Math.random() * 9);
            const startMinute = Math.random() < 0.5 ? 0 : 30;
            
            const start = new Date(date);
            start.setHours(startHour, startMinute, 0, 0);
            
            // Dauer: 15, 30, 45 oder 60 Minuten
            const durations = [15, 30, 45, 60];
            const duration = durations[Math.floor(Math.random() * durations.length)];
            
            const end = new Date(start);
            end.setMinutes(end.getMinutes() + duration);
            
            appointments.push({
                id: `appt-${day}-${i}`,
                start: start.toISOString(),
                end: end.toISOString(),
                doctorName: doctor.name,
                doctorId: doctor.id,
                doctorColor: doctor.color,
                patientName: patient,
                title: `Termin mit ${patient}`,
                description: `Konsultation - ${patient}`,
            });
        }
    }
    
    return appointments;
}


