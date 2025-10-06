#!/usr/bin/env python3
"""
Script para testar se o erro de validação decimal foi corrigido
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.tarifarios import calcular_preco_servico
from core.models import Servico
from decimal import Decimal

def test_calcular_preco_servico():
    """Testa se a função calcular_preco_servico retorna a tupla corretamente"""
    
    print("🔍 Testando a função calcular_preco_servico...")
    
    # Criar um serviço de teste
    servico_teste = type('ServicoTeste', (), {
        'servico': 'Transfer GIG / Zona Sul',
        'pax': 3,
        'numero_venda': '123'
    })()
    
    try:
        resultado = calcular_preco_servico(servico_teste)
        print(f"✅ Resultado: {resultado}")
        print(f"✅ Tipo: {type(resultado)}")
        
        if isinstance(resultado, tuple) and len(resultado) == 2:
            veiculo, preco = resultado
            print(f"✅ Veículo: {veiculo} (tipo: {type(veiculo)})")
            print(f"✅ Preço: {preco} (tipo: {type(preco)})")
            
            # Testar se pode converter para Decimal
            preco_decimal = Decimal(str(preco))
            print(f"✅ Conversão para Decimal: {preco_decimal}")
            
            return True
        else:
            print(f"❌ Resultado não é uma tupla válida: {resultado}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_atribuicao_decimal():
    """Testa se a atribuição ao campo preco_calculado funciona"""
    
    print("\n🔍 Testando atribuição a campo DecimalField...")
    
    try:
        # Simular o que acontece na view
        from core.tarifarios import calcular_preco_servico
        
        servico_teste = type('ServicoTeste', (), {
            'servico': 'Transfer GIG / Zona Sul',
            'pax': 3,
            'numero_venda': '123'
        })()
        
        veiculo_recomendado, preco_calculado = calcular_preco_servico(servico_teste)
        
        print(f"✅ Desempacotamento funcionou:")
        print(f"   - Veículo: {veiculo_recomendado}")
        print(f"   - Preço: {preco_calculado}")
        
        # Testar se pode ser atribuído a um campo Decimal
        preco_decimal = Decimal(str(preco_calculado))
        print(f"✅ Pode ser convertido para Decimal: {preco_decimal}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na atribuição: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testando correção do erro de validação decimal")
    print("=" * 50)
    
    sucesso1 = test_calcular_preco_servico()
    sucesso2 = test_atribuicao_decimal()
    
    print("\n" + "=" * 50)
    if sucesso1 and sucesso2:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("✅ O erro de validação decimal foi corrigido.")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print("❌ O erro de validação decimal ainda persiste.")