"""
Configurações específicas para deploy na Vercel
"""
import os
from .settings import *

# Vercel Configuration
DEBUG = False
ALLOWED_HOSTS = [
    '.vercel.app',
    'localhost',
    '127.0.0.1',
    # Adicione seu domínio customizado aqui
    'fretamento-intertouring.vercel.app',
]

# Database - SQLite para Vercel
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/db.sqlite3',  # Vercel usa /tmp para arquivos temporários
    }
}

# Static files para Vercel
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configurações de segurança para produção
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Session e cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# CSRF para Vercel
CSRF_TRUSTED_ORIGINS = [
    'https://*.vercel.app',
    'https://fretamento-intertouring.vercel.app',
]

# Cache usando sistema de arquivos (compatível com Vercel)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp/django_cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Logging simplificado para Vercel
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'escalas': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Template otimizado para produção
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Configurações específicas da Vercel
# A Vercel automaticamente define essas variáveis de ambiente
if os.environ.get('VERCEL'):
    # Secret key deve vir de variável de ambiente
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', SECRET_KEY)
    
    # Configurar domínio da Vercel
    VERCEL_URL = os.environ.get('VERCEL_URL')
    if VERCEL_URL:
        ALLOWED_HOSTS.append(VERCEL_URL)
        CSRF_TRUSTED_ORIGINS.append(f'https://{VERCEL_URL}')

# Configurações otimizadas para serverless
USE_TZ = True
TIME_ZONE = 'America/Sao_Paulo'

# Desabilitar algumas funcionalidades não compatíveis com serverless
CONN_MAX_AGE = 0  # Não usar connection pooling em serverless