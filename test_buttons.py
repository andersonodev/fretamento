#!/usr/bin/env python
"""
Script para testar os botões de Agrupar e Escalar diretamente no Django
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from django.urls import reverse
from escalas.models import Escala, AlocacaoVan, GrupoServico
from datetime import datetime

def test_buttons():
    """Testa os botões de agrupar e escalar"""
    print("=== TESTE DOS BOTÕES AGRUPAR E ESCALAR ===\n")
    
    # Configurar cliente de teste
    client = Client()
    
    # Obter ou criar usuário de teste
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@test.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✓ Usuário de teste criado: {user.username}")
    else:
        print(f"✓ Usuário de teste encontrado: {user.username}")
    
    # Fazer login
    login_success = client.login(username='testuser', password='testpass123')
    print(f"✓ Login realizado: {'Sucesso' if login_success else 'Falhou'}")
    
    # Verificar escalas disponíveis
    escalas = Escala.objects.all()
    print(f"✓ Escalas disponíveis: {escalas.count()}")
    
    if not escalas.exists():
        print("❌ Nenhuma escala encontrada para teste")
        return
    
    # Pegar a primeira escala para teste
    escala_teste = escalas.first()
    data_str = escala_teste.data.strftime('%d-%m-%Y')
    print(f"✓ Testando com escala: {data_str}")
    
    # URL da escala
    url = f'/escalas/visualizar/{data_str}/'
    print(f"✓ URL de teste: {url}")
    
    # Primeiro, fazer GET para obter a página
    print("\n--- TESTE GET ---")
    response = client.get(url)
    print(f"Status GET: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ GET falhou: {response.status_code}")
        print(f"Conteúdo: {response.content[:500]}")
        return
    
    # Testar POST com acao=agrupar
    print("\n--- TESTE POST AGRUPAR ---")
    post_data = {'acao': 'agrupar'}
    response_agrupar = client.post(url, data=post_data)
    print(f"Status POST Agrupar: {response_agrupar.status_code}")
    print(f"Tipo de resposta: {type(response_agrupar)}")
    
    if hasattr(response_agrupar, 'url'):
        print(f"Redirect para: {response_agrupar.url}")
    
    # Testar POST com acao=otimizar
    print("\n--- TESTE POST ESCALAR ---")
    post_data = {'acao': 'otimizar'}
    response_escalar = client.post(url, data=post_data)
    print(f"Status POST Escalar: {response_escalar.status_code}")
    print(f"Tipo de resposta: {type(response_escalar)}")
    
    if hasattr(response_escalar, 'url'):
        print(f"Redirect para: {response_escalar.url}")
    
    # Verificar logs de console
    print("\n--- VERIFICAÇÃO DE DADOS ---")
    alocacoes = AlocacaoVan.objects.filter(escala=escala_teste)
    grupos = GrupoServico.objects.filter(escala=escala_teste)
    print(f"Alocações na escala: {alocacoes.count()}")
    print(f"Grupos na escala: {grupos.count()}")
    
    print("\n=== TESTE CONCLUÍDO ===")

if __name__ == '__main__':
    test_buttons()