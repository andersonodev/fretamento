#!/usr/bin/env python
import os
import django
import requests

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from django.test import Client
from django.middleware.csrf import get_token
from django.contrib.auth.models import User
from core.models import ProcessamentoPlanilha

def testar_delecao():
    # Verificar arquivos disponíveis
    arquivo = ProcessamentoPlanilha.objects.first()
    if not arquivo:
        print("❌ Nenhum arquivo encontrado para teste")
        return
    
    print(f"📁 Testando deleção do arquivo: {arquivo.nome_arquivo} (ID: {arquivo.id})")
    
    # Criar cliente de teste
    client = Client()
    
    # Simular requisição GET para obter token CSRF
    response = client.get('/core/arquivos/')
    print(f"✅ GET /core/arquivos/ - Status: {response.status_code}")
    
    # Obter token CSRF do contexto
    csrf_token = None
    if hasattr(response, 'context') and response.context and 'csrf_token' in response.context:
        csrf_token = response.context['csrf_token']
    
    if not csrf_token:
        # Tentar obter de outra forma
        csrf_token = get_token(None)
    
    print(f"🔒 Token CSRF obtido: {str(csrf_token)[:10]}...")
    
    # Dados da requisição
    data = {
        'csrfmiddlewaretoken': csrf_token
    }
    
    # Fazer requisição de deleção
    print(f"🗑️ Fazendo requisição POST para /core/arquivos/{arquivo.id}/deletar/")
    
    response = client.post(
        f'/core/arquivos/{arquivo.id}/deletar/',
        data=data,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    
    print(f"📊 Status da resposta: {response.status_code}")
    print(f"📄 Content-Type: {response.get('Content-Type', 'N/A')}")
    
    try:
        content = response.content.decode('utf-8')
        print(f"📝 Resposta (primeiros 500 chars): {content[:500]}")
        
        if response.status_code == 200:
            print("✅ Deleção bem-sucedida!")
            import json
            try:
                data = json.loads(content)
                print(f"🔍 Dados JSON: {data}")
            except:
                print("⚠️ Resposta não é JSON válido")
        else:
            print(f"❌ Erro na deleção: Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao processar resposta: {e}")

if __name__ == "__main__":
    testar_delecao()