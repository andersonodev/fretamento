#!/usr/bin/env python
"""
Script para testar o comportamento específico do botão Agrupar
Simula exatamente o que acontece quando clicamos no botão no navegador
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from escalas.models import Escala, AlocacaoVan, GrupoServico

def test_button_behavior():
    """Testa o comportamento específico do botão agrupar"""
    print("=== TESTE ESPECÍFICO BOTÃO AGRUPAR ===\n")
    
    # Configurar cliente de teste
    client = Client()
    
    # Fazer login com usuário admin existente
    login_success = client.login(username='admin', password='admin123')
    print(f"✓ Login realizado: {'Sucesso' if login_success else 'Falhou'}")
    
    if not login_success:
        print("❌ Falha no login. Tentando com testuser...")
        login_success = client.login(username='testuser', password='testpass123')
        print(f"✓ Login testuser: {'Sucesso' if login_success else 'Falhou'}")
        
        if not login_success:
            print("❌ Não foi possível fazer login")
            return
    
    # Encontrar uma escala para teste
    escalas = Escala.objects.all()
    if not escalas.exists():
        print("❌ Nenhuma escala encontrada")
        return
    
    escala = escalas.first()
    data_str = escala.data.strftime('%d-%m-%Y')
    url = f'/escalas/visualizar/{data_str}/'
    
    print(f"✓ Testando escala: {data_str}")
    print(f"✓ URL: {url}")
    
    # Verificar dados antes do agrupamento
    alocacoes_antes = AlocacaoVan.objects.filter(escala=escala).count()
    grupos_antes = GrupoServico.objects.filter(escala=escala).count()
    alocacoes_sem_grupo_antes = AlocacaoVan.objects.filter(escala=escala, grupo_info__isnull=True).count()
    
    print(f"\n--- ESTADO ANTES DO AGRUPAMENTO ---")
    print(f"Total de alocações: {alocacoes_antes}")
    print(f"Total de grupos: {grupos_antes}")
    print(f"Alocações sem grupo: {alocacoes_sem_grupo_antes}")
    
    # Primeiro, fazer GET para carregar a página
    print(f"\n--- TESTE GET ---")
    get_response = client.get(url)
    print(f"Status GET: {get_response.status_code}")
    
    if get_response.status_code != 200:
        print(f"❌ GET falhou: {get_response.status_code}")
        return
    
    # Agora fazer POST com acao=agrupar (simula clique no botão)
    print(f"\n--- TESTE POST AGRUPAR ---")
    
    # Dados exatamente como enviados pelo formulário HTML
    post_data = {
        'acao': 'agrupar',
        'csrfmiddlewaretoken': client.session.get('csrftoken', 'test-token')
    }
    
    print(f"Dados POST: {post_data}")
    
    response = client.post(url, data=post_data, follow=True)
    print(f"Status final: {response.status_code}")
    print(f"URL final: {response.request['PATH_INFO']}")
    
    # Verificar dados após o agrupamento
    alocacoes_depois = AlocacaoVan.objects.filter(escala=escala).count()
    grupos_depois = GrupoServico.objects.filter(escala=escala).count()
    alocacoes_sem_grupo_depois = AlocacaoVan.objects.filter(escala=escala, grupo_info__isnull=True).count()
    
    print(f"\n--- ESTADO DEPOIS DO AGRUPAMENTO ---")
    print(f"Total de alocações: {alocacoes_depois}")
    print(f"Total de grupos: {grupos_depois}")
    print(f"Alocações sem grupo: {alocacoes_sem_grupo_depois}")
    
    # Verificar se houve mudança
    novos_grupos = grupos_depois - grupos_antes
    agrupamentos_feitos = alocacoes_sem_grupo_antes - alocacoes_sem_grupo_depois
    
    print(f"\n--- RESULTADO ---")
    print(f"Novos grupos criados: {novos_grupos}")
    print(f"Serviços agrupados: {agrupamentos_feitos}")
    
    if novos_grupos > 0:
        print(f"✅ AGRUPAMENTO FUNCIONOU! {novos_grupos} grupos criados")
    elif alocacoes_sem_grupo_antes == 0:
        print(f"ℹ️  Todos os serviços já estavam agrupados")
    else:
        print(f"❌ AGRUPAMENTO NÃO FUNCIONOU! Nenhum grupo foi criado")
    
    # Verificar mensagens Django
    messages = list(response.context['messages']) if response.context and 'messages' in response.context else []
    if messages:
        print(f"\n--- MENSAGENS DJANGO ---")
        for msg in messages:
            print(f"{msg.tags.upper()}: {msg}")
    
    print("\n=== TESTE CONCLUÍDO ===")

if __name__ == '__main__':
    test_button_behavior()