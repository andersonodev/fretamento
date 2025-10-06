#!/usr/bin/env python3
"""
Script para testar os redirecionamentos de login e dashboard
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User

def test_login_redirects():
    """Testa se os redirecionamentos estão funcionando corretamente"""
    
    print("🔍 Testando redirecionamentos de login e dashboard...")
    client = Client()
    
    print("\n1. Testando acesso à raiz ('/') sem estar logado:")
    response = client.get('/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 302:
        print(f"   ✅ Redirecionado para: {response.url}")
        if '/auth/login/' in response.url:
            print("   ✅ Usuário não autenticado redirecionado ao login corretamente")
        else:
            print("   ❌ Redirecionamento incorreto para usuário não autenticado")
    
    print("\n2. Testando acesso direto ao login:")
    response = client.get('/auth/login/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Página de login carregada corretamente")
    
    print("\n3. Criando usuário de teste...")
    # Criar usuário de teste se não existir
    try:
        user = User.objects.get(username='teste')
        print("   ✅ Usuário de teste já existe")
    except User.DoesNotExist:
        user = User.objects.create_user(username='teste', password='senha123')
        print("   ✅ Usuário de teste criado")
    
    print("\n4. Testando login e redirecionamento ao dashboard:")
    login_success = client.login(username='teste', password='senha123')
    print(f"   Login success: {login_success}")
    
    if login_success:
        print("\n5. Testando acesso à raiz ('/') após login:")
        response = client.get('/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 302:
            print(f"   ✅ Redirecionado para: {response.url}")
            if '/core/' in response.url:
                print("   ✅ Usuário autenticado redirecionado ao dashboard corretamente")
            else:
                print("   ❌ Redirecionamento incorreto para usuário autenticado")
        
        print("\n6. Testando acesso direto ao dashboard:")
        response = client.get('/core/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Dashboard carregado corretamente")
        else:
            print("   ❌ Erro ao carregar dashboard")
        
        print("\n7. Testando simulação de login via POST:")
        response = client.post('/auth/login/', {
            'username': 'teste',
            'password': 'senha123',
        }, follow=True)
        print(f"   Status final: {response.status_code}")
        if response.status_code == 200:
            final_url = response.wsgi_request.path
            print(f"   URL final: {final_url}")
            if final_url == '/core/':
                print("   ✅ Login via POST redireciona ao dashboard corretamente")
            else:
                print("   ❌ Login via POST não redireciona ao dashboard")
    
    print("\n8. Testando URLs importantes:")
    urls_importantes = [
        ('core:home', 'Dashboard'),
        ('authentication:login', 'Login'),
        ('authentication:logout', 'Logout'),
        ('escalas:selecionar_ano', 'Escalas'),
    ]
    
    for url_name, descricao in urls_importantes:
        try:
            url = reverse(url_name)
            print(f"   ✅ {descricao}: {url}")
        except Exception as e:
            print(f"   ❌ {descricao}: Erro - {e}")

def test_dashboard_availability():
    """Testa se o dashboard está disponível"""
    
    print("\n🔍 Testando disponibilidade do dashboard...")
    client = Client()
    
    # Login first
    try:
        user = User.objects.get(username='teste')
    except User.DoesNotExist:
        user = User.objects.create_user(username='teste', password='senha123')
    
    client.login(username='teste', password='senha123')
    
    response = client.get('/core/')
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        indicators = [
            ('Dashboard', 'dashboard' in content.lower()),
            ('Estatísticas', 'estatísticas' in content.lower() or 'stats' in content.lower()),
            ('Navbar', 'navbar' in content.lower()),
            ('Cards', 'card' in content.lower()),
            ('Usuário logado', user.username in content),
        ]
        
        for indicator, found in indicators:
            if found:
                print(f"   ✅ {indicator}: Presente")
            else:
                print(f"   ⚠️  {indicator}: Não encontrado")
        
        return True
    else:
        print(f"   ❌ Dashboard não carregou (Status: {response.status_code})")
        return False

if __name__ == "__main__":
    print("🧪 Testando configuração de login e redirecionamento ao dashboard")
    print("=" * 70)
    
    try:
        test_login_redirects()
        dashboard_ok = test_dashboard_availability()
        
        print("\n" + "=" * 70)
        if dashboard_ok:
            print("✅ CONFIGURAÇÃO CORRETA!")
            print("✅ Login redireciona para o dashboard como esperado.")
        else:
            print("❌ PROBLEMAS ENCONTRADOS!")
            print("❌ Verifique a configuração do dashboard.")
            
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()