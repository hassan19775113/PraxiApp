#!/bin/bash

# Vercel Build Script for Django
echo "Building Django application for Vercel..."

# Install Python dependencies
pip install -r requirements.txt

# Change to Django project directory
cd django

# Collect static files
python manage.py collectstatic --noinput --settings=praxi_backend.settings.prod

echo "Build completed successfully!"
