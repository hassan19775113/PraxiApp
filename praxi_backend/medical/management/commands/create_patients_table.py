"""
Management Command: create_patients_table

Erstellt die patients-Tabelle für Development (SQLite).
Da medical.Patient unmanaged ist, wird diese Tabelle normalerweise nicht durch Django erstellt.

Verwendung:
    python manage.py create_patients_table
"""

from django.core.management.base import BaseCommand
from django.db import connection, connections


class Command(BaseCommand):
    help = 'Erstellt die patients-Tabelle für Development (wenn nicht vorhanden)'

    def handle(self, *args, **options):
        # Verwende die 'medical' Datenbank oder 'default' falls medical nicht existiert
        db = 'medical' if 'medical' in connections else 'default'
        conn = connections[db]
        
        with conn.cursor() as cursor:
            # Prüfe, ob die Tabelle bereits existiert
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='patients'
            """)
            
            if cursor.fetchone():
                self.stdout.write(self.style.WARNING('Tabelle "patients" existiert bereits.'))
                return
            
            # Erstelle die Tabelle
            self.stdout.write('Erstelle Tabelle "patients"...')
            
            cursor.execute("""
                CREATE TABLE patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    birth_date DATE NOT NULL,
                    gender VARCHAR(20),
                    phone VARCHAR(50),
                    email VARCHAR(255),
                    created_at DATETIME,
                    updated_at DATETIME
                )
            """)
            
            self.stdout.write(self.style.SUCCESS('Tabelle "patients" erfolgreich erstellt!'))
            self.stdout.write(self.style.SUCCESS('Sie können jetzt "python manage.py seed" ausführen.'))

