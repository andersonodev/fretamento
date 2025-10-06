#!/usr/bin/env python
"""
Debug das datas no banco de dados
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.models import Servico
from django.db.models import Count, Sum, Q

def debug_datas_servicos():
    """Verifica as datas dos serviços no banco"""
    print("=== DATAS DOS SERVIÇOS NO BANCO ===")
    
    # Buscar datas únicas com estatísticas
    datas_com_servicos = (Servico.objects
                         .values('data_do_servico')
                         .annotate(
                             total_servicos=Count('id'),
                             com_horario=Count('id', filter=Q(horario__isnull=False)),
                             total_pax=Sum('pax')
                         )
                         .order_by('-data_do_servico')[:10])
    
    for data_info in datas_com_servicos:
        data = data_info['data_do_servico']
        print(f"Data raw: {data}")
        print(f"Data formatada (d/m/Y): {data.strftime('%d/%m/%Y')}")
        print(f"Data formatada (m/d/Y): {data.strftime('%m/%d/%Y')}")
        print(f"Serviços: {data_info['total_servicos']}")
        print(f"PAX: {data_info['total_pax']}")
        print(f"Com horário: {data_info['com_horario']}")
        print("---")

def debug_primeiros_servicos():
    """Mostra os primeiros serviços para verificar formato das datas"""
    print("\n=== PRIMEIROS SERVIÇOS ===")
    
    servicos = Servico.objects.all()[:5]
    for servico in servicos:
        print(f"Cliente: {servico.cliente}")
        print(f"Data do serviço (raw): {servico.data_do_servico}")
        print(f"Data do serviço (d/m/Y): {servico.data_do_servico.strftime('%d/%m/%Y')}")
        print(f"Serviço: {servico.servico[:50]}...")
        print("---")

if __name__ == "__main__":
    debug_datas_servicos()
    debug_primeiros_servicos()