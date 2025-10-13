#!/usr/bin/env python
"""
Script para testar conexão PostgreSQL no Heroku
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings_heroku_persistent')
django.setup()

try:
    from django.db import connection
    from django.core.management.color import no_style
    
    print("🔍 Testando conexão PostgreSQL...")
    
    # Testar conexão básica
    cursor = connection.cursor()
    cursor.execute('SELECT version()')
    result = cursor.fetchone()
    print(f"✅ PostgreSQL conectado: {result[0][:50]}...")
    
    # Testar se consegue listar tabelas
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    tables = cursor.fetchall()
    print(f"📊 Tabelas existentes: {len(tables)} tabelas")
    
    # Verificar se django_migrations existe
    cursor.execute("SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name='django_migrations')")
    has_migrations = cursor.fetchone()[0]
    print(f"🔄 Tabela django_migrations: {'✅ Existe' if has_migrations else '❌ Não existe'}")
    
    # Se não existe, criar
    if not has_migrations:
        print("🚀 Criando estrutura inicial...")
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
    
    print("🎉 Teste de conexão concluído!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)