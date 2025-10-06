#!/usr/bin/env python3
"""
Script para testar se o erro de decimal.InvalidOperation foi corrigido
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from escalas.views import converter_para_decimal_seguro
from escalas.models import AlocacaoVan, Escala
from core.models import Servico
from datetime import date, time
from decimal import Decimal

def testar_funcao_segura():
    """Testa a função converter_para_decimal_seguro"""
    print("🔧 TESTANDO FUNÇÃO SEGURA DE CONVERSÃO")
    print("-" * 50)
    
    valores_teste = [
        "",           # String vazia
        " ",          # Espaços
        "   ",        # Múltiplos espaços
        None,         # None
        "abc",        # Texto inválido
        "R$ 100,00",  # Formato monetário
        "100.50",     # Decimal válido
        100.75,       # Float válido
        200,          # Integer válido
    ]
    
    for valor in valores_teste:
        resultado = converter_para_decimal_seguro(valor)
        print(f"✅ '{valor}' -> {resultado}")

def testar_alocacao_com_valores_problematicos():
    """Testa a criação de alocação com valores que causariam erro"""
    print("\n🔧 TESTANDO ALOCAÇÃO COM VALORES PROBLEMÁTICOS")
    print("-" * 50)
    
    # Criar escala de teste
    escala = Escala.objects.create(
        data=date.today(),
        etapa='ESTRUTURA'
    )
    
    # Criar serviço com dados que poderiam causar problema
    servico = Servico.objects.create(
        numero_venda="",  # String vazia
        cliente="Cliente Teste Problemas",
        local_pickup="",  # String vazia
        pax=0,           # PAX zero
        horario=time(10, 0),
        data_do_servico=date.today(),
        servico="SERVIÇO TESTE PROBLEMAS"
    )
    
    try:
        # Criar alocação
        alocacao = AlocacaoVan.objects.create(
            escala=escala,
            servico=servico,
            van='VAN1',
            ordem=1,
            automatica=True
        )
        
        print(f"✅ Alocação criada: ID {alocacao.id}")
        
        # Calcular preço (aqui é onde era o erro)
        veiculo, preco = alocacao.calcular_preco_e_veiculo()
        
        print(f"✅ Cálculo concluído sem erro:")
        print(f"   - Veículo: {veiculo}")
        print(f"   - Preço: {preco}")
        print(f"   - Preço salvo: {alocacao.preco_calculado}")
        print(f"   - Lucratividade: {alocacao.lucratividade}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ainda presente: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Limpar dados de teste
        try:
            alocacao.delete()
            escala.delete() 
            servico.delete()
            print("🧹 Dados de teste limpos")
        except:
            pass

def main():
    """Função principal"""
    print("🔧 TESTE DE CORREÇÃO DO ERRO decimal.InvalidOperation")
    print("=" * 60)
    
    # 1. Testar função auxiliar
    testar_funcao_segura()
    
    # 2. Testar alocação com valores problemáticos
    sucesso = testar_alocacao_com_valores_problematicos()
    
    print("\n" + "=" * 60)
    if sucesso:
        print("✅ CORREÇÃO APLICADA COM SUCESSO!")
        print("O erro decimal.InvalidOperation foi corrigido.")
    else:
        print("❌ CORREÇÃO NÃO FUNCIONOU!")
        print("O erro ainda persiste.")
    print("=" * 60)

if __name__ == "__main__":
    main()