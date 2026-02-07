"""
Management command to set up the production database.
Runs migrations and creates default admin user.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection


class Command(BaseCommand):
    help = 'Setup production database: run migrations and create admin user'

    def handle(self, *args, **options):
        self.stdout.write('Starting production setup...')
        
        # Run migrations
        self.stdout.write('Running migrations...')
        from django.core.management import call_command
        call_command('migrate', '--noinput', verbosity=1, stdout=self.stdout)
        
        # Create admin user
        self.stdout.write('Creating admin user...')
        User = get_user_model()
        
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@praxiapp.local',
                password='praxiapp2026!Admin'
            )
            self.stdout.write(self.style.SUCCESS('✓ Admin user created'))
            self.stdout.write(self.style.WARNING('  Username: admin'))
            self.stdout.write(self.style.WARNING('  Password: praxiapp2026!Admin'))
            self.stdout.write(self.style.WARNING('  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ Admin user already exists'))
        
        self.stdout.write(self.style.SUCCESS('Production setup completed!'))
