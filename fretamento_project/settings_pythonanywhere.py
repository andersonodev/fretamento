"""
Django settings for fretamento_project project in PythonAnywhere environment.
"""

from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Adicionar o domínio do PythonAnywhere aos hosts permitidos
ALLOWED_HOSTS = ['andersonodev.pythonanywhere.com']

# Configuração para banco de dados MySQL no PythonAnywhere
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'andersonodev$fretamento_intertouring',
        'USER': 'andersonodev',
        'PASSWORD': '1907@@Jr',  # Senha definida no PythonAnywhere
        'HOST': 'andersonodev.mysql.pythonanywhere-services.com',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# Se você usar PostgreSQL (conta paga), use esta configuração:
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'fretamento_db',
        'USER': 'seuusername',
        'PASSWORD': 'db_password',
        'HOST': 'postgresql-seuusername.alwaysdata.net',
        'PORT': '5432',
    }
}
"""

# Configuração de Static e Media Files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Cache - Use memcached se disponível, senão use o LocMemCache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'fretamento-cache',
    }
}

# Configurações de Segurança
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = False  # Defina como True se tiver SSL configurado
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Performance para templates
TEMPLATES[0]['APP_DIRS'] = False
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Logging para arquivo
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'pythonanywhere_error.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}