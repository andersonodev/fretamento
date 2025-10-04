#!/usr/bin/env python
"""
Script de teste para verificar o sistema de busca inteligente de preços
"""

import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.busca_inteligente_precos import BuscadorInteligentePrecosCodigoDoAnalista
from core.logic import CalculadorVeiculoPreco
from core.models import Servico


def test_busca_inteligente():
    """Testa o sistema de busca inteligente"""
    print("=== TESTE DO SISTEMA DE BUSCA INTELIGENTE ===\n")
    
    # Criar instância do buscador
    buscador = BuscadorInteligentePrecosCodigoDoAnalista()
    
    # Testes de busca em diferentes tarifários
    testes = [
        # Teste 1: Transfer exato no tarifário de motoristas
        {
            'nome': 'Transfer In ou Out Sdu / Centro',
            'tipo': 'motoristas',
            'esperado': 40.0
        },
        # Teste 2: Transfer com variação no nome
        {
            'nome': 'Transfer OUT SDU Centro',
            'tipo': 'motoristas',
            'esperado': 40.0
        },
        # Teste 3: Transfer com mais variações
        {
            'nome': 'transfer saida santos dumont centro',
            'tipo': 'motoristas',
            'esperado': 40.0
        },
        # Teste 4: Disposição exata
        {
            'nome': 'Disposição 04h',
            'tipo': 'motoristas',
            'esperado': 170.0
        },
        # Teste 5: Disposição com variação
        {
            'nome': 'Disposicao 4 horas',
            'tipo': 'motoristas',
            'esperado': 170.0
        },
        # Teste 6: Busca no tarifário JW
        {
            'nome': 'Aeroporto Santos Dumont RJ',
            'tipo': 'jw',
            'veiculo': 'Executivo',
            'esperado': 85.0
        },
        # Teste 7: Busca no tarifário JW com variação
        {
            'nome': 'Santos Dumont Airport',
            'tipo': 'jw',
            'veiculo': 'Executivo',
            'esperado': 85.0
        }
    ]
    
    for i, teste in enumerate(testes, 1):
        print(f"Teste {i}: {teste['nome']}")
        
        if teste['tipo'] == 'jw':
            resultado = buscador.buscar_preco_jw(
                nome_servico=teste['nome'],
                veiculo=teste.get('veiculo', 'Executivo')
            )
        else:
            resultado = buscador.buscar_preco_motoristas(
                nome_servico=teste['nome'],
                numero_venda="1"
            )
        
        status = "✅ PASSOU" if resultado == teste['esperado'] else "❌ FALHOU"
        print(f"   Resultado: R$ {resultado:.2f} | Esperado: R$ {teste['esperado']:.2f} | {status}")
        
        if resultado != teste['esperado']:
            # Mostrar detalhes da busca para debug
            print(f"   DEBUG: Buscando '{teste['nome']}' no tarifário {teste['tipo']}")
            if teste['tipo'] == 'jw':
                matches = buscador.buscar_melhor_match_tarifario(teste['nome'], buscador.TARIFARIO_JW)
            else:
                matches = buscador.buscar_melhor_match_tarifario(teste['nome'], buscador.TARIFARIO_MOTORISTAS)
            
            if matches and len(matches) >= 3:
                print(f"   Melhor match encontrado: '{matches[0]}' (similaridade: {matches[1]:.3f})")
            else:
                print("   Nenhum match encontrado")
        
        print()


def test_calculador_veiculo_preco():
    """Testa a classe CalculadorVeiculoPreco"""
    print("=== TESTE DO CALCULADOR DE VEÍCULO E PREÇO ===\n")
    
    # Criar alguns serviços de teste
    servicos_teste = [
        {
            'servico': 'Transfer In ou Out Sdu / Centro',
            'pax': 2,
            'numero_venda': 1
        },
        {
            'servico': 'Transfer OUT Santos Dumont Centro',
            'pax': 4,
            'numero_venda': 2
        },
        {
            'servico': 'Disposição 6 horas',
            'pax': 8,
            'numero_venda': 1
        }
    ]
    
    calculador = CalculadorVeiculoPreco()
    
    for i, dados in enumerate(servicos_teste, 1):
        print(f"Teste {i}: {dados['servico']}")
        print(f"   PAX: {dados['pax']} | Número de vendas: {dados['numero_venda']}")
        
        try:
            # Criar objeto Servico para teste
            servico = Servico(
                servico=dados['servico'],
                pax=dados['pax'],
                numero_venda=dados['numero_venda']
            )
            
            # Testar o método alocar_veiculo_e_preco
            veiculo, preco = calculador.alocar_veiculo_e_preco(servico)
            
            print(f"   Resultado: Veículo: {veiculo} | Preço: R$ {preco:.2f}")
            print("   ✅ Método funciona corretamente")
            
        except Exception as e:
            print(f"   ❌ ERRO: {str(e)}")
        
        print()


if __name__ == "__main__":
    test_busca_inteligente()
    test_calculador_veiculo_preco()
    print("=== TESTES CONCLUÍDOS ===")