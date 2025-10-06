#!/usr/bin/env python
"""
Script para precificar uma escala e testar a formatação
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

def precificar_escala():
    """Precifica uma escala para testar a formatação"""
    
    try:
        escala = Escala.objects.get(data=date(2025, 10, 2))
        print(f"✅ Escala encontrada: {escala}")
        
        # Precificar as primeiras 10 alocações para teste
        alocacoes = escala.alocacoes.all()[:10]
        
        print(f"\n💰 Precificando {len(alocacoes)} alocações...")
        
        for i, alocacao in enumerate(alocacoes):
            # Simular preços baseados no PAX
            pax = alocacao.servico.pax
            if pax <= 3:
                preco = 200.0
                veiculo = "Executivo"
            elif pax <= 11:
                preco = 300.0
                veiculo = "Van 15 lugares"
            else:
                preco = 500.0
                veiculo = "Micro"
            
            alocacao.preco_calculado = preco
            alocacao.veiculo_recomendado = veiculo
            alocacao.lucratividade = preco / max(pax, 1)
            alocacao.save()
            
            print(f"   {i+1}. ID:{alocacao.id} | PAX: {pax} | Preço: R$ {preco} | Veículo: {veiculo}")
        
        # Verificar totais após precificação
        escala.refresh_from_db()
        total_valor = escala.total_van1_valor + escala.total_van2_valor
        alocacoes_com_preco = escala.alocacoes.filter(preco_calculado__isnull=False).count()
        
        print(f"\n📊 Resultado da precificação:")
        print(f"   Alocações com preço: {alocacoes_com_preco}")
        print(f"   Valor total VAN1: R$ {escala.total_van1_valor}")
        print(f"   Valor total VAN2: R$ {escala.total_van2_valor}")
        print(f"   Valor total geral: R$ {total_valor}")
        
        return escala
        
    except Escala.DoesNotExist:
        print("❌ Escala não encontrada")
        return None

def testar_formatacao_completa():
    """Testa o ciclo completo: precificar → formatar → verificar"""
    
    print("🔄 Teste completo de formatação de escala\n")
    
    # 1. Precificar escala
    escala = precificar_escala()
    if not escala:
        return
    
    input("\n⏸️  Pressione Enter para continuar com a formatação...")
    
    # 2. Simular formatação
    print(f"\n🧹 Formatando escala...")
    
    # Desfazer grupos (se existirem)
    grupos_removidos = escala.grupos.count()
    escala.grupos.all().delete()
    
    # Desprecificar alocações
    alocacoes_desprecificadas = 0
    for alocacao in escala.alocacoes.all():
        if alocacao.preco_calculado is not None:
            alocacao.preco_calculado = None
            alocacao.veiculo_recomendado = None
            alocacao.lucratividade = None
            alocacao.detalhes_precificacao = None
            alocacao.save()
            alocacoes_desprecificadas += 1
    
    # Resetar etapa
    escala.etapa = 'DADOS_PUXADOS'
    escala.save()
    escala.refresh_from_db()
    
    # 3. Verificar resultado
    print(f"\n✅ Resultado da formatação:")
    print(f"   Grupos removidos: {grupos_removidos}")
    print(f"   Alocações desprecificadas: {alocacoes_desprecificadas}")
    print(f"   Etapa: {escala.etapa}")
    
    # Verificar novos totais
    total_valor = escala.total_van1_valor + escala.total_van2_valor
    alocacoes_com_preco = escala.alocacoes.filter(preco_calculado__isnull=False).count()
    
    print(f"   Alocações com preço: {alocacoes_com_preco}")
    print(f"   Valor total VAN1: R$ {escala.total_van1_valor}")
    print(f"   Valor total VAN2: R$ {escala.total_van2_valor}")
    print(f"   Valor total geral: R$ {total_valor}")
    
    if total_valor == 0 and alocacoes_com_preco == 0:
        print("\n🎉 SUCESSO! A formatação funcionou corretamente!")
    else:
        print(f"\n❌ ERRO! Ainda há valores ou preços não zerados.")

if __name__ == "__main__":
    testar_formatacao_completa()