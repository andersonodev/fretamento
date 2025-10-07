#!/usr/bin/env python

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Configuração do Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

def test_agrupamento():
    """Testa o agrupamento via HTTP POST simulado"""
    
    # Criar cliente de teste
    client = Client()
    
    # Fazer login (assumindo que existe um usuário)
    User = get_user_model()
    try:
        user = User.objects.first()
        if not user:
            print("❌ Nenhum usuário encontrado!")
            return
        
        # Login
        client.force_login(user)
        print(f"✅ Login feito como: {user.username}")
        
        # Testar POST de agrupamento
        url = '/escalas/visualizar/07-10-2025/'
        data = {'acao': 'agrupar'}
        
        print(f"🔄 Enviando POST para: {url}")
        print(f"📋 Dados: {data}")
        
        response = client.post(url, data)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"🔄 Redirect: {response.url if hasattr(response, 'url') else 'N/A'}")
        
        # Verificar mensagens
        if hasattr(response, 'context') and response.context:
            from django.contrib.messages import get_messages
            messages = list(get_messages(response.wsgi_request))
            if messages:
                print("💬 Mensagens:")
                for msg in messages:
                    print(f"   {msg.level_tag}: {msg}")
            else:
                print("💬 Nenhuma mensagem")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agrupamento()