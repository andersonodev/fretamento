#!/bin/bash

# Build script para Vercel

echo "🚀 Iniciando build para Vercel..."

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements-vercel.txt

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --settings=fretamento_project.settings_vercel

# Criar diretório para build
mkdir -p staticfiles_build

# Copiar arquivos estáticos para o diretório de build
cp -r staticfiles/* staticfiles_build/

echo "✅ Build concluído com sucesso!"