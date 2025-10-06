#!/usr/bin/env python3
"""
Script para debugar o erro de decimal.InvalidOperation
"""
import os
import sys
import django
from decimal import Decimal, InvalidOperation

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.models import Servico
from core.tarifarios import calcular_preco_servico
from core.busca_inteligente_precos import BuscadorInteligentePrecosCodigoDoAnalista

def criar_servico_teste():
    """Cria um serviço de teste para debugar"""
    class ServicoTeste:
        def __init__(self, servico="TRANSFER IN REGULAR", pax=2, numero_venda="1"):
            self.servico = servico
            self.pax = pax
            self.numero_venda = numero_venda
    
    return ServicoTeste()

def testar_conversao_decimal(valor):
    """Testa se um valor pode ser convertido para Decimal"""
    try:
        decimal_val = Decimal(str(valor))
        print(f"✅ Conversão OK: {valor} -> {decimal_val}")
        return True
    except InvalidOperation as e:
        print(f"❌ Erro de conversão: {valor} -> {e}")
        return False
    except Exception as e:
        print(f"❌ Outro erro: {valor} -> {e}")
        return False

def debug_calcular_preco():
    """Debug da função calcular_preco_servico"""
    print("🔍 DEBUG: calcular_preco_servico")
    print("-" * 50)
    
    servico_teste = criar_servico_teste()
    print(f"Serviço teste: {servico_teste.servico}, PAX: {servico_teste.pax}, Venda: {servico_teste.numero_venda}")
    
    try:
        veiculo, preco = calcular_preco_servico(servico_teste)
        print(f"Resultado: Veículo={veiculo}, Preço={preco} (tipo: {type(preco)})")
        
        # Testar conversão para Decimal
        if testar_conversao_decimal(preco):
            print("✅ Preço pode ser convertido para Decimal")
        else:
            print("❌ Preço NÃO pode ser convertido para Decimal")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro em calcular_preco_servico: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_buscador_inteligente():
    """Debug do buscador inteligente"""
    print("\n🔍 DEBUG: BuscadorInteligentePrecosCodigoDoAnalista")
    print("-" * 50)
    
    buscador = BuscadorInteligentePrecosCodigoDoAnalista()
    
    # Testar busca JW
    print("Testando busca JW...")
    preco_jw = buscador.buscar_preco_jw("TRANSFER IN REGULAR", "Executivo")
    print(f"Preço JW: {preco_jw} (tipo: {type(preco_jw)})")
    testar_conversao_decimal(preco_jw)
    
    # Testar busca motoristas
    print("\nTestando busca motoristas...")
    preco_motorista = buscador.buscar_preco_motoristas("TRANSFER IN REGULAR", "1")
    print(f"Preço Motorista: {preco_motorista} (tipo: {type(preco_motorista)})")
    testar_conversao_decimal(preco_motorista)

def debug_tarifarios():
    """Debug dos valores nos tarifários"""
    print("\n🔍 DEBUG: Valores nos tarifários")
    print("-" * 50)
    
    from core.tarifarios import TARIFARIO_JW, TARIFARIO_MOTORISTAS
    
    # Verificar valores problemáticos no TARIFARIO_JW
    print("Verificando TARIFARIO_JW...")
    for servico, dados in TARIFARIO_JW.items():
        if isinstance(dados, dict):
            for veiculo, preco in dados.items():
                if preco is not None:
                    if not testar_conversao_decimal(preco):
                        print(f"⚠️  Valor problemático em JW: {servico}[{veiculo}] = {preco}")
        else:
            if not testar_conversao_decimal(dados):
                print(f"⚠️  Valor problemático em JW: {servico} = {dados}")
    
    # Verificar valores problemáticos no TARIFARIO_MOTORISTAS
    print("\nVerificando TARIFARIO_MOTORISTAS...")
    for servico, preco in TARIFARIO_MOTORISTAS.items():
        if not testar_conversao_decimal(preco):
            print(f"⚠️  Valor problemático em MOTORISTAS: {servico} = {preco}")

def main():
    """Função principal"""
    print("🔧 DEBUG DO ERRO decimal.InvalidOperation")
    print("=" * 60)
    
    # 1. Testar valores nos tarifários
    debug_tarifarios()
    
    # 2. Testar buscador inteligente
    debug_buscador_inteligente()
    
    # 3. Testar função principal
    debug_calcular_preco()
    
    print("\n" + "=" * 60)
    print("🏁 DEBUG CONCLUÍDO")

if __name__ == "__main__":
    main()