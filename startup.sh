#!/bin/bash

# Azure Web App startup script for Django
echo "🚀 Starting Fretamento Django App on Azure..."

# Set environment variables for production
export DEBUG=False
export USE_DOCKER=False
export DJANGO_SETTINGS_MODULE=fretamento_project.settings

# Install dependencies if not cached
echo "📦 Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Run Django setup
echo "🔧 Running Django setup..."

# Collect static files
echo "📊 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

# Create superuser if needed (for first deploy)
echo "👤 Creating superuser if needed..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@fretamento.com', 'admin123')
    print('✅ Superuser created')
else:
    print('ℹ️ Superuser already exists')
" || echo "⚠️ Superuser creation skipped"

# Start Gunicorn
echo "🌐 Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 600 --keep-alive 2 --max-requests 1000 fretamento_project.wsgi:application