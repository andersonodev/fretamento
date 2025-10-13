#!/usr/bin/env python
"""
Script para testar login do usuário anderson
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings_heroku')
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

print("🔐 Testando autenticação do usuário 'anderson'...")

# Testar com diferentes combinações de senha
test_passwords = [
    "123",      # Senha simples
    "123456",   # Senha comum
    "anderson", # Nome do usuário
    "admin",    # Senha padrão
    "password", # Senha genérica
]

user = User.objects.get(username='anderson')
print(f"👤 Usuário encontrado: {user.username}")
print(f"🔑 Hash da senha: {user.password[:50]}...")

for password in test_passwords:
    authenticated_user = authenticate(username='anderson', password=password)
    if authenticated_user:
        print(f"✅ SUCESSO! Senha correta: '{password}'")
        break
    else:
        print(f"❌ Senha incorreta: '{password}'")

# Vamos também verificar se o usuário pode definir uma nova senha
print(f"\n🔧 Definindo nova senha 'senha123' para teste...")
user.set_password('senha123')
user.save()

# Testar a nova senha
authenticated_user = authenticate(username='anderson', password='senha123')
if authenticated_user:
    print(f"✅ NOVA SENHA FUNCIONANDO: 'senha123'")
else:
    print(f"❌ Erro ao definir nova senha")

print("\n📋 Instruções:")
print("1. Acesse: https://fretamento-intertouring-app-ca2ff72f9735.herokuapp.com/auth/login/")
print("2. Use: anderson / senha123")