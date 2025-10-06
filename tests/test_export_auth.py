#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from django.test import Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
import io
import sys

def test_export_with_auth():
    client = Client()
    
    # Criar usuário de teste
    user = User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@test.com'
    )
    
    # Fazer login
    client.login(username='testuser', password='testpass123')
    
    print("Usuário logado, testando exportação...")
    
    # Testar URL brasileira
    try:
        url_br = reverse('escalas:exportar_escala_br', args=['04-10-2025'])
        print(f"Testando URL brasileira: {url_br}")
        
        # Capturar saída de erro para detectar problemas
        old_stderr = sys.stderr
        sys.stderr = mystderr = io.StringIO()
        
        response = client.get(url_br)
        
        # Restaurar stderr
        sys.stderr = old_stderr
        error_output = mystderr.getvalue()
        
        print(f"Status: {response.status_code}")
        if error_output:
            print(f"Erros capturados:\n{error_output}")
        
        if response.status_code == 200:
            print("✅ Exportação brasileira funcionou!")
            print(f"Content-Type: {response.get('Content-Type', 'N/A')}")
        elif response.status_code == 404:
            print("❌ Erro 404 - Data não encontrada ou sem dados")
        elif response.status_code == 500:
            print("❌ Erro 500 - Erro interno do servidor")
        else:
            print(f"⚠️  Status inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exceção ao testar URL brasileira: {e}")
    
    # Testar URL ISO para comparação
    try:
        url_iso = reverse('escalas:exportar_escala', args=['2025-10-04'])
        print(f"\nTestando URL ISO: {url_iso}")
        
        # Capturar saída de erro
        old_stderr = sys.stderr
        sys.stderr = mystderr = io.StringIO()
        
        response = client.get(url_iso)
        
        # Restaurar stderr
        sys.stderr = old_stderr
        error_output = mystderr.getvalue()
        
        print(f"Status: {response.status_code}")
        if error_output:
            print(f"Erros capturados:\n{error_output}")
        
        if response.status_code == 200:
            print("✅ Exportação ISO funcionou!")
            print(f"Content-Type: {response.get('Content-Type', 'N/A')}")
        elif response.status_code == 404:
            print("❌ Erro 404 - Data não encontrada ou sem dados")
        elif response.status_code == 500:
            print("❌ Erro 500 - Erro interno do servidor")
        else:
            print(f"⚠️  Status inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exceção ao testar URL ISO: {e}")

if __name__ == "__main__":
    test_export_with_auth()