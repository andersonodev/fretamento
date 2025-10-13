#!/usr/bin/env python
"""
Script para testar POST do formulário de login
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings_heroku')
django.setup()

from django.test import Client
from django.urls import reverse

print("🔐 Testando POST do formulário de login...")

# Criar cliente de teste
client = Client()

# Obter URL do login
login_url = reverse('authentication:login')
print(f"📍 URL do login: {login_url}")

# Testar GET primeiro
print("\n1️⃣ Testando GET /auth/login/")
response = client.get(login_url)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type', 'N/A')}")

# Extrair CSRF token
from django.middleware.csrf import get_token
csrf_token = get_token(client)
print(f"CSRF Token obtido: {csrf_token[:20]}...")

# Testar POST com credenciais corretas
print("\n2️⃣ Testando POST com anderson/senha123")
post_data = {
    'username': 'anderson',
    'password': 'senha123',
    'csrfmiddlewaretoken': csrf_token
}

response = client.post(login_url, data=post_data, follow=True)
print(f"Status final: {response.status_code}")
print(f"URL final: {response.wsgi_request.path}")

# Verificar se está autenticado
if hasattr(response.wsgi_request, 'user') and response.wsgi_request.user.is_authenticated:
    print(f"✅ Login bem-sucedido! Usuário: {response.wsgi_request.user.username}")
else:
    print("❌ Login falhou!")
    if response.context and 'form' in response.context:
        form = response.context['form']
        if form.errors:
            print(f"Erros do formulário: {form.errors}")

print("\n3️⃣ Verificando URL de redirecionamento...")
try:
    home_url = reverse('core:home')
    print(f"URL core:home: {home_url}")
    
    # Testar se a home funciona
    response = client.get(home_url)
    print(f"Status da home: {response.status_code}")
except Exception as e:
    print(f"❌ Erro na URL core:home: {e}")

print("\n📊 Resumo dos testes concluído!")