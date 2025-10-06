#!/usr/bin/env python
"""
Script para associar serviços existentes aos seus arquivos de origem
baseado na data de criação
"""

import os
import sys
import django
from datetime import datetime

# Configura Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.models import Servico, ProcessamentoPlanilha
from django.db.models import Q

def associar_servicos_arquivos():
    """Associa serviços existentes aos seus arquivos de origem"""
    
    print("🔧 Iniciando associação de serviços com arquivos...")
    
    # Busca serviços sem arquivo_origem definido
    servicos_sem_arquivo = Servico.objects.filter(
        Q(arquivo_origem__isnull=True) | Q(arquivo_origem='')
    )
    
    print(f"📄 Encontrados {servicos_sem_arquivo.count()} serviços sem arquivo de origem")
    
    # Busca processamentos concluídos
    processamentos = ProcessamentoPlanilha.objects.filter(
        status='CONCLUIDO'
    ).order_by('created_at')
    
    print(f"📁 Encontrados {processamentos.count()} arquivos processados")
    
    atualizados = 0
    
    for processamento in processamentos:
        # Busca serviços criados no mesmo dia do processamento
        data_processamento = processamento.created_at.date()
        
        servicos_do_dia = servicos_sem_arquivo.filter(
            created_at__date=data_processamento
        )
        
        if servicos_do_dia.exists():
            print(f"📋 Associando {servicos_do_dia.count()} serviços ao arquivo {processamento.nome_arquivo}")
            
            # Atualiza todos os serviços do dia
            servicos_atualizados = servicos_do_dia.update(
                arquivo_origem=processamento.nome_arquivo
            )
            
            atualizados += servicos_atualizados
    
    print(f"✅ Associação concluída! {atualizados} serviços foram associados aos seus arquivos de origem")
    return atualizados

if __name__ == '__main__':
    try:
        total_atualizados = associar_servicos_arquivos()
        print(f"\n🎉 Script executado com sucesso!")
        print(f"📊 Total de serviços atualizados: {total_atualizados}")
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        sys.exit(1)