"""
Configurações específicas para deploy no Heroku (versão gratuita)
"""
import os
from .settings import *

# ============================================
# CONFIGURAÇÕES BÁSICAS DO HEROKU
# ============================================

# DEBUG deve ser False em produção
DEBUG = False

# Secret Key do Heroku Config Vars
SECRET_KEY = os.environ.get('SECRET_KEY')

# Allowed Hosts para Heroku
ALLOWED_HOSTS = [
    '.herokuapp.com',
    'localhost',
    '127.0.0.1',
]

# ============================================
# BANCO DE DADOS - SQLITE PARA PLANO GRATUITO
# ============================================

# Para manter o projeto 100% gratuito, usamos SQLite
# Em produção real, recomenda-se PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        },
        'CONN_MAX_AGE': 600,
    }
}

# ============================================
# MIDDLEWARE PARA HEROKU
# ============================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================
# ARQUIVOS ESTÁTICOS - WHITENOISE
# ============================================

# Servir arquivos estáticos com WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Media files (para upload de planilhas)
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# ============================================
# CACHE - LOCAL PARA PLANO GRATUITO
# ============================================

# Cache local para manter o projeto gratuito
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'fretamento-cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        },
    }
}

# ============================================
# CONFIGURAÇÕES DE SEGURANÇA
# ============================================

# HTTPS/SSL no Heroku
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Cookies seguras
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ============================================
# LOGGING PARA HEROKU
# ============================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'heroku': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'heroku',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'core': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'escalas': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'authentication': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# ============================================
# CONFIGURAÇÕES DE PERFORMANCE
# ============================================

# Otimizações de template
TEMPLATES[0]['APP_DIRS'] = False
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Limites de upload
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Timezone
USE_TZ = True