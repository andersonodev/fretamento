#!/usr/bin/env python
"""
Script de teste para validar o sistema de tarifários
Execute: python test_tarifarios.py
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.tarifarios import (
    calcular_preco_servico, calcular_veiculo_recomendado,
    buscar_preco_jw, buscar_preco_motoristas, 
    gerar_chave_tarifario, obter_estatisticas_tarifario
)
from core.models import Servico

def test_veiculo_recomendado():
    """Testa recomendação de veículos por PAX"""
    print("🚗 Testando recomendação de veículos...")
    
    testes = [
        (1, "Executivo"),
        (3, "Executivo"),
        (4, "Van 15 lugares"),
        (11, "Van 15 lugares"),
        (12, "Van 18 lugares"),
        (14, "Van 18 lugares"),
        (15, "Micro"),
        (26, "Micro"),
        (27, "Ônibus"),
        (50, "Ônibus"),
    ]
    
    for pax, esperado in testes:
        resultado = calcular_veiculo_recomendado(pax)
        status = "✅" if resultado == esperado else "❌"
        print(f"  {status} {pax} PAX -> {resultado} (esperado: {esperado})")

def test_busca_tarifario_jw():
    """Testa busca no tarifário JW"""
    print("\n💰 Testando busca no tarifário JW...")
    
    testes = [
        ("SDU / Zona Sul", "Executivo", 229.00),
        ("SDU / Zona Sul", "Van 15 lugares", 300.00),
        ("AIRJ / Zona Sul", "Micro", 961.00),
        ("Transfer Petrópolis", "Ônibus", 2669.00),
        ("Serviço Inexistente", "Executivo", 0.0),
    ]
    
    for servico, veiculo, esperado in testes:
        resultado = buscar_preco_jw(servico, veiculo)
        status = "✅" if resultado == esperado else "❌"
        print(f"  {status} {servico} ({veiculo}) -> R$ {resultado} (esperado: R$ {esperado})")

def test_busca_tarifario_motoristas():
    """Testa busca no tarifário de motoristas"""
    print("\n🚖 Testando busca no tarifário de motoristas...")
    
    testes = [
        ("Transfer In ou Out Sdu / Centro", 1, 40.00),
        ("Transfer In ou Out Sdu / Centro", 4, 40.00),
        ("Transfer In ou Out Sdu / Centro", 5, 80.00),  # 2 carros
        ("Transfer In ou Out Sdu / Centro", 8, 80.00),  # 2 carros
        ("Disposição 04h", 1, 170.00),
        ("Hora extra", 1, 46.00),
        ("Serviço Inexistente", 1, 0.0),
    ]
    
    for servico, pax, esperado in testes:
        resultado = buscar_preco_motoristas(servico, pax)
        status = "✅" if resultado == esperado else "❌"
        print(f"  {status} {servico} ({pax} PAX) -> R$ {resultado} (esperado: R$ {esperado})")

def test_gerar_chave_tarifario():
    """Testa geração de chaves para busca nos tarifários"""
    print("\n🔑 Testando geração de chaves de tarifário...")
    
    servicos_teste = [
        {
            'servico': 'Transfer SDU para Zona Sul',
            'tipo': 'TRANSFER',
            'aeroporto': 'SDU',
            'regiao': 'ZONA SUL',
            'esperado': 'SDU / Zona Sul'
        },
        {
            'servico': 'Transfer GIG para Barra',
            'tipo': 'TRANSFER',
            'aeroporto': 'GIG',
            'regiao': 'BARRA',
            'esperado': 'AIRJ / Barra + Recreio'
        },
        {
            'servico': 'Disposição 4h',
            'tipo': 'DISPOSICAO',
            'aeroporto': '',
            'regiao': '',
            'esperado': 'À disposição / Tour de 4 horas'
        },
        {
            'servico': 'Tour em Petrópolis',
            'tipo': 'TOUR',
            'aeroporto': '',
            'regiao': '',
            'esperado': 'Tour em Petrópolis'
        },
    ]
    
    for teste in servicos_teste:
        servico = Servico(
            servico=teste['servico'],
            tipo=teste['tipo'],
            aeroporto=teste['aeroporto'],
            regiao=teste['regiao'],
            pax=1,
            data_do_servico='2024-01-01',
            horario='10:00',
            cliente='Teste'
        )
        
        resultado = gerar_chave_tarifario(servico)
        status = "✅" if resultado == teste['esperado'] else "❌"
        print(f"  {status} {teste['servico']} -> '{resultado}' (esperado: '{teste['esperado']}')")

def test_calculo_preco_completo():
    """Testa cálculo completo de preço para serviços"""
    print("\n🧮 Testando cálculo completo de preços...")
    
    servicos_teste = [
        {
            'servico': 'Transfer SDU para Zona Sul',
            'tipo': 'TRANSFER',
            'aeroporto': 'SDU',
            'regiao': 'ZONA SUL',
            'pax': 2,
            'veiculo_esperado': 'Executivo',
            'preco_esperado': 229.00
        },
        {
            'servico': 'Transfer GIG para Zona Sul',
            'tipo': 'TRANSFER',
            'aeroporto': 'GIG',
            'regiao': 'ZONA SUL',
            'pax': 12,
            'veiculo_esperado': 'Van 18 lugares',
            'preco_esperado': 429.00
        },
        {
            'servico': 'Disposição 6h',
            'tipo': 'DISPOSICAO',
            'aeroporto': '',
            'regiao': '',
            'pax': 8,
            'veiculo_esperado': 'Van 15 lugares',
            'preco_esperado': 707.00
        },
    ]
    
    for teste in servicos_teste:
        servico = Servico(
            servico=teste['servico'],
            tipo=teste['tipo'],
            aeroporto=teste['aeroporto'],
            regiao=teste['regiao'],
            pax=teste['pax'],
            data_do_servico='2024-01-01',
            horario='10:00',
            cliente='Teste'
        )
        
        veiculo, preco = calcular_preco_servico(servico)
        
        veiculo_ok = veiculo == teste['veiculo_esperado']
        preco_ok = abs(preco - teste['preco_esperado']) < 0.01
        
        status_veiculo = "✅" if veiculo_ok else "❌"
        status_preco = "✅" if preco_ok else "❌"
        
        print(f"  {teste['servico']} ({teste['pax']} PAX)")
        print(f"    {status_veiculo} Veículo: {veiculo} (esperado: {teste['veiculo_esperado']})")
        print(f"    {status_preco} Preço: R$ {preco:.2f} (esperado: R$ {teste['preco_esperado']:.2f})")

def test_estatisticas():
    """Testa geração de estatísticas dos tarifários"""
    print("\n📊 Testando estatísticas dos tarifários...")
    
    stats = obter_estatisticas_tarifario()
    
    print(f"  📈 Total serviços JW: {stats['total_servicos_jw']}")
    print(f"  📈 Total serviços Motoristas: {stats['total_servicos_motoristas']}")
    print(f"  💰 Menor preço JW: R$ {stats['menor_preco_jw']:.2f}")
    print(f"  💰 Maior preço JW: R$ {stats['maior_preco_jw']:.2f}")
    print(f"  💰 Menor preço Motoristas: R$ {stats['menor_preco_motoristas']:.2f}")
    print(f"  💰 Maior preço Motoristas: R$ {stats['maior_preco_motoristas']:.2f}")
    print(f"  🚐 Custo diário van: R$ {stats['custo_diario_van']:.2f}")
    print(f"  🚗 Veículos disponíveis: {len(stats['veiculos_disponiveis'])}")

def main():
    """Executa todos os testes"""
    print("🧪 INICIANDO TESTES DO SISTEMA DE TARIFÁRIOS")
    print("=" * 60)
    
    try:
        test_veiculo_recomendado()
        test_busca_tarifario_jw()
        test_busca_tarifario_motoristas()
        test_gerar_chave_tarifario()
        test_calculo_preco_completo()
        test_estatisticas()
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES CONCLUÍDOS!")
        print("📝 Revise os resultados acima para identificar possíveis problemas.")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()