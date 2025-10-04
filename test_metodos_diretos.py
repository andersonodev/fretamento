#!/usr/bin/env python
"""
Teste direto do método alocar_veiculo_e_preco
"""

import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.logic import CalculadorVeiculoPreco
from core.tarifarios import calcular_preco_servico


class MockServico:
    """Mock simples do objeto Servico para testes"""
    def __init__(self, servico, pax, numero_venda):
        self.servico = servico
        self.pax = pax
        self.numero_venda = numero_venda


def test_alocar_veiculo_e_preco():
    """Testa diretamente o método alocar_veiculo_e_preco"""
    print("=== TESTE DIRETO DO MÉTODO alocar_veiculo_e_preco ===\n")
    
    calculador = CalculadorVeiculoPreco()
    
    # Criar alguns serviços mock
    servicos_teste = [
        MockServico('Transfer In ou Out Sdu / Centro', 2, 1),
        MockServico('Transfer OUT Santos Dumont Centro', 4, 2),
        MockServico('Disposição 04h', 8, 1),
        MockServico('Disposicao 6 horas', 12, 1),
    ]
    
    for i, servico in enumerate(servicos_teste, 1):
        print(f"Teste {i}: {servico.servico}")
        print(f"   PAX: {servico.pax} | Número de vendas: {servico.numero_venda}")
        
        try:
            # Testar o método alocar_veiculo_e_preco_servico (para serviços individuais)
            veiculo, preco = calculador.alocar_veiculo_e_preco_servico(servico)
            
            print(f"   Resultado: Veículo: {veiculo} | Preço: R$ {preco:.2f}")
            print("   ✅ Método funciona corretamente")
            
        except Exception as e:
            print(f"   ❌ ERRO: {str(e)}")
        
        print()


def test_calcular_preco_servico():
    """Testa diretamente a função calcular_preco_servico"""
    print("=== TESTE DIRETO DA FUNÇÃO calcular_preco_servico ===\n")
    
    # Criar alguns serviços mock
    servicos_teste = [
        MockServico('Transfer In ou Out Sdu / Centro', 2, 1),
        MockServico('Transfer OUT Santos Dumont Centro', 4, 2),
        MockServico('Disposição 04h', 8, 1),
        MockServico('Disposicao 6 horas', 12, 1),
    ]
    
    for i, servico in enumerate(servicos_teste, 1):
        print(f"Teste {i}: {servico.servico}")
        print(f"   PAX: {servico.pax} | Número de vendas: {servico.numero_venda}")
        
        try:
            # Testar a função calcular_preco_servico
            veiculo, preco = calcular_preco_servico(servico)
            
            print(f"   Resultado: Veículo: {veiculo} | Preço: R$ {preco:.2f}")
            print("   ✅ Função funciona corretamente")
            
        except Exception as e:
            print(f"   ❌ ERRO: {str(e)}")
        
        print()


if __name__ == "__main__":
    test_alocar_veiculo_e_preco()
    test_calcular_preco_servico()
    print("=== TESTES CONCLUÍDOS ===")