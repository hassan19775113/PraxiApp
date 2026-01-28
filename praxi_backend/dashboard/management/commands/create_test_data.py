"""
Management Command: create_test_data

Erstellt Testdaten für Browser-Tests:
- Ärzte (Users mit Rolle 'doctor')
- Terminarten (AppointmentType)
- Ressourcen (Räume, Geräte, Personal)
- Termine (Appointments)

Verwendung:
    python manage.py create_test_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import random

from praxi_backend.core.models import User, Role
from praxi_backend.appointments.models import (
    Appointment,
    AppointmentType,
    Resource,
    AppointmentResource,
)


class Command(BaseCommand):
    help = 'Erstellt Testdaten für Browser-Tests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Löscht zuerst alle Testdaten',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Lösche Testdaten...'))
            self._clear_test_data()

        self.stdout.write(self.style.SUCCESS('Erstelle Testdaten...'))

        # Rollen erstellen (falls nicht vorhanden)
        self._create_roles()

        # Ärzte erstellen
        doctors = self._create_doctors()

        # Terminarten erstellen
        appointment_types = self._create_appointment_types()

        # Ressourcen erstellen
        resources = self._create_resources()

        # Termine erstellen
        appointments = self._create_appointments(doctors, appointment_types, resources)

        self.stdout.write(self.style.SUCCESS(f'\n[OK] Testdaten erfolgreich erstellt:'))
        self.stdout.write(self.style.SUCCESS(f'   - {len(doctors)} Aerzte'))
        self.stdout.write(self.style.SUCCESS(f'   - {len(appointment_types)} Terminarten'))
        self.stdout.write(self.style.SUCCESS(f'   - {len(resources)} Ressourcen'))
        self.stdout.write(self.style.SUCCESS(f'   - {len(appointments)} Termine'))

    def _create_roles(self):
        """Erstellt Rollen, falls nicht vorhanden."""
        role_names = ['admin', 'doctor', 'assistant', 'billing']
        for role_name in role_names:
            Role.objects.using('default').get_or_create(name=role_name)

    def _create_doctors(self):
        """Erstellt Test-Ärzte."""
        doctor_role, _ = Role.objects.using('default').get_or_create(name='doctor')

        doctors_data = [
            {'first_name': 'Dr. Anna', 'last_name': 'Müller', 'username': 'dr_mueller', 'email': 'a.mueller@praxis.de', 'color': '#4A90E2'},
            {'first_name': 'Dr. Thomas', 'last_name': 'Schmidt', 'username': 'dr_schmidt', 'email': 't.schmidt@praxis.de', 'color': '#7ED6C1'},
            {'first_name': 'Dr. Sarah', 'last_name': 'Weber', 'username': 'dr_weber', 'email': 's.weber@praxis.de', 'color': '#6FCF97'},
            {'first_name': 'Dr. Michael', 'last_name': 'Fischer', 'username': 'dr_fischer', 'email': 'm.fischer@praxis.de', 'color': '#F2C94C'},
            {'first_name': 'Dr. Lisa', 'last_name': 'Wagner', 'username': 'dr_wagner', 'email': 'l.wagner@praxis.de', 'color': '#EB5757'},
        ]

        doctors = []
        for data in doctors_data:
            user, created = User.objects.using('default').get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data['email'],
                    'is_active': True,
                    'is_staff': True,
                }
            )
            if created:
                user.set_password('test123')
                user.save(using='default')

            user.role = doctor_role
            user.calendar_color = data['color']
            user.save(using='default')

            doctors.append(user)

        return doctors

    def _create_appointment_types(self):
        """Erstellt Test-Terminarten."""
        types_data = [
            {'name': 'Konsultation', 'color': '#4A90E2', 'duration_minutes': 30},
            {'name': 'Nachsorge', 'color': '#7ED6C1', 'duration_minutes': 20},
            {'name': 'Operation', 'color': '#EB5757', 'duration_minutes': 60},
            {'name': 'Vorsorge', 'color': '#6FCF97', 'duration_minutes': 45},
            {'name': 'Beratung', 'color': '#F2C94C', 'duration_minutes': 25},
        ]

        types = []
        for data in types_data:
            type_obj, _ = AppointmentType.objects.using('default').get_or_create(
                name=data['name'],
                defaults={
                    'color': data['color'],
                    'duration_minutes': data['duration_minutes'],
                    'active': True,
                }
            )
            types.append(type_obj)

        return types

    def _create_resources(self):
        """Erstellt Test-Ressourcen."""
        resources_data = [
            # Räume
            {'name': 'Behandlungsraum 1', 'type': Resource.TYPE_ROOM, 'color': '#4A90E2'},
            {'name': 'Behandlungsraum 2', 'type': Resource.TYPE_ROOM, 'color': '#7ED6C1'},
            {'name': 'OP-Saal 1', 'type': Resource.TYPE_ROOM, 'color': '#EB5757'},
            {'name': 'Sprechzimmer', 'type': Resource.TYPE_ROOM, 'color': '#6FCF97'},
            # Geräte
            {'name': 'Röntgengerät', 'type': Resource.TYPE_DEVICE, 'color': '#4A90E2'},
            {'name': 'Ultraschall', 'type': Resource.TYPE_DEVICE, 'color': '#7ED6C1'},
            {'name': 'EKG-Gerät', 'type': Resource.TYPE_DEVICE, 'color': '#6FCF97'},
            # Personal
            {'name': 'MFA Müller', 'type': Resource.TYPE_DEVICE, 'color': '#F2C94C'},  # Note: TYPE_STAFF not available, using TYPE_DEVICE
            {'name': 'MFA Schmidt', 'type': Resource.TYPE_DEVICE, 'color': '#F2C94C'},  # Note: TYPE_STAFF not available, using TYPE_DEVICE
        ]

        resources = []
        for data in resources_data:
            resource, _ = Resource.objects.using('default').get_or_create(
                name=data['name'],
                type=data['type'],
                defaults={
                    'color': data['color'],
                    'active': True,
                }
            )
            resources.append(resource)

        return resources

    def _create_appointments(self, doctors, appointment_types, resources):
        """Erstellt Test-Termine."""
        appointments = []

        # Zeitraum: nächste 2 Wochen
        today = timezone.now().replace(hour=8, minute=0, second=0, microsecond=0)
        start_date = today.date()

        # Status-Optionen
        statuses = [
            Appointment.STATUS_SCHEDULED,
            Appointment.STATUS_CONFIRMED,
            Appointment.STATUS_COMPLETED,
            Appointment.STATUS_CANCELLED,
        ]

        # Patienten-IDs (wir verwenden hier Dummy-IDs für Termine/OPs)
        # Hinweis: Patient-Stammdaten liegen in der managed `patients` Tabelle.
        patient_ids = list(range(1, 11))  # IDs 1-10

        # Erstelle Termine für die nächsten 14 Tage
        for day_offset in range(14):
            current_date = start_date + timedelta(days=day_offset)
            
            # Nur Werktage (Mo-Fr)
            if current_date.weekday() >= 5:  # Samstag (5) oder Sonntag (6)
                continue

            # 5-8 Termine pro Tag
            num_appointments = random.randint(5, 8)

            for i in range(num_appointments):
                # Zufällige Zeit (8:00 - 17:00)
                hour = random.randint(8, 16)
                minute = random.choice([0, 15, 30, 45])

                start_time = timezone.make_aware(
                    datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute))
                )

                # Zufälliger Arzt, Terminart
                doctor = random.choice(doctors)
                appointment_type = random.choice(appointment_types)
                duration = timedelta(minutes=appointment_type.duration_minutes)
                end_time = start_time + duration

                # Zufälliger Status
                status = random.choice(statuses)

                # Zufälliger Patient
                patient_id = random.choice(patient_ids)

                # Erstelle Termin
                appointment = Appointment.objects.using('default').create(
                    patient_id=patient_id,
                    doctor=doctor,
                    type=appointment_type,
                    start_time=start_time,
                    end_time=end_time,
                    status=status,
                    notes=f'Test-Termin {i+1} am {current_date.strftime("%d.%m.%Y")}',
                )

                # Zufällige Ressourcen hinzufügen
                # 1-2 Ressourcen pro Termin
                num_resources = random.randint(1, 2)
                selected_resources = random.sample(resources, min(num_resources, len(resources)))

                for resource in selected_resources:
                    AppointmentResource.objects.using('default').create(
                        appointment=appointment,
                        resource=resource,
                    )

                appointments.append(appointment)

        return appointments

    def _clear_test_data(self):
        """Löscht Testdaten (optional)."""
        # Vorsicht: Löscht nur Testdaten, die mit diesem Command erstellt wurden
        # Identifikation über Username-Pattern oder andere Marker
        User.objects.using('default').filter(username__startswith='dr_').delete()
        Appointment.objects.using('default').filter(notes__startswith='Test-Termin').delete()
        # Ressourcen und Terminarten werden nicht gelöscht (könnten auch manuell erstellt sein)

