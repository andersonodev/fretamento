#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from django.urls import reverse
from django.test import Client
from datetime import date

def test_urls():
    client = Client()
    
    print("Testando URLs de escalas...")
    
    # Testar URL brasileira
    try:
        url_br = reverse('escalas:exportar_escala_br', args=['04-10-2025'])
        print(f"URL brasileira: {url_br}")
        
        response = client.get(url_br)
        print(f"Status da resposta brasileira: {response.status_code}")
        
        if response.status_code == 500:
            print("Erro 500 detectado!")
            
    except Exception as e:
        print(f"Erro ao testar URL brasileira: {e}")
    
    # Testar URL ISO
    try:
        url_iso = reverse('escalas:exportar_escala', args=['2025-10-04'])
        print(f"URL ISO: {url_iso}")
        
        response = client.get(url_iso)
        print(f"Status da resposta ISO: {response.status_code}")
        
    except Exception as e:
        print(f"Erro ao testar URL ISO: {e}")

if __name__ == "__main__":
    test_urls()