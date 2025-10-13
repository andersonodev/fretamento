#!/usr/bin/env python
"""
Teste real de login usando requests HTTP direto
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings_heroku')
django.setup()

import requests
from django.conf import settings
from django.urls import reverse
from authentication.views import CustomLoginView
from core.views import home
import sys

def test_login_flow():
    """Testa o fluxo de login usando requests HTTP"""
    
    print("🔐 Teste REAL de login via HTTP...")
    
    # URL base do Heroku
    BASE_URL = "https://fretamento-intertouring-app-ca2ff72f9735.herokuapp.com"
    
    try:
        # 1. Primeiro, pegar a página de login para obter o CSRF token
        print("\n1️⃣ Obtendo página de login...")
        session = requests.Session()
        
        login_url = f"{BASE_URL}/auth/login/"
        response = session.get(login_url)
        
        print(f"   Status: {response.status_code}")
        print(f"   URL final: {response.url}")
        
        if response.status_code != 200:
            print(f"❌ Erro ao acessar página de login: {response.status_code}")
            print(response.text[:500])
            return
        
        # 2. Extrair CSRF token do HTML
        print("\n2️⃣ Extraindo CSRF token...")
        html = response.text
        csrf_start = html.find('name="csrfmiddlewaretoken" value="')
        if csrf_start == -1:
            print("❌ CSRF token não encontrado!")
            return
            
        csrf_start += len('name="csrfmiddlewaretoken" value="')
        csrf_end = html.find('"', csrf_start)
        csrf_token = html[csrf_start:csrf_end]
        
        print(f"   CSRF Token: {csrf_token[:20]}...")
        
        # 3. Fazer login
        print("\n3️⃣ Fazendo login...")
        
        login_data = {
            'username': 'anderson',
            'password': 'senha123',
            'csrfmiddlewaretoken': csrf_token,
        }
        
        # Headers importantes
        headers = {
            'Referer': login_url,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        response = session.post(login_url, data=login_data, headers=headers, allow_redirects=False)
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        # 4. Verificar resultado
        if response.status_code == 302:
            redirect_url = response.headers.get('Location', '')
            print(f"✅ Redirecionamento: {redirect_url}")
            
            # Seguir redirecionamento
            if redirect_url:
                if redirect_url.startswith('/'):
                    redirect_url = BASE_URL + redirect_url
                
                print("\n4️⃣ Seguindo redirecionamento...")
                response = session.get(redirect_url)
                print(f"   Status: {response.status_code}")
                print(f"   URL final: {response.url}")
                
                if "Sistema de Fretamento" in response.text or "Dashboard" in response.text:
                    print("✅ Login realizado com sucesso!")
                else:
                    print("⚠️ Redirecionado, mas página pode não estar correta")
                    print(f"   Conteúdo: {response.text[:200]}...")
        else:
            print(f"❌ Login falhou: {response.status_code}")
            print(f"   Conteúdo: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Erro durante teste: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_login_flow()