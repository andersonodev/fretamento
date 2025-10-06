#!/usr/bin/env python
"""
Script para corrigir as datas que foram importadas incorretamente no banco
Converte datas que foram interpretadas como americanas para o formato brasileiro correto
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.models import Servico
from datetime import date

def corrigir_datas_americanas():
    """Corrige datas que foram interpretadas incorretamente"""
    print("=== CORRIGINDO DATAS AMERICANAS PARA BRASILEIRAS ===")
    
    # Mapear datas problemáticas
    correcoes = {
        # Formato americano -> Formato brasileiro correto
        date(2025, 1, 10): date(2025, 10, 1),   # 01/10/2025 -> 10/01/2025
        date(2025, 2, 10): date(2025, 10, 2),   # 02/10/2025 -> 10/02/2025  
        date(2025, 3, 10): date(2025, 10, 3),   # 03/10/2025 -> 10/03/2025
        date(2025, 4, 10): date(2025, 10, 4),   # 04/10/2025 -> 10/04/2025
        date(2025, 5, 10): date(2025, 10, 5),   # 05/10/2025 -> 10/05/2025
        # Note: 10/10/2025 permanece igual (10/10/2025)
        # Note: 15/10/2025 já está correto (não pode ser mês 15)
    }
    
    total_corrigidos = 0
    
    for data_errada, data_correta in correcoes.items():
        # Contar serviços com data errada
        servicos_errados = Servico.objects.filter(data_do_servico=data_errada)
        count = servicos_errados.count()
        
        if count > 0:
            print(f"Corrigindo {count} serviços de {data_errada.strftime('%Y-%m-%d')} para {data_correta.strftime('%Y-%m-%d')}")
            
            # Atualizar em lote
            servicos_errados.update(data_do_servico=data_correta)
            total_corrigidos += count
    
    print(f"\n✅ Total de serviços corrigidos: {total_corrigidos}")
    
    # Mostrar estatísticas finais
    print("\n=== ESTATÍSTICAS FINAIS ===")
    datas_unicas = Servico.objects.values_list('data_do_servico', flat=True).distinct().order_by('-data_do_servico')[:10]
    
    for data in datas_unicas:
        count = Servico.objects.filter(data_do_servico=data).count()
        print(f"Data: {data.strftime('%d/%m/%Y')} - {count} serviços")

if __name__ == "__main__":
    corrigir_datas_americanas()