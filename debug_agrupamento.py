#!/usr/bin/env python3
"""
Script detalhado para analisar por que o agrupamento não está funcionando
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from escalas.models import Escala, AlocacaoVan
from escalas.views import VisualizarEscalaView
from datetime import date

def analisar_compatibilidade():
    """Analisa detalhadamente a compatibilidade dos serviços"""
    print("=== ANÁLISE DE COMPATIBILIDADE ===")
    
    # Buscar uma escala com dados
    escala = Escala.objects.filter(etapa='DADOS_PUXADOS').order_by('-data').first()
    if not escala:
        print("❌ Nenhuma escala encontrada")
        return
    
    print(f"📅 Analisando escala: {escala.data}")
    
    # Buscar alocações sem grupo
    alocacoes = escala.alocacoes.filter(grupo_info__isnull=True)[:10]  # Limitando a 10 para análise
    
    print(f"📊 Analisando {alocacoes.count()} alocações...")
    
    view = VisualizarEscalaView()
    
    for i, alocacao1 in enumerate(alocacoes):
        print(f"\n--- Alocação {i+1} ---")
        print(f"Cliente: {alocacao1.servico.cliente}")
        print(f"Serviço: {alocacao1.servico.servico}")
        print(f"Horário: {alocacao1.servico.horario}")
        print(f"PAX: {alocacao1.servico.pax}")
        print(f"Local Pickup: {alocacao1.servico.local_pickup}")
        
        # Verificar compatibilidade com outras alocações
        compatíveis = []
        for alocacao2 in alocacoes:
            if alocacao1.id != alocacao2.id:
                if view._servicos_sao_compativeis(alocacao1.servico, alocacao2.servico):
                    compatíveis.append(alocacao2)
        
        if compatíveis:
            print(f"✅ Compatível com {len(compatíveis)} serviços:")
            for comp in compatíveis:
                print(f"   - {comp.servico.cliente}: {comp.servico.servico}")
        else:
            print("❌ Não há serviços compatíveis")
            
            # Analisar por que não é compatível
            print("🔍 Testando critérios específicos:")
            
            for alocacao2 in alocacoes[:5]:  # Teste com primeiros 5
                if alocacao1.id != alocacao2.id:
                    print(f"\n   vs {alocacao2.servico.cliente}:")
                    
                    # Critério 1: Mesmo serviço
                    nome1 = view._normalizar_nome_servico(alocacao1.servico.servico)
                    nome2 = view._normalizar_nome_servico(alocacao2.servico.servico)
                    if nome1 == nome2:
                        print(f"     ✅ Mesmo serviço: {nome1}")
                        diff_min = view._diferenca_horario_minutos(alocacao1.servico.horario, alocacao2.servico.horario)
                        print(f"     ⏰ Diferença horário: {diff_min:.1f} min (limite: 35)")
                        if diff_min <= 35:
                            print("     ✅ Dentro do limite de horário")
                        else:
                            print("     ❌ Fora do limite de horário")
                    else:
                        print(f"     ❌ Serviços diferentes: '{nome1}' vs '{nome2}'")
                    
                    # Critério 2: Transfer OUT
                    is_transfer1 = view._eh_transfer_out(alocacao1.servico.servico)
                    is_transfer2 = view._eh_transfer_out(alocacao2.servico.servico)
                    if is_transfer1 and is_transfer2:
                        print(f"     ✅ Ambos são transfers OUT")
                        pickup1 = alocacao1.servico.local_pickup or ''
                        pickup2 = alocacao2.servico.local_pickup or ''
                        if pickup1 == pickup2:
                            print(f"     ✅ Mesmo pickup: {pickup1}")
                            total_pax = alocacao1.servico.pax + alocacao2.servico.pax
                            print(f"     👥 Total PAX: {total_pax} (mínimo: 4)")
                            if total_pax >= 4:
                                print("     ✅ PAX suficiente")
                            else:
                                print("     ❌ PAX insuficiente")
                        else:
                            print(f"     ❌ Pickups diferentes: '{pickup1}' vs '{pickup2}'")
                    elif is_transfer1 or is_transfer2:
                        print(f"     ⚠️  Apenas um é transfer OUT")
                    
                    # Critério 3: Tours
                    is_tour1 = view._eh_tour(alocacao1.servico.servico)
                    is_tour2 = view._eh_tour(alocacao2.servico.servico)
                    if is_tour1 and is_tour2:
                        print(f"     ✅ Ambos são tours")
                        diff_min = view._diferenca_horario_minutos(alocacao1.servico.horario, alocacao2.servico.horario)
                        print(f"     ⏰ Diferença horário: {diff_min:.1f} min (limite: 35)")
                    elif is_tour1 or is_tour2:
                        print(f"     ⚠️  Apenas um é tour")
                    
                    break  # Analisar apenas o primeiro para não sobrecarregar

def verificar_servicos_por_tipo():
    """Verifica tipos de serviços disponíveis"""
    print("\n=== ANÁLISE DE TIPOS DE SERVIÇOS ===")
    
    escala = Escala.objects.filter(etapa='DADOS_PUXADOS').order_by('-data').first()
    if not escala:
        return
    
    alocacoes = escala.alocacoes.filter(grupo_info__isnull=True)
    
    # Agrupar por tipo de serviço
    servicos_por_nome = {}
    for alocacao in alocacoes:
        nome = alocacao.servico.servico
        if nome not in servicos_por_nome:
            servicos_por_nome[nome] = []
        servicos_por_nome[nome].append(alocacao)
    
    print(f"📊 Tipos de serviços encontrados:")
    for nome, lista in servicos_por_nome.items():
        print(f"  '{nome}': {len(lista)} ocorrências")
        if len(lista) > 1:
            print(f"    🔄 Potencial para agrupamento!")
            for alocacao in lista:
                print(f"      - {alocacao.servico.cliente} às {alocacao.servico.horario}")

def main():
    """Função principal"""
    print("🔍 ANÁLISE DETALHADA DO AGRUPAMENTO\n")
    
    verificar_servicos_por_tipo()
    analisar_compatibilidade()

if __name__ == "__main__":
    main()