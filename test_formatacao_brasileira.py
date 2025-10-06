#!/usr/bin/env python3
"""
Teste para verificar se a formatação brasileira de preços está funcionando corretamente
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.templatetags.custom_filters import (
    currency, currency_compact, currency_no_cents, 
    number_br, price_per_pax, profit_margin, price_color_class, profit_score
)

def test_formatacao_brasileira():
    """
    Testa todos os filtros de formatação brasileira
    """
    print("🔢 Testando Formatação Brasileira de Preços")
    print("=" * 50)
    
    # Testes de currency
    print("💰 Teste currency():")
    valores_teste = [1234.56, 0, None, 1000000, 99.9, 10.1]
    for valor in valores_teste:
        resultado = currency(valor)
        print(f"  {valor} → {resultado}")
    
    print("\n💹 Teste currency_compact():")
    for valor in [1500, 12000, 1500000, 2500000]:
        resultado = currency_compact(valor)
        print(f"  {valor} → {resultado}")
    
    print("\n🏷️ Teste currency_no_cents():")
    for valor in [1234.56, 1000, 999.99]:
        resultado = currency_no_cents(valor)
        print(f"  {valor} → {resultado}")
    
    print("\n🔢 Teste number_br():")
    for valor in [1234.56, 1000000, 99.9]:
        resultado = number_br(valor)
        print(f"  {valor} → {resultado}")
    
    print("\n👥 Teste price_per_pax():")
    for preco, pax in [(1000, 10), (2500, 15), (0, 5)]:
        resultado = price_per_pax(preco, pax)
        print(f"  R$ {preco} ÷ {pax} PAX → {resultado}")
    
    print("\n📊 Teste profit_margin():")
    for preco, custo in [(1000, 800), (500, 600), (2000, 1500)]:
        resultado = profit_margin(preco, custo)
        print(f"  Preço: R$ {preco}, Custo: R$ {custo} → {resultado}")
    
    print("\n📈 Teste profit_score():")
    for valor in [12.5, 8.75, 15.0, 0]:
        resultado = profit_score(valor)
        print(f"  {valor} → {resultado}")
    
    print("\n🎨 Teste price_color_class():")
    for valor in [1000, 500, 2000]:
        resultado = price_color_class(valor)
        print(f"  R$ {valor} → classe: {resultado}")
    
    print("\n✅ Teste de Formatação Brasileira Concluído!")
    print("=" * 50)

def verificar_templates():
    """
    Verifica se os templates foram atualizados corretamente
    """
    print("\n📄 Verificando Templates Atualizados")
    print("=" * 50)
    
    templates_principais = [
        'templates/escalas/visualizar.html',
        'templates/escalas/gerenciar.html',
        'templates/escalas/selecionar_mes.html',
        'templates/core/tarifarios.html',
        'templates/core/simulador_precos.html'
    ]
    
    for template in templates_principais:
        if os.path.exists(template):
            with open(template, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
            # Verificar se ainda existem floatformat:2 com R$
            ocorrencias_antigas = conteudo.count('|floatformat:2')
            ocorrencias_currency = conteudo.count('|currency')
            
            print(f"📄 {template}:")
            print(f"  - floatformat:2 restantes: {ocorrencias_antigas}")
            print(f"  - |currency encontrados: {ocorrencias_currency}")
            
            if ocorrencias_antigas > 0:
                print(f"  ⚠️  Ainda existem formatações antigas!")
            else:
                print(f"  ✅ Template atualizado com sucesso!")
        else:
            print(f"❌ Template não encontrado: {template}")

if __name__ == "__main__":
    test_formatacao_brasileira()
    verificar_templates()