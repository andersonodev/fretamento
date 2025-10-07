#!/bin/bash

# Azure Web App startup script para Django
echo "🚀 Iniciando Fretamento Django App no Azure..."

# Definir variáveis de ambiente
export DEBUG=False
export USE_DOCKER=False
export DJANGO_SETTINGS_MODULE=fretamento_project.settings

# Ir para o diretório correto
cd /home/site/wwwroot

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

# Executar migrações
echo "�️ Executando migrações..."
python manage.py migrate --noinput

# Coletar arquivos estáticos
echo "� Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

# Iniciar Gunicorn na porta especificada pelo Azure
echo "🌐 Iniciando servidor Gunicorn..."
port=${PORT:-8000}
exec gunicorn --bind 0.0.0.0:$port --workers 2 --timeout 600 --keep-alive 2 --access-logfile - --error-logfile - fretamento_project.wsgi:application