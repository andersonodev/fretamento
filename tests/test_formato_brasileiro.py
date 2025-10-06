#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
import uuid

def test_brazilian_format():
    client = Client()
    
    # Usar ou criar usuário existente
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        try:
            user = User.objects.create_user(
                username=f'testuser_{uuid.uuid4().hex[:8]}',
                password='testpass123',
                email='test@test.com'
            )
        except:
            # Se não conseguir criar, pega o primeiro usuário
            user = User.objects.first()
            if not user:
                print("❌ Nenhum usuário encontrado no sistema")
                return
    
    # Fazer login
    if hasattr(user, 'username'):
        login_success = client.login(username=user.username, password='testpass123')
        if not login_success:
            # Tentar com admin/admin
            login_success = client.login(username='admin', password='admin')
    
    if not login_success:
        print("⚠️  Testando sem autenticação...")
    else:
        print("✅ Login realizado com sucesso")
    
    print("\n🇧🇷 Testando URLs com formato brasileiro (DD-MM-YYYY)...")
    
    # Testar URLs brasileiras
    urls_teste = [
        ('escalas:visualizar_escala', '04-10-2025'),
        ('escalas:exportar_escala', '04-10-2025'),
        ('escalas:puxar_dados', '04-10-2025'),
    ]
    
    for url_name, data_br in urls_teste:
        try:
            url = reverse(url_name, args=[data_br])
            print(f"📍 Testando: {url}")
            
            response = client.get(url)
            
            if response.status_code == 200:
                print(f"   ✅ Status 200 - Funcionando!")
            elif response.status_code == 302:
                print(f"   ↩️  Status 302 - Redirecionamento (provavelmente para login)")
            elif response.status_code == 404:
                print(f"   ⚠️  Status 404 - Escala não encontrada (normal se não há dados)")
            else:
                print(f"   ❓ Status {response.status_code} - Resposta inesperada")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    print(f"\n📊 Teste de filtro date_br:")
    
    # Testar filtro date_br
    from datetime import date
    from core.templatetags.custom_filters import date_br
    
    test_date = date(2025, 10, 4)
    formatted = date_br(test_date)
    print(f"   Data: {test_date} → Formato BR: {formatted}")
    
    if formatted == "04-10-2025":
        print("   ✅ Filtro date_br funcionando corretamente!")
    else:
        print("   ❌ Filtro date_br com problema")
    
    print(f"\n🔍 Teste de parse_data_brasileira:")
    
    # Testar parse_data_brasileira
    from escalas.views import parse_data_brasileira
    
    test_strings = ['04-10-2025', '2025-10-04', '04/10/2025']
    
    for date_str in test_strings:
        try:
            parsed = parse_data_brasileira(date_str)
            print(f"   '{date_str}' → {parsed}")
            if parsed and parsed.year == 2025 and parsed.month == 10 and parsed.day == 4:
                print(f"     ✅ Parse correto!")
            else:
                print(f"     ❌ Parse incorreto!")
        except Exception as e:
            print(f"     ❌ Erro no parse: {e}")

if __name__ == "__main__":
    test_brazilian_format()