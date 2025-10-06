#!/usr/bin/env python3
"""
Script para testar completamente o sistema de agrupamento conforme especificações
"""
import os
import sys
import django
from datetime import time

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from escalas.models import Escala, AlocacaoVan
from escalas.views import VisualizarEscalaView

class ServicoTeste:
    """Classe mock para simular serviços"""
    def __init__(self, servico, horario, pax, numero_venda, local_pickup=""):
        self.servico = servico
        self.horario = horario
        self.pax = pax
        self.numero_venda = numero_venda
        self.local_pickup = local_pickup

def testar_criterios_agrupamento():
    """Testa todos os critérios de agrupamento especificados"""
    print("="*70)
    print("🔍 TESTE COMPLETO DO SISTEMA DE AGRUPAMENTO")
    print("="*70)
    
    view = VisualizarEscalaView()
    todos_testes_passaram = True
    
    # 🔹 TESTE 1: Serviços com mesmo nome e ≤ 40 minutos
    print("\n🔹 TESTE 1: Serviços com mesmo nome e ≤ 40 minutos")
    print("-" * 50)
    
    servico1 = ServicoTeste("TOUR REGULAR RIO", time(8, 0), 2, "Venda001")
    servico2 = ServicoTeste("TOUR REGULAR RIO", time(8, 20), 3, "Venda002")  # 20 min diff
    servico3 = ServicoTeste("TOUR REGULAR RIO", time(9, 30), 2, "Venda003")  # 90 min diff
    
    resultado1 = view._servicos_sao_compativeis(servico1, servico2)
    resultado2 = view._servicos_sao_compativeis(servico1, servico3)
    
    print(f"   Teste 1.1 - Mesmo nome, 20 min diferença: {'✅ PASSOU' if resultado1 else '❌ FALHOU'}")
    print(f"   Teste 1.2 - Mesmo nome, 90 min diferença: {'✅ PASSOU' if not resultado2 else '❌ FALHOU'}")
    
    if not resultado1 or resultado2:
        todos_testes_passaram = False
    
    # 🔹 TESTE 2: Transfers OUT regulares com mesmo pickup e PAX ≥ 4
    print("\n🔹 TESTE 2: Transfers OUT regulares com mesmo pickup e PAX ≥ 4")
    print("-" * 50)
    
    transfer1 = ServicoTeste("TRANSFER OUT REGULAR", time(9, 0), 1, "Venda003", "Hotel X")
    transfer2 = ServicoTeste("TRANSFER OUT REGULAR", time(9, 25), 3, "Venda004", "Hotel X")  # Total PAX = 4
    transfer3 = ServicoTeste("TRANSFER OUT REGULAR", time(9, 30), 1, "Venda005", "Hotel Y")  # Local diferente
    transfer4 = ServicoTeste("TRANSFER OUT REGULAR", time(9, 40), 2, "Venda006", "Hotel X")  # PAX insuficiente com transfer1
    
    resultado3 = view._servicos_sao_compativeis(transfer1, transfer2)
    resultado4 = view._servicos_sao_compativeis(transfer1, transfer3)
    resultado5 = view._servicos_sao_compativeis(transfer1, transfer4)
    
    print(f"   Teste 2.1 - Mesmo pickup, PAX total = 4: {'✅ PASSOU' if resultado3 else '❌ FALHOU'}")
    print(f"   Teste 2.2 - Pickup diferente: {'✅ PASSOU' if not resultado4 else '❌ FALHOU'}")
    print(f"   Teste 2.3 - Mesmo pickup, PAX total = 3: {'✅ PASSOU' if not resultado5 else '❌ FALHOU'}")
    
    if not resultado3 or resultado4 or resultado5:
        todos_testes_passaram = False
    
    # 🔹 TESTE 3: Tours com nomes similares
    print("\n🔹 TESTE 3: Tours com nomes similares")
    print("-" * 50)
    
    tour1 = ServicoTeste("TOUR PRIVATIVO", time(10, 0), 2, "Venda007")
    tour2 = ServicoTeste("TOUR REGULAR", time(10, 30), 4, "Venda008")
    tour3 = ServicoTeste("VEÍCULO + GUIA À DISPOSIÇÃO 06 HORAS", time(10, 35), 3, "Venda009")
    tour4 = ServicoTeste("GUIA À DISPOSIÇÃO 08 HORAS", time(10, 25), 2, "Venda010")
    tour5 = ServicoTeste("GUIA À DISPOSIÇÃO 10 HORAS", time(10, 15), 3, "Venda011")
    
    resultado6 = view._servicos_sao_compativeis(tour1, tour2)  # Tours
    resultado7 = view._servicos_sao_compativeis(tour1, tour3)  # Tour + Veículo + Guia
    resultado8 = view._servicos_sao_compativeis(tour4, tour5)  # Guia à disposição (diferentes horas)
    
    print(f"   Teste 3.1 - TOUR PRIVATIVO + TOUR REGULAR: {'✅ PASSOU' if resultado6 else '❌ FALHOU'}")
    print(f"   Teste 3.2 - TOUR + VEÍCULO + GUIA: {'✅ PASSOU' if resultado7 else '❌ FALHOU'}")
    print(f"   Teste 3.3 - GUIA À DISPOSIÇÃO (8h + 10h): {'✅ PASSOU' if resultado8 else '❌ FALHOU'}")
    
    if not resultado6 or not resultado7 or not resultado8:
        todos_testes_passaram = False
    
    # 🔹 TESTE 4: Casos que NÃO devem ser agrupados
    print("\n🔹 TESTE 4: Casos que NÃO devem ser agrupados")
    print("-" * 50)
    
    servico_diff1 = ServicoTeste("TRANSFER IN REGULAR", time(11, 0), 2, "Venda012")
    servico_diff2 = ServicoTeste("TRANSFER OUT REGULAR", time(11, 10), 3, "Venda013")
    
    resultado9 = view._servicos_sao_compativeis(servico_diff1, servico_diff2)
    
    print(f"   Teste 4.1 - TRANSFER IN + TRANSFER OUT: {'✅ PASSOU' if not resultado9 else '❌ FALHOU'}")
    
    if resultado9:
        todos_testes_passaram = False
    
    return todos_testes_passaram

