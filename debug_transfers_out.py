#!/usr/bin/env python3
"""
Script específico para debugar problemas dos transfers OUT
"""
import os
import sys
import django
from datetime import time

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from escalas.views import VisualizarEscalaView

class ServicoTeste:
    """Classe mock para simular serviços"""
    def __init__(self, servico, horario, pax, numero_venda, local_pickup=""):
        self.servico = servico
        self.horario = horario
        self.pax = pax
        self.numero_venda = numero_venda
        self.local_pickup = local_pickup

def debug_transfers_out():
    """Debug específico para transfers OUT"""
    print("🔧 DEBUG TRANSFERS OUT REGULARES")
    print("="*60)
    
    view = VisualizarEscalaView()
    
    # Casos de teste
    transfer1 = ServicoTeste("TRANSFER OUT REGULAR", time(9, 0), 1, "Venda003", "Hotel X")
    transfer2 = ServicoTeste("TRANSFER OUT REGULAR", time(9, 25), 3, "Venda004", "Hotel X")  # Total PAX = 4
    transfer3 = ServicoTeste("TRANSFER OUT REGULAR", time(9, 30), 1, "Venda005", "Hotel Y")  # Local diferente
    transfer4 = ServicoTeste("TRANSFER OUT REGULAR", time(9, 40), 2, "Venda006", "Hotel X")  # PAX insuficiente
    
    print(f"Transfer 1: {transfer1.servico}, {transfer1.horario}, PAX={transfer1.pax}, Pickup='{transfer1.local_pickup}'")
    print(f"Transfer 2: {transfer2.servico}, {transfer2.horario}, PAX={transfer2.pax}, Pickup='{transfer2.local_pickup}'")
    print(f"Transfer 3: {transfer3.servico}, {transfer3.horario}, PAX={transfer3.pax}, Pickup='{transfer3.local_pickup}'")
    print(f"Transfer 4: {transfer4.servico}, {transfer4.horario}, PAX={transfer4.pax}, Pickup='{transfer4.local_pickup}'")
    print()
    
    # Debug passo a passo
    print("🔍 TESTE 1: Transfer1 + Transfer2 (mesmo pickup, PAX total = 4)")
    print("-" * 50)
    
    # Verificar se são transfers OUT
    eh_transfer1 = view._eh_transfer_out(transfer1.servico)
    eh_transfer2 = view._eh_transfer_out(transfer2.servico)
    print(f"Transfer1 é transfer OUT: {eh_transfer1}")
    print(f"Transfer2 é transfer OUT: {eh_transfer2}")
    
    # Verificar pickup
    mesmo_pickup = transfer1.local_pickup == transfer2.local_pickup
    print(f"Mesmo pickup: {mesmo_pickup} ('{transfer1.local_pickup}' == '{transfer2.local_pickup}')")
    
    # Verificar PAX
    total_pax = transfer1.pax + transfer2.pax
    pax_suficiente = total_pax >= 4
    print(f"PAX total: {total_pax} ≥ 4? {pax_suficiente}")
    
    # Teste final
    resultado = view._servicos_sao_compativeis(transfer1, transfer2)
    print(f"Resultado final: {resultado}")
    print()
    
    print("🔍 TESTE 2: Transfer1 + Transfer3 (pickup diferente)")
    print("-" * 50)
    mesmo_pickup = transfer1.local_pickup == transfer3.local_pickup
    print(f"Mesmo pickup: {mesmo_pickup} ('{transfer1.local_pickup}' == '{transfer3.local_pickup}')")
    resultado = view._servicos_sao_compativeis(transfer1, transfer3)
    print(f"Resultado final: {resultado}")
    print()
    
    print("🔍 TESTE 3: Transfer1 + Transfer4 (mesmo pickup, PAX total = 3)")
    print("-" * 50)
    total_pax = transfer1.pax + transfer4.pax
    pax_suficiente = total_pax >= 4
    print(f"PAX total: {total_pax} ≥ 4? {pax_suficiente}")
    resultado = view._servicos_sao_compativeis(transfer1, transfer4)
    print(f"Resultado final: {resultado}")

if __name__ == "__main__":
    debug_transfers_out()