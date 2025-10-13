#!/usr/bin/env python
"""
Script para rodar migrações no Vercel
Como o Vercel é serverless, precisamos rodar as migrações localmente
ou usar um comando específico
"""
import os
import django

# Configurar Django para Vercel
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings_vercel')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model

def setup_vercel_database():
    """Configura o banco de dados para o Vercel"""
    print("🔧 Configurando banco de dados para Vercel...")
    
    # Rodar migrações
    print("📊 Executando migrações...")
    call_command('migrate', '--run-syncdb')
    
    # Criar superusuário se não existir
    User = get_user_model()
    if not User.objects.filter(username='anderson').exists():
        print("👤 Criando superusuário...")
        User.objects.create_superuser(
            username='anderson',
            email='anderson@intertouring.com.br',
            password='senha123'
        )
        print("✅ Superusuário criado: anderson / senha123")
    else:
        print("👤 Superusuário já existe")
    
    # Coletar arquivos estáticos
    print("📁 Coletando arquivos estáticos...")
    call_command('collectstatic', '--noinput')
    
    print("✅ Configuração do Vercel concluída!")

if __name__ == '__main__':
    setup_vercel_database()