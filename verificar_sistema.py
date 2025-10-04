#!/usr/bin/env python
"""
Script de verificação do sistema limpo
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.models import Servico, ProcessamentoPlanilha, GrupoServico
from escalas.models import Escala, AlocacaoVan, GrupoServico as EscalaGrupoServico, ServicoGrupo

def verificar_sistema():
    """Verifica o estado atual do sistema"""
    print("🔍 VERIFICAÇÃO DO SISTEMA DE FRETAMENTO")
    print("="*50)
    
    # Contadores
    servicos = Servico.objects.count()
    escalas = Escala.objects.count()
    alocacoes = AlocacaoVan.objects.count()
    grupos_core = GrupoServico.objects.count()
    grupos_escalas = EscalaGrupoServico.objects.count()
    servico_grupos = ServicoGrupo.objects.count()
    processamentos = ProcessamentoPlanilha.objects.count()
    
    print("📊 CONTAGEM ATUAL:")
    print(f"• Serviços: {servicos}")
    print(f"• Escalas: {escalas}")
    print(f"• Alocações de Van: {alocacoes}")
    print(f"• Grupos de Serviços (Core): {grupos_core}")
    print(f"• Grupos de Serviços (Escalas): {grupos_escalas}")
    print(f"• Serviços em Grupos: {servico_grupos}")
    print(f"• Processamentos de Planilha: {processamentos}")
    
    total = servicos + escalas + alocacoes + grupos_core + grupos_escalas + servico_grupos + processamentos
    
    print(f"\n📈 TOTAL DE REGISTROS: {total}")
    
    if total == 0:
        print("\n✅ SISTEMA COMPLETAMENTE LIMPO!")
        print("🎯 Pronto para receber novos dados")
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("1. Acesse http://127.0.0.1:8000/core/upload/")
        print("2. Faça upload de uma nova planilha")
        print("3. Os dados serão processados com formato brasileiro correto")
        print("4. Crie escalas usando os novos dados")
    else:
        print(f"\n⚠️  Sistema não está completamente limpo ({total} registros restantes)")
        
        if servicos > 0:
            print(f"   • {servicos} serviços ainda presentes")
        if escalas > 0:
            print(f"   • {escalas} escalas ainda presentes")
        if alocacoes > 0:
            print(f"   • {alocacoes} alocações ainda presentes")

if __name__ == "__main__":
    verificar_sistema()