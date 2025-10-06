#!/usr/bin/env python3
"""
Script para verificar se há dados problemáticos no sistema
"""
import os
import sys
import django
from decimal import Decimal, InvalidOperation

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from escalas.models import AlocacaoVan
from core.models import Servico

def verificar_alocacoes_problematicas():
    """Verifica se há alocações com valores problemáticos"""
    print("🔍 VERIFICANDO ALOCAÇÕES EXISTENTES")
    print("-" * 50)
    
    alocacoes = AlocacaoVan.objects.all()
    total = alocacoes.count()
    
    print(f"Total de alocações: {total}")
    
    if total == 0:
        print("ℹ️  Nenhuma alocação encontrada (sistema foi limpo)")
        return
    
    problemas_encontrados = 0
    
    for alocacao in alocacoes:
        try:
            # Testar se o preco_calculado pode ser convertido para Decimal
            if alocacao.preco_calculado is not None:
                teste_decimal = Decimal(str(alocacao.preco_calculado))
                
            # Testar se lucratividade é válida
            if alocacao.lucratividade is not None:
                teste_lucrat = float(alocacao.lucratividade)
            
        except (InvalidOperation, ValueError, TypeError) as e:
            print(f"⚠️  Problema na alocação ID {alocacao.id}:")
            print(f"   - Preço: {alocacao.preco_calculado} (tipo: {type(alocacao.preco_calculado)})")
            print(f"   - Lucratividade: {alocacao.lucratividade} (tipo: {type(alocacao.lucratividade)})")
            print(f"   - Erro: {e}")
            problemas_encontrados += 1
    
    if problemas_encontrados == 0:
        print("✅ Todas as alocações estão OK")
    else:
        print(f"⚠️  {problemas_encontrados} alocações com problemas encontradas")

def verificar_servicos_problematicos():
    """Verifica se há serviços com dados problemáticos"""
    print("\n🔍 VERIFICANDO SERVIÇOS EXISTENTES")
    print("-" * 50)
    
    servicos = Servico.objects.all()
    total = servicos.count()
    
    print(f"Total de serviços: {total}")
    
    if total == 0:
        print("ℹ️  Nenhum serviço encontrado (sistema foi limpo)")
        return
    
    problemas_encontrados = 0
    
    for servico in servicos:
        try:
            # Verificar PAX
            if servico.pax is None or servico.pax < 0:
                print(f"⚠️  Serviço ID {servico.id} com PAX inválido: {servico.pax}")
                problemas_encontrados += 1
                
            # Verificar número de venda
            if hasattr(servico, 'numero_venda'):
                numero_venda = servico.numero_venda
                if numero_venda and not str(numero_venda).strip():
                    print(f"⚠️  Serviço ID {servico.id} com número de venda vazio/espaços")
                    problemas_encontrados += 1
                    
        except Exception as e:
            print(f"⚠️  Erro ao verificar serviço ID {servico.id}: {e}")
            problemas_encontrados += 1
    
    if problemas_encontrados == 0:
        print("✅ Todos os serviços estão OK")
    else:
        print(f"⚠️  {problemas_encontrados} serviços com problemas encontrados")

def verificar_string_vazia_ou_espacos():
    """Testa conversões problemáticas específicas"""
    print("\n🔍 VERIFICANDO CONVERSÕES PROBLEMÁTICAS")
    print("-" * 50)
    
    valores_problematicos = [
        "",           # String vazia
        " ",          # Espaços
        "   ",        # Múltiplos espaços
        None,         # None
        "nan",        # Not a Number
        "inf",        # Infinito
        "-inf",       # Infinito negativo
        "abc",        # Texto
        "R$ 100,00",  # Formato monetário
        "100,50",     # Vírgula decimal
    ]
    
    for valor in valores_problematicos:
        try:
            resultado = Decimal(str(valor))
            print(f"✅ Conversão OK: '{valor}' -> {resultado}")
        except InvalidOperation:
            print(f"❌ InvalidOperation: '{valor}'")
        except Exception as e:
            print(f"❌ Outro erro: '{valor}' -> {e}")

def main():
    """Função principal"""
    print("🔧 VERIFICAÇÃO DE DADOS PROBLEMÁTICOS")
    print("=" * 60)
    
    verificar_alocacoes_problematicas()
    verificar_servicos_problematicos()
    verificar_string_vazia_ou_espacos()
    
    print("\n" + "=" * 60)
    print("🏁 VERIFICAÇÃO CONCLUÍDA")

if __name__ == "__main__":
    main()