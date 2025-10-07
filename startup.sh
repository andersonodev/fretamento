#!/bin/bash

# Azure Web App startup script para Django
echo "🚀 Iniciando Fretamento Django App no Azure..."

# Definir variáveis de ambiente
export DEBUG=False
export USE_DOCKER=False
export DJANGO_SETTINGS_MODULE=fretamento_project.settings

# Instalar dependências
echo "📦 Instalando dependências..."
python -m pip install --upgrade pip

# Usar requirements específicos se existir
if [ -f requirements-azure.txt ]; then
    pip install -r requirements-azure.txt
else
    pip install -r requirements.txt
fi

# Configurar Django
echo "🔧 Configurando Django..."

# Coletar arquivos estáticos
echo "📊 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

# Executar migrações
echo "🗄️ Executando migrações..."
python manage.py migrate --noinput

# Iniciar Gunicorn
echo "🌐 Iniciando servidor Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 600 --keep-alive 2 fretamento_project.wsgi:application