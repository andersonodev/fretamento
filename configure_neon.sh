#!/bin/bash

# =========================================
# SCRIPT DE CONFIGURAÇÃO NEON + HEROKU
# =========================================

echo "🚀 Configurando PostgreSQL Neon.tech no Heroku..."

# Verificar se DATABASE_URL foi fornecida
if [ -z "$1" ]; then
    echo "❌ ERRO: Forneça a CONNECTION STRING do Neon!"
    echo ""
    echo "📖 COMO USAR:"
    echo "./configure_neon.sh 'postgresql://usuario:senha@ep-exemplo.us-east-2.aws.neon.tech/fretamento_db?sslmode=require'"
    echo ""
    echo "🔍 Para encontrar a string:"
    echo "1. Acesse neon.tech"
    echo "2. Vá no seu projeto"
    echo "3. Clique em 'Connection Details'"
    echo "4. Copie 'Connection string'"
    exit 1
fi

DATABASE_URL="$1"
echo "📊 DATABASE_URL recebida: ${DATABASE_URL:0:30}..."

echo ""
echo "🔧 Configurando variáveis no Heroku..."

# Configurar DATABASE_URL
echo "📥 Configurando DATABASE_URL..."
heroku config:set DATABASE_URL="$DATABASE_URL"

# Configurar settings para persistente
echo "📥 Configurando Django Settings..."
heroku config:set DJANGO_SETTINGS_MODULE="fretamento_project.settings_heroku_persistent"

echo ""
echo "🔄 Executando migrações..."
heroku run python manage.py migrate

echo ""
echo "👤 Criando superusuário..."
echo "📝 Preencha as informações quando solicitado:"
heroku run python manage.py createsuperuser

echo ""
echo "🎯 Testando conectividade..."
heroku run python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT version()')
result = cursor.fetchone()
print('✅ PostgreSQL conectado:', result[0])
"

echo ""
echo "🔄 Forçando restart para aplicar mudanças..."
heroku restart

echo ""
echo "✅ CONFIGURAÇÃO CONCLUÍDA!"
echo "🌐 Acesse: https://fretamento-intertouring-app-ca2ff72f9735.herokuapp.com/"
echo "🛡️  Admin: https://fretamento-intertouring-app-ca2ff72f9735.herokuapp.com/admin/"
echo ""
echo "🎉 Dados agora são 100% PERSISTENTES!"