#!/usr/bin/env python3
"""
Script para apagar todos os serviços que foram feitos upload no sistema
"""
import os
import sys
import django
from django.db import transaction

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.models import Servico, GrupoServico, ServicoGrupo
from escalas.models import Escala, AlocacaoVan, GrupoServico as EscalaGrupoServico, ServicoGrupo as EscalaServicoGrupo

def contar_dados():
    """Conta todos os dados antes da exclusão"""
    print("📊 CONTAGEM ATUAL DE DADOS NO SISTEMA:")
    print("-" * 50)
    
    # Contar serviços
    total_servicos = Servico.objects.count()
    print(f"🔹 Serviços: {total_servicos}")
    
    # Contar escalas
    total_escalas = Escala.objects.count()
    print(f"🔹 Escalas: {total_escalas}")
    
    # Contar alocações
    total_alocacoes = AlocacaoVan.objects.count()
    print(f"🔹 Alocações de Van: {total_alocacoes}")
    
    # Contar grupos de serviços (core)
    total_grupos_core = GrupoServico.objects.count()
    print(f"🔹 Grupos de Serviço (core): {total_grupos_core}")
    
    # Contar relações serviço-grupo (core)
    total_servico_grupo_core = ServicoGrupo.objects.count()
    print(f"🔹 Relações Serviço-Grupo (core): {total_servico_grupo_core}")
    
    # Contar grupos de serviços (escalas) - se existir
    try:
        total_grupos_escalas = EscalaGrupoServico.objects.count()
        print(f"🔹 Grupos de Serviço (escalas): {total_grupos_escalas}")
    except:
        print(f"🔹 Grupos de Serviço (escalas): Modelo não encontrado")
    
    # Contar relações serviço-grupo (escalas) - se existir
    try:
        total_servico_grupo_escalas = EscalaServicoGrupo.objects.count()
        print(f"🔹 Relações Serviço-Grupo (escalas): {total_servico_grupo_escalas}")
    except:
        print(f"🔹 Relações Serviço-Grupo (escalas): Modelo não encontrado")
    
    print("-" * 50)
    return total_servicos, total_escalas, total_alocacoes

def confirmar_exclusao():
    """Solicita confirmação do usuário"""
    print("\n⚠️  ATENÇÃO: OPERAÇÃO IRREVERSÍVEL!")
    print("Esta operação irá apagar TODOS os dados de serviços do sistema:")
    print("• Todos os serviços importados")
    print("• Todas as escalas criadas") 
    print("• Todas as alocações de vans")
    print("• Todos os grupos de serviços")
    print("• Todas as relações entre serviços e grupos")
    
    resposta = input("\n❓ Tem certeza que deseja continuar? Digite 'CONFIRMO' para prosseguir: ")
    return resposta.upper() == 'CONFIRMO'

def apagar_todos_dados():
    """Apaga todos os dados do sistema"""
    print("\n🗑️  INICIANDO EXCLUSÃO DE DADOS...")
    print("=" * 60)
    
    try:
        with transaction.atomic():
            # 1. Apagar relações serviço-grupo (core)
            print("🔄 Apagando relações Serviço-Grupo (core)...")
            count = ServicoGrupo.objects.count()
            ServicoGrupo.objects.all().delete()
            print(f"   ✅ {count} relações apagadas")
            
            # 2. Apagar relações serviço-grupo (escalas) - se existir
            try:
                print("🔄 Apagando relações Serviço-Grupo (escalas)...")
                count = EscalaServicoGrupo.objects.count()
                EscalaServicoGrupo.objects.all().delete()
                print(f"   ✅ {count} relações apagadas")
            except Exception as e:
                print(f"   ⚠️  Modelo não encontrado ou erro: {e}")
            
            # 3. Apagar grupos de serviços (core)
            print("🔄 Apagando Grupos de Serviços (core)...")
            count = GrupoServico.objects.count()
            GrupoServico.objects.all().delete()
            print(f"   ✅ {count} grupos apagados")
            
            # 4. Apagar grupos de serviços (escalas) - se existir
            try:
                print("🔄 Apagando Grupos de Serviços (escalas)...")
                count = EscalaGrupoServico.objects.count()
                EscalaGrupoServico.objects.all().delete()
                print(f"   ✅ {count} grupos apagados")
            except Exception as e:
                print(f"   ⚠️  Modelo não encontrado ou erro: {e}")
            
            # 5. Apagar alocações de vans
            print("🔄 Apagando Alocações de Vans...")
            count = AlocacaoVan.objects.count()
            AlocacaoVan.objects.all().delete()
            print(f"   ✅ {count} alocações apagadas")
            
            # 6. Apagar escalas
            print("🔄 Apagando Escalas...")
            count = Escala.objects.count()
            Escala.objects.all().delete()
            print(f"   ✅ {count} escalas apagadas")
            
            # 7. Apagar serviços (por último, pois outros dependem dele)
            print("🔄 Apagando Serviços...")
            count = Servico.objects.count()
            Servico.objects.all().delete()
            print(f"   ✅ {count} serviços apagados")
            
            print("\n✅ EXCLUSÃO CONCLUÍDA COM SUCESSO!")
            
    except Exception as e:
        print(f"\n❌ ERRO durante a exclusão: {e}")
        print("💡 A transação foi revertida. Nenhum dado foi perdido.")
        return False
    
    return True

def verificar_limpeza():
    """Verifica se a limpeza foi bem-sucedida"""
    print("\n🔍 VERIFICAÇÃO PÓS-LIMPEZA:")
    print("-" * 40)
    
    servicos_restantes = Servico.objects.count()
    escalas_restantes = Escala.objects.count()
    alocacoes_restantes = AlocacaoVan.objects.count()
    grupos_restantes = GrupoServico.objects.count()
    relacoes_restantes = ServicoGrupo.objects.count()
    
    print(f"🔹 Serviços restantes: {servicos_restantes}")
    print(f"🔹 Escalas restantes: {escalas_restantes}")
    print(f"🔹 Alocações restantes: {alocacoes_restantes}")
    print(f"🔹 Grupos restantes: {grupos_restantes}")
    print(f"🔹 Relações restantes: {relacoes_restantes}")
    
    if all(count == 0 for count in [servicos_restantes, escalas_restantes, alocacoes_restantes, grupos_restantes, relacoes_restantes]):
        print("\n🎉 SISTEMA COMPLETAMENTE LIMPO!")
        return True
    else:
        print("\n⚠️  Alguns dados ainda restam no sistema.")
        return False

def main():
    """Função principal"""
    print("🧹 LIMPEZA COMPLETA DO SISTEMA DE FRETAMENTO")
    print("=" * 60)
    
    # 1. Contar dados atuais
    contar_dados()
    
    # 2. Solicitar confirmação
    if not confirmar_exclusao():
        print("\n❌ Operação cancelada pelo usuário.")
        return
    
    # 3. Executar limpeza
    sucesso = apagar_todos_dados()
    
    if sucesso:
        # 4. Verificar se a limpeza foi bem-sucedida
        verificar_limpeza()
        
        print("\n" + "=" * 60)
        print("✅ LIMPEZA CONCLUÍDA!")
        print("O sistema está agora completamente limpo e pronto para novos uploads.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ LIMPEZA FALHOU!")
        print("Verifique os erros acima e tente novamente.")
        print("=" * 60)

if __name__ == "__main__":
    main()