def testar_funcoes_auxiliares():
    """Testa as funções auxiliares de verificação"""
    print("\n🔧 TESTE DAS FUNÇÕES AUXILIARES")
    print("-" * 50)
    
    view = VisualizarEscalaView()
    
    # Teste das funções de identificação
    testes = [
        ("_eh_transfer_out", "TRANSFER OUT REGULAR", True),
        ("_eh_transfer_out", "TRANSFER IN REGULAR", False),
        ("_eh_tour", "TOUR PRIVATIVO RIO", True),
        ("_eh_tour", "VEÍCULO + GUIA À DISPOSIÇÃO 6 HORAS", True),
        ("_eh_tour", "TRANSFER OUT REGULAR", False),
        ("_eh_guia_disposicao", "GUIA À DISPOSIÇÃO 08 HORAS", True),
        ("_eh_guia_disposicao", "GUIA À DISPOSIÇÃO 10 HORAS", True),
        ("_eh_guia_disposicao", "TOUR PRIVATIVO", False),
    ]
    
    funcoes_ok = True
    for funcao_nome, texto_teste, esperado in testes:
        funcao = getattr(view, funcao_nome)
        resultado = funcao(texto_teste)
        status = "✅" if resultado == esperado else "❌"
        print(f"   {funcao_nome}('{texto_teste}'): {status} {resultado} (esperado: {esperado})")
        if resultado != esperado:
            funcoes_ok = False
    
    return funcoes_ok

def testar_diferenca_horarios():
    """Testa o cálculo de diferença de horários"""
    print("\n⏰ TESTE DE DIFERENÇA DE HORÁRIOS")
    print("-" * 50)
    
    view = VisualizarEscalaView()
    
    testes_horario = [
        (time(8, 0), time(8, 20), 20),    # 20 minutos
        (time(8, 0), time(8, 40), 40),    # 40 minutos
        (time(8, 0), time(9, 30), 90),    # 90 minutos
        (time(10, 30), time(10, 0), 30),  # Ordem invertida
    ]
    
    horarios_ok = True
    for h1, h2, esperado in testes_horario:
        resultado = view._diferenca_horario_minutos(h1, h2)
        status = "✅" if abs(resultado - esperado) < 1 else "❌"
        print(f"   {h1} ↔ {h2}: {status} {resultado:.0f} min (esperado: {esperado})")
        if abs(resultado - esperado) >= 1:
            horarios_ok = False
    
    return horarios_ok

def verificar_implementacao_principal():
    """Verifica se as funções principais existem"""
    print("\n🏗️  VERIFICAÇÃO DA IMPLEMENTAÇÃO")
    print("-" * 50)
    
    view = VisualizarEscalaView()
    
    funcoes_necessarias = [
        '_servicos_sao_compativeis',
        '_normalizar_nome_servico', 
        '_diferenca_horario_minutos',
        '_eh_transfer_out',
        '_eh_tour',
        '_eh_guia_disposicao'
    ]
    
    implementacao_ok = True
    for funcao in funcoes_necessarias:
        if hasattr(view, funcao):
            print(f"   ✅ {funcao} implementada")
        else:
            print(f"   ❌ {funcao} NÃO encontrada")
            implementacao_ok = False
    
    return implementacao_ok

def main():
    """Função principal do teste"""
    print("🚀 INICIANDO VERIFICAÇÃO COMPLETA DO SISTEMA DE AGRUPAMENTO")
    
    todos_ok = True
    
    # 1. Verificar se as funções existem
    if not verificar_implementacao_principal():
        print("\n❌ ERRO: Funções principais não encontradas!")
        todos_ok = False
    
    # 2. Testar funções auxiliares
    if not testar_funcoes_auxiliares():
        print("\n❌ ERRO: Problemas nas funções auxiliares!")
        todos_ok = False
    
    # 3. Testar cálculo de horários
    if not testar_diferenca_horarios():
        print("\n❌ ERRO: Problemas no cálculo de horários!")
        todos_ok = False
    
    # 4. Testar critérios de agrupamento
    if not testar_criterios_agrupamento():
        print("\n❌ ERRO: Critérios de agrupamento não funcionam corretamente!")
        todos_ok = False
    
    # Resultado final
    print("\n" + "="*70)
    if todos_ok:
        print("🎉 SISTEMA DE AGRUPAMENTO ESTÁ FUNCIONANDO CORRETAMENTE!")
        print("✅ Todos os critérios especificados estão implementados e funcionando")
    else:
        print("⚠️  SISTEMA DE AGRUPAMENTO TEM PROBLEMAS!")
        print("❌ Alguns critérios não estão funcionando conforme especificado")
    print("="*70)
    
    return todos_ok

if __name__ == "__main__":
    main()