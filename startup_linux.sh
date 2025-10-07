#!/bin/bash

# Azure Linux Web App startup script
echo "Starting Django application on Azure Linux..."

# Activate virtual environment if it exists
if [ -d "antenv" ]; then
    source antenv/bin/activate
fi

# Set environment variables
export DEBUG=False
export USE_DOCKER=False
export DJANGO_SETTINGS_MODULE=fretamento_project.settings

# Install dependencies
pip install -r requirements-azure.txt

# Run Django setup
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

# Start Gunicorn
gunicorn --bind=0.0.0.0 --timeout 600 fretamento_project.wsgi