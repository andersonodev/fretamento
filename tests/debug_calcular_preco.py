#!/usr/bin/env python
"""
Debug da função calcular_preco_servico
"""

import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.tarifarios import calcular_preco_servico, calcular_veiculo_recomendado
from core.busca_inteligente_precos import BuscadorInteligentePrecosCodigoDoAnalista
from core.models import Servico


class MockServico:
    """Mock simples do objeto Servico para testes"""
    def __init__(self, servico, pax, numero_venda):
        self.servico = servico
        self.pax = pax
        self.numero_venda = numero_venda


def debug_calcular_preco_servico():
    """Debug da função calcular_preco_servico"""
    print("=== DEBUG CALCULAR_PRECO_SERVICO ===\n")
    
    # Criar mock
    mock_servico = MockServico('Transfer In ou Out Sdu / Centro', 2, 1)
    
    print("1. Verificando mock:")
    print(f"   servico: {mock_servico.servico}")
    print(f"   pax: {mock_servico.pax}")
    print(f"   numero_venda: {mock_servico.numero_venda}")
    print(f"   isinstance(mock_servico, Servico): {isinstance(mock_servico, Servico)}")
    print()
    
    print("2. Testando step by step:")
    
    # Simular o início da função
    if not isinstance(mock_servico, Servico):
        print("   ❌ Mock não é instância de Servico - retornando ('Executivo', 0.0)")
        return
    
    pax = mock_servico.pax
    veiculo = calcular_veiculo_recomendado(pax)
    print(f"   Veículo calculado: {veiculo}")
    
    # Testar busca inteligente
    buscador = BuscadorInteligentePrecosCodigoDoAnalista()
    
    preco_jw = buscador.buscar_preco_jw(
        nome_servico=mock_servico.servico,
        veiculo=veiculo
    )
    print(f"   Preço JW: {preco_jw}")
    
    if preco_jw == 0.0:
        preco_motoristas = buscador.buscar_preco_motoristas(
            nome_servico=mock_servico.servico,
            numero_venda=str(mock_servico.numero_venda)
        )
        print(f"   Preço Motoristas: {preco_motoristas}")
    
    print()
    
    print("3. Testando com objeto Servico real (se possível):")
    try:
        # Tentar criar um Servico real
        servico_real = Servico(
            servico='Transfer In ou Out Sdu / Centro',
            pax=2,
            numero_venda=1
        )
        print(f"   isinstance(servico_real, Servico): {isinstance(servico_real, Servico)}")
        
        # Testar a função completa
        veiculo, preco = calcular_preco_servico(servico_real)
        print(f"   Resultado: Veículo: {veiculo} | Preço: R$ {preco:.2f}")
        
    except Exception as e:
        print(f"   ❌ Erro ao criar Servico real: {e}")


if __name__ == "__main__":
    debug_calcular_preco_servico()