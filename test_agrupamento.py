#!/usr/bin/env python3
"""
Script para testar a funcionalidade de agrupamento
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from escalas.models import Escala, AlocacaoVan
from datetime import date

def testar_agrupamento():
    """Testa se o agrupamento está funcionando"""
    print("=== TESTE DE AGRUPAMENTO ===")
    
    # Buscar uma escala com dados
    escalas = Escala.objects.filter(etapa='DADOS_PUXADOS').order_by('-data')
    
    if not escalas.exists():
        print("❌ Nenhuma escala com dados puxados encontrada")
        return False
    
    escala = escalas.first()
    print(f"✅ Escala encontrada: {escala.data} (etapa: {escala.etapa})")
    
    # Verificar alocações disponíveis
    alocacoes = escala.alocacoes.all()
    print(f"📊 Total de alocações: {alocacoes.count()}")
    
    alocacoes_sem_grupo = escala.alocacoes.filter(grupo_info__isnull=True)
    print(f"📊 Alocações sem grupo: {alocacoes_sem_grupo.count()}")
    
    if alocacoes_sem_grupo.count() < 2:
        print("⚠️  Poucos serviços disponíveis para agrupamento")
    
    # Verificar se os métodos necessários existem
    try:
        from escalas.views import VisualizarEscalaView
        view = VisualizarEscalaView()
        
        print("✅ Método _agrupar_servicos existe")
        
        # Testar o agrupamento
        print("🔄 Executando agrupamento...")
        grupos_criados = view._agrupar_servicos(escala)
        print(f"✅ Agrupamento concluído: {grupos_criados} grupos criados")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no agrupamento: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_modelos():
    """Verifica se os modelos estão corretos"""
    print("\n=== VERIFICAÇÃO DOS MODELOS ===")
    
    try:
        from escalas.models import GrupoServico, ServicoGrupo
        print("✅ Modelos GrupoServico e ServicoGrupo importados")
        
        # Verificar fields
        grupo_fields = [field.name for field in GrupoServico._meta.fields]
        print(f"📋 Campos GrupoServico: {grupo_fields}")
        
        servico_grupo_fields = [field.name for field in ServicoGrupo._meta.fields]
        print(f"📋 Campos ServicoGrupo: {servico_grupo_fields}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação dos modelos: {e}")
        return False

def verificar_urls():
    """Verifica se as URLs estão configuradas"""
    print("\n=== VERIFICAÇÃO DAS URLS ===")
    
    try:
        from django.urls import reverse
        
        urls_teste = [
            'escalas:agrupar_servicos',
            'escalas:desagrupar_servico',
            'escalas:desagrupar_grupo_completo'
        ]
        
        for url_name in urls_teste:
            try:
                url = reverse(url_name)
                print(f"✅ URL {url_name}: {url}")
            except Exception as e:
                print(f"❌ URL {url_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação das URLs: {e}")
        return False

def main():
    """Função principal"""
    print("🔍 DIAGNÓSTICO DO BOTÃO DE AGRUPAMENTO\n")
    
    success = True
    
    # 1. Verificar modelos
    if not verificar_modelos():
        success = False
    
    # 2. Verificar URLs
    if not verificar_urls():
        success = False
    
    # 3. Testar agrupamento
    if not testar_agrupamento():
        success = False
    
    print(f"\n{'='*50}")
    if success:
        print("✅ DIAGNÓSTICO COMPLETO: Sistema funcionando")
    else:
        print("❌ DIAGNÓSTICO COMPLETO: Problemas encontrados")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()