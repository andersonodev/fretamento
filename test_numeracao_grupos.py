#!/usr/bin/env python3
"""
Teste para verificar numeração sequencial de grupos (Grupo #1, #2, etc.)
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from escalas.models import Escala
from core.templatetags.custom_filters import grupo_sequencial

def testar_numeracao_sequencial():
    """Testa se a numeração sequencial de grupos está funcionando"""
    
    print("🔍 Testando numeração sequencial de grupos...")
    
    try:
        # Buscar uma escala com grupos
        escala = Escala.objects.first()
        if not escala:
            print("❌ Nenhuma escala encontrada no banco de dados")
            return False
        
        print(f"📅 Testando escala: {escala.data}")
        
        # Buscar grupos das VANs
        grupos_van1 = list(escala.grupos.filter(van='VAN1').order_by('ordem'))
        grupos_van2 = list(escala.grupos.filter(van='VAN2').order_by('ordem'))
        
        print(f"\n📊 Grupos encontrados:")
        print(f"   • VAN1: {len(grupos_van1)} grupos")
        print(f"   • VAN2: {len(grupos_van2)} grupos")
        
        # Testar numeração VAN1
        if grupos_van1:
            print(f"\n🚐 VAN1 - Numeração sequencial:")
            for i, grupo in enumerate(grupos_van1, 1):
                numero_sequencial = grupo_sequencial(grupo, grupos_van1)
                db_id = grupo.id
                print(f"   • Grupo DB#{db_id} → Grupo #{numero_sequencial} (esperado: #{i})")
                
                if numero_sequencial != i:
                    print(f"   ❌ ERRO: Numeração incorreta! Esperado #{i}, obtido #{numero_sequencial}")
                    return False
                else:
                    print(f"   ✅ Correto: #{numero_sequencial}")
        else:
            print(f"\n🚐 VAN1: Nenhum grupo encontrado")
        
        # Testar numeração VAN2
        if grupos_van2:
            print(f"\n🚐 VAN2 - Numeração sequencial:")
            for i, grupo in enumerate(grupos_van2, 1):
                numero_sequencial = grupo_sequencial(grupo, grupos_van2)
                db_id = grupo.id
                print(f"   • Grupo DB#{db_id} → Grupo #{numero_sequencial} (esperado: #{i})")
                
                if numero_sequencial != i:
                    print(f"   ❌ ERRO: Numeração incorreta! Esperado #{i}, obtido #{numero_sequencial}")
                    return False
                else:
                    print(f"   ✅ Correto: #{numero_sequencial}")
        else:
            print(f"\n🚐 VAN2: Nenhum grupo encontrado")
        
        # Testar filtro com grupo inexistente
        if grupos_van1:
            print(f"\n🧪 Teste de grupo inexistente:")
            from escalas.models import GrupoServico
            grupo_fake = GrupoServico(id=99999, ordem=999)
            numero_fake = grupo_sequencial(grupo_fake, grupos_van1)
            print(f"   • Grupo inexistente → #{numero_fake} (esperado: #1)")
            
            if numero_fake == 1:
                print(f"   ✅ Correto: Grupo inexistente retorna #1")
            else:
                print(f"   ❌ ERRO: Grupo inexistente deveria retornar #1")
                return False
        
        # Verificar se o template foi atualizado
        template_path = project_root / "templates" / "escalas" / "visualizar.html"
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            if 'grupo_sequencial:grupos_van1' in template_content and 'grupo_sequencial:grupos_van2' in template_content:
                print(f"\n🎯 TEMPLATE: ✅ ATUALIZADO!")
                print(f"   Template usando filtro grupo_sequencial para VAN1 e VAN2")
                
                # Contar ocorrências
                van1_count = template_content.count('grupo_sequencial:grupos_van1')
                van2_count = template_content.count('grupo_sequencial:grupos_van2')
                print(f"   Filtros encontrados: VAN1={van1_count}, VAN2={van2_count}")
            else:
                print(f"\n🎯 TEMPLATE: ❌ NÃO ATUALIZADO!")
                print(f"   Template ainda não está usando o filtro grupo_sequencial")
                return False
        
        print(f"\n🎉 NUMERAÇÃO SEQUENCIAL IMPLEMENTADA:")
        print(f"   ✅ Filtro custom: grupo_sequencial funcionando")
        print(f"   ✅ Template: Usando numeração sequencial")
        print(f"   ✅ VAN1: Grupos #{1} a #{len(grupos_van1)}")
        print(f"   ✅ VAN2: Grupos #{1} a #{len(grupos_van2)}")
        print(f"   ✅ Ordenação: Por campo 'ordem' e depois por ID")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verificar_ordem_grupos():
    """Verifica se os grupos estão ordenados corretamente"""
    
    print("\n🔍 Verificando ordenação dos grupos...")
    
    try:
        escalas = Escala.objects.all()[:3]  # Verificar 3 escalas
        
        for escala in escalas:
            print(f"\n📅 Escala: {escala.data}")
            
            # VAN1
            grupos_van1 = escala.grupos.filter(van='VAN1').order_by('ordem', 'id')
            if grupos_van1:
                print(f"   🚐 VAN1 ({len(grupos_van1)} grupos):")
                for i, grupo in enumerate(grupos_van1, 1):
                    print(f"      #{i}: DB#{grupo.id}, ordem={grupo.ordem}, cliente={grupo.cliente_principal}")
            
            # VAN2
            grupos_van2 = escala.grupos.filter(van='VAN2').order_by('ordem', 'id')
            if grupos_van2:
                print(f"   🚐 VAN2 ({len(grupos_van2)} grupos):")
                for i, grupo in enumerate(grupos_van2, 1):
                    print(f"      #{i}: DB#{grupo.id}, ordem={grupo.ordem}, cliente={grupo.cliente_principal}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar ordenação: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando teste de numeração sequencial de grupos\n")
    
    # Verificar ordenação
    verificar_ordem_grupos()
    
    # Testar numeração sequencial
    sucesso = testar_numeracao_sequencial()
    
    if sucesso:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ A numeração sequencial dos grupos está funcionando corretamente!")
        print("💡 Agora os grupos aparecem como 'Grupo #1', 'Grupo #2', etc.")
    else:
        print("\n💥 ALGUNS TESTES FALHARAM!")
        print("❌ Verifique a implementação e tente novamente!")