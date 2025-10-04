#!/usr/bin/env python
"""
Script para limpar TODOS os dados do sistema de fretamento
Remove todos os serviços, escalas, alocações e processamentos de planilhas
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
from django.db import transaction

def confirmar_limpeza():
    """Solicita confirmação do usuário antes de prosseguir"""
    print("🚨 ATENÇÃO: OPERAÇÃO DESTRUTIVA 🚨")
    print("="*50)
    print("Esta operação irá APAGAR PERMANENTEMENTE:")
    print("✗ Todos os serviços importados")
    print("✗ Todas as escalas criadas") 
    print("✗ Todas as alocações de vans")
    print("✗ Todos os grupos de serviços")
    print("✗ Todo o histórico de processamento de planilhas")
    print("✗ Todos os dados relacionados")
    print("="*50)
    
    # Mostrar estatísticas atuais
    print("\n📊 DADOS ATUAIS NO SISTEMA:")
    print(f"• Serviços: {Servico.objects.count()}")
    print(f"• Escalas: {Escala.objects.count()}")
    print(f"• Alocações: {AlocacaoVan.objects.count()}")
    print(f"• Processamentos: {ProcessamentoPlanilha.objects.count()}")
    
    print("\n⚠️  ESTA AÇÃO NÃO PODE SER DESFEITA! ⚠️")
    
    while True:
        resposta = input("\nDeseja continuar? Digite 'CONFIRMAR' para prosseguir ou 'cancelar' para sair: ").strip()
        
        if resposta == 'CONFIRMAR':
            return True
        elif resposta.lower() in ['cancelar', 'cancel', 'não', 'nao', 'n']:
            return False
        else:
            print("❌ Resposta inválida. Digite 'CONFIRMAR' ou 'cancelar'")

def limpar_dados():
    """Remove todos os dados do sistema"""
    print("\n🧹 INICIANDO LIMPEZA DOS DADOS...")
    
    try:
        with transaction.atomic():
            # 1. Remover alocações e grupos de escalas (ordem importa devido às FKs)
            print("🗑️  Removendo alocações de vans...")
            alocacoes_removidas = AlocacaoVan.objects.count()
            AlocacaoVan.objects.all().delete()
            print(f"   ✅ {alocacoes_removidas} alocações removidas")
            
            print("🗑️  Removendo grupos de serviços das escalas...")
            servico_grupos_removidos = ServicoGrupo.objects.count()
            ServicoGrupo.objects.all().delete()
            print(f"   ✅ {servico_grupos_removidos} serviços de grupos removidos")
            
            escalas_grupos_removidos = EscalaGrupoServico.objects.count()
            EscalaGrupoServico.objects.all().delete()
            print(f"   ✅ {escalas_grupos_removidos} grupos de escalas removidos")
            
            # 2. Remover escalas
            print("🗑️  Removendo escalas...")
            escalas_removidas = Escala.objects.count()
            Escala.objects.all().delete()
            print(f"   ✅ {escalas_removidas} escalas removidas")
            
            # 3. Remover grupos de serviços gerais
            print("🗑️  Removendo grupos de serviços...")
            grupos_removidos = GrupoServico.objects.count()
            GrupoServico.objects.all().delete()
            print(f"   ✅ {grupos_removidos} grupos removidos")
            
            # 4. Remover todos os serviços
            print("🗑️  Removendo todos os serviços...")
            servicos_removidos = Servico.objects.count()
            Servico.objects.all().delete()
            print(f"   ✅ {servicos_removidos} serviços removidos")
            
            # 5. Remover histórico de processamentos
            print("🗑️  Removendo histórico de processamentos...")
            processamentos_removidos = ProcessamentoPlanilha.objects.count()
            ProcessamentoPlanilha.objects.all().delete()
            print(f"   ✅ {processamentos_removidos} processamentos removidos")
            
        print("\n🎉 LIMPEZA CONCLUÍDA COM SUCESSO!")
        print("="*50)
        print("✅ Todos os dados foram removidos do sistema")
        print("✅ O banco de dados está limpo e pronto para novos dados")
        print("✅ Você pode agora fazer upload de novas planilhas")
        
        # Verificar se realmente está vazio
        print("\n📊 VERIFICAÇÃO FINAL:")
        print(f"• Serviços: {Servico.objects.count()}")
        print(f"• Escalas: {Escala.objects.count()}")
        print(f"• Alocações: {AlocacaoVan.objects.count()}")
        print(f"• Processamentos: {ProcessamentoPlanilha.objects.count()}")
        
        if (Servico.objects.count() == 0 and 
            Escala.objects.count() == 0 and 
            AlocacaoVan.objects.count() == 0 and 
            ProcessamentoPlanilha.objects.count() == 0):
            print("\n✅ VERIFICAÇÃO PASSOU: Sistema completamente limpo!")
        else:
            print("\n⚠️  Alguns dados ainda permanecem no sistema")
            
    except Exception as e:
        print(f"\n❌ ERRO durante a limpeza: {e}")
        print("🔄 Operação revertida automaticamente (transação)")
        return False
    
    return True

def main():
    """Função principal"""
    print("🧹 LIMPEZA COMPLETA DO SISTEMA DE FRETAMENTO")
    print("="*50)
    
    if not confirmar_limpeza():
        print("\n❌ Operação cancelada pelo usuário")
        print("✅ Nenhum dado foi modificado")
        return
    
    print("\n⏳ Processando...")
    
    if limpar_dados():
        print("\n🎯 PRÓXIMOS PASSOS:")
        print("1. Acesse /core/upload/ para fazer upload de novas planilhas")
        print("2. Processe os dados com o novo formato brasileiro corrigido")
        print("3. Crie novas escalas com os dados limpos")
        
    print("\n🏁 Script finalizado!")

if __name__ == "__main__":
    main()