#!/usr/bin/env python
"""
Script de teste para verificar se a formatação de escala está funcionando corretamente
"""

import os
import sys
import django
from datetime import date

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from escalas.models import Escala, AlocacaoVan
from core.models import Servico

def testar_formatacao():
    """Testa se a formatação está zerando os preços corretamente"""
    
    print("🔍 Testando formatação de escala...")
    
    # Buscar uma escala de teste (02/10/2025 da imagem)
    try:
        escala = Escala.objects.get(data=date(2025, 10, 2))
        print(f"✅ Escala encontrada: {escala}")
        print(f"   Etapa: {escala.etapa}")
        print(f"   Status: {escala.status}")
        
        # Verificar alocações
        alocacoes = escala.alocacoes.all()
        print(f"   Total de alocações: {alocacoes.count()}")
        
        # Verificar preços antes
        alocacoes_com_preco = alocacoes.filter(preco_calculado__isnull=False)
        print(f"   Alocações com preço: {alocacoes_com_preco.count()}")
        
        total_valor_van1 = escala.total_van1_valor
        total_valor_van2 = escala.total_van2_valor
        print(f"   Valor total VAN1: R$ {total_valor_van1}")
        print(f"   Valor total VAN2: R$ {total_valor_van2}")
        print(f"   Valor total geral: R$ {total_valor_van1 + total_valor_van2}")
        
        # Verificar grupos
        grupos = escala.grupos.all()
        print(f"   Total de grupos: {grupos.count()}")
        
        # Mostrar detalhes das primeiras 3 alocações
        print("\n📋 Primeiras 3 alocações:")
        for i, alocacao in enumerate(alocacoes[:3]):
            print(f"   {i+1}. ID:{alocacao.id} | Cliente: {alocacao.servico.cliente[:30]}... | "
                  f"Preço: R$ {alocacao.preco_calculado or 0} | Van: {alocacao.van}")
        
        return escala
        
    except Escala.DoesNotExist:
        print("❌ Escala de 02/10/2025 não encontrada")
        
        # Listar escalas disponíveis
        escalas = Escala.objects.all().order_by('-data')[:5]
        print(f"\n📅 Escalas disponíveis (últimas 5):")
        for escala in escalas:
            alocacoes_count = escala.alocacoes.count()
            precos_count = escala.alocacoes.filter(preco_calculado__isnull=False).count()
            print(f"   {escala.data} - {escala.etapa} - {alocacoes_count} alocações - {precos_count} com preço")
        
        return None

def verificar_formatacao_teste():
    """Faz uma formatação de teste em uma escala"""
    escala = testar_formatacao()
    
    if not escala:
        return
    
    print(f"\n🧪 Simulando formatação...")
    
    # 1. Verificar grupos antes
    grupos_antes = escala.grupos.count()
    
    # 2. Verificar preços antes
    alocacoes_com_preco_antes = escala.alocacoes.filter(preco_calculado__isnull=False).count()
    
    # 3. Simular desprecificação
    print(f"\n⚙️ Desprecificando alocações...")
    alocacoes_desprecificadas = 0
    for alocacao in escala.alocacoes.all():
        if alocacao.preco_calculado is not None:
            print(f"   Removendo preço de alocação {alocacao.id}: R$ {alocacao.preco_calculado}")
            alocacao.preco_calculado = None
            alocacao.veiculo_recomendado = None
            alocacao.lucratividade = None
            alocacao.detalhes_precificacao = None
            alocacao.save()
            alocacoes_desprecificadas += 1
    
    # 4. Verificar resultado
    print(f"\n✅ Resultado da formatação:")
    print(f"   Grupos removidos: {grupos_antes} → {escala.grupos.count()}")
    print(f"   Alocações desprecificadas: {alocacoes_desprecificadas}")
    print(f"   Preços zerados: {alocacoes_com_preco_antes} → {escala.alocacoes.filter(preco_calculado__isnull=False).count()}")
    
    # Verificar novos totais
    escala.refresh_from_db()
    total_valor_van1 = escala.total_van1_valor
    total_valor_van2 = escala.total_van2_valor
    print(f"   Novo valor VAN1: R$ {total_valor_van1}")
    print(f"   Novo valor VAN2: R$ {total_valor_van2}")
    print(f"   Novo valor total: R$ {total_valor_van1 + total_valor_van2}")

if __name__ == "__main__":
    verificar_formatacao_teste()