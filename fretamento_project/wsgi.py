"""
WSGI config for fretamento_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Configurar settings module baseado no ambiente
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')

# Para Vercel, usar settings específicos
if os.environ.get('VERCEL') or 'vercel' in settings_module:
    settings_module = 'fretamento_project.settings_vercel'

os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

application = get_wsgi_application()

# Para compatibilidade com Vercel serverless
app = application
