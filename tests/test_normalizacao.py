#!/usr/bin/env python3
"""
Teste da normalização de nomes
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from escalas.views import VisualizarEscalaView

def testar_normalizacao():
    """Testa a normalização de nomes"""
    print("=== TESTE DE NORMALIZAÇÃO ===")
    
    view = VisualizarEscalaView()
    
    nomes_teste = [
        'TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BÚZIOS',
        'TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO (GIG) PARA ZONA SUL',
        'TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA HOTÉIS',
        'TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT RJ (SDU) PARA HOTÉIS',
    ]
    
    for nome in nomes_teste:
        normalizado = view._normalizar_nome_servico(nome)
        print(f"Original: {nome}")
        print(f"Normalizado: {normalizado}")
        print()

def comparar_nomes():
    """Compara nomes similares"""
    print("=== COMPARAÇÃO DE NOMES ===")
    
    view = VisualizarEscalaView()
    
    pares = [
        (
            'TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA ZONA SUL',
            'TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO (GIG) PARA ZONA SUL'
        ),
        (
            'TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA HOTÉIS',
            'TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT RJ (SDU) PARA HOTÉIS'
        )
    ]
    
    for nome1, nome2 in pares:
        norm1 = view._normalizar_nome_servico(nome1)
        norm2 = view._normalizar_nome_servico(nome2)
        
        print(f"Nome 1: {nome1}")
        print(f"Norm 1: {norm1}")
        print(f"Nome 2: {nome2}")
        print(f"Norm 2: {norm2}")
        print(f"Iguais: {norm1 == norm2}")
        print()

if __name__ == "__main__":
    testar_normalizacao()
    comparar_nomes()