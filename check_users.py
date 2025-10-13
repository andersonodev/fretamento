#!/usr/bin/env python
"""
Script para verificar usuários e configuração de autenticação
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings_heroku')
django.setup()

from django.contrib.auth.models import User

print("🔍 Verificando usuários no sistema...")

# Listar todos os usuários
users = User.objects.all()
print(f"📊 Total de usuários: {users.count()}")

for user in users:
    print(f"\n👤 Usuário: {user.username}")
    print(f"📧 Email: {user.email}")
    print(f"🔑 Superuser: {user.is_superuser}")
    print(f"👔 Staff: {user.is_staff}")
    print(f"✅ Ativo: {user.is_active}")
    print(f"🗓️ Último login: {user.last_login}")
    print(f"📅 Data criação: {user.date_joined}")

# Verificar especificamente o usuário anderson
anderson = User.objects.filter(username='anderson').first()
if anderson:
    print(f"\n✅ Usuário 'anderson' encontrado!")
    print(f"🔐 Senha definida: {'Sim' if anderson.password else 'Não'}")
else:
    print(f"\n❌ Usuário 'anderson' NÃO encontrado!")

print("\n🔍 Verificando configurações de autenticação...")

# Verificar URLs de autenticação
print("📋 Verificando apps instalados...")
from django.conf import settings
auth_apps = [app for app in settings.INSTALLED_APPS if 'auth' in app.lower()]
for app in auth_apps:
    print(f"  - {app}")