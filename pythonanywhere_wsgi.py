"""
WSGI config for fretamento_project project on PythonAnywhere.

This file will be placed at:
/var/www/seuusername_pythonanywhere_com_wsgi.py
"""

import os
import sys

# Adicionar diretório do projeto ao caminho do sistema
# Substitua 'seuusername' pelo seu nome de usuário no PythonAnywhere
# e 'fretamento-intertouring' pelo nome do diretório do seu projeto
path = '/home/seuusername/fretamento-intertouring'
if path not in sys.path:
    sys.path.append(path)

# Definir as configurações específicas para o PythonAnywhere
os.environ['DJANGO_SETTINGS_MODULE'] = 'fretamento_project.settings_pythonanywhere'

# Importar o objeto de aplicação WSGI do Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()