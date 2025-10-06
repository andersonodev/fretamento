#!/usr/bin/env python
"""
Debug detalhado do sistema de busca
"""

import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.busca_inteligente_precos import BuscadorInteligentePrecosCodigoDoAnalista


def debug_busca():
    """Debug detalhado da busca"""
    print("=== DEBUG DETALHADO DA BUSCA ===\n")
    
    buscador = BuscadorInteligentePrecosCodigoDoAnalista()
    
    print("1. Verificando tarifários carregados:")
    print(f"   TARIFARIO_MOTORISTAS: {len(buscador.TARIFARIO_MOTORISTAS)} itens")
    print(f"   TARIFARIO_JW: {len(buscador.TARIFARIO_JW)} itens")
    print()
    
    print("2. Amostra do TARIFARIO_MOTORISTAS:")
    for i, (chave, valor) in enumerate(list(buscador.TARIFARIO_MOTORISTAS.items())[:5]):
        print(f"   '{chave}': {valor}")
    print()
    
    print("3. Testando busca específica:")
    nome_teste = "Transfer In ou Out Sdu / Centro"
    print(f"   Buscando: '{nome_teste}'")
    
    # Debug da busca step by step
    resultado = buscador.buscar_melhor_match_tarifario(
        nome_teste, buscador.TARIFARIO_MOTORISTAS, threshold=0.2
    )
    
    print(f"   Resultado da busca: {resultado}")
    
    if resultado and len(resultado) >= 3:
        chave, preco, similaridade = resultado
        print(f"   Chave encontrada: '{chave}'")
        print(f"   Preço: {preco}")
        print(f"   Similaridade: {similaridade}")
    else:
        print("   Nenhum resultado válido")
    
    print()
    
    # Teste com busca_preco_motoristas
    print("4. Testando busca_preco_motoristas:")
    preco_final = buscador.buscar_preco_motoristas(nome_teste, "1")
    print(f"   Preço final: {preco_final}")
    
    print()
    
    # Teste manual de similaridade
    print("5. Teste manual de similaridade:")
    nome_normalizado = buscador.normalizar_nome_servico(nome_teste)
    print(f"   Nome normalizado: '{nome_normalizado}'")
    
    for chave_tarifario in list(buscador.TARIFARIO_MOTORISTAS.keys())[:5]:
        chave_normalizada = buscador.normalizar_nome_servico(chave_tarifario)
        similaridade = buscador.calcular_similaridade(nome_teste, chave_tarifario)
        print(f"   '{chave_tarifario}' -> '{chave_normalizada}' | Sim: {similaridade:.3f}")


if __name__ == "__main__":
    debug_busca()