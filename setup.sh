#!/bin/bash

# Script de setup do Sistema de Fretamento

echo "🚌 Configurando Sistema de Fretamento..."

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale o Python 3 primeiro."
    exit 1
fi

# Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativa ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Instala dependências
echo "📚 Instalando dependências..."
pip install -r requirements.txt

# Executa migrações
echo "🗄️ Executando migrações do banco..."
python manage.py makemigrations
python manage.py migrate

# Cria superusuário se não existir
echo "👤 Verificando superusuário..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@fretamento.com', 'admin123')
    print('Superusuário criado: admin / admin123')
else:
    print('Superusuário já existe.')
"

# Coleta arquivos estáticos
echo "🎨 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

echo ""
echo "✅ Sistema configurado com sucesso!"
echo ""
echo "🚀 Para iniciar o servidor:"
echo "   source venv/bin/activate"
echo "   python manage.py runserver"
echo ""
echo "🌐 Acesse: http://localhost:8000"
echo "🔐 Admin: http://localhost:8000/admin (admin / admin123)"
echo ""
echo "📋 Próximos passos:"
echo "   1. Acesse o sistema"
echo "   2. Faça upload da planilha OS"
echo "   3. Crie e otimize suas escalas"