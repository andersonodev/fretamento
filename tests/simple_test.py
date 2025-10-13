#!/usr/bin/env python
"""
Script simples para testar o fluxo de login
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings_heroku')
django.setup()

from django.contrib.auth import authenticate
from django.urls import reverse

print("🔐 Teste simples de login...")

print("\n1️⃣ Testando autenticação direta")
user = authenticate(username='anderson', password='senha123')
if user:
    print(f"✅ Autenticação OK: {user.username}")
    print(f"   - Ativo: {user.is_active}")
    print(f"   - Staff: {user.is_staff}")
    print(f"   - Superuser: {user.is_superuser}")
else:
    print("❌ Falha na autenticação")

print("\n2️⃣ Verificando URLs")
try:
    login_url = reverse('authentication:login')
    print(f"✅ URL login: {login_url}")
except Exception as e:
    print(f"❌ Erro URL login: {e}")

try:
    home_url = reverse('core:home')
    print(f"✅ URL home: {home_url}")
except Exception as e:
    print(f"❌ Erro URL home: {e}")

print("\n3️⃣ Testando settings")
from django.conf import settings
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"DEBUG: {settings.DEBUG}")

print("\n4️⃣ Verificando view de login")
from authentication.views import CustomLoginView
print(f"✅ CustomLoginView encontrada: {CustomLoginView}")

success_url = CustomLoginView().get_success_url()
print(f"✅ Success URL: {success_url}")

print("\n✅ Teste concluído!")