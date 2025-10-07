#!/usr/bin/env python
import os
import sys
import django

# Configuração do Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from escalas.models import Escala, AlocacaoVan, GrupoServico, ServicoGrupo
from datetime import datetime

def debug_agrupamento():
    print("=== DEBUG AGRUPAMENTO ===")
    
    # Verificar escala para 07/10/2025
    data = datetime(2025, 10, 7).date()
    print(f"Procurando escala para: {data}")
    
    try:
        escala = Escala.objects.get(data=data)
        print(f"✅ Escala encontrada - ID: {escala.id}")
        print(f"   Etapa: '{escala.etapa}'")
        print(f"   Status: '{escala.status}'")
        
        # Verificar alocações
        total_alocacoes = escala.alocacoes.count()
        alocacoes_sem_grupo = escala.alocacoes.filter(grupo_info__isnull=True).count()
        alocacoes_com_grupo = escala.alocacoes.filter(grupo_info__isnull=False).count()
        
        print(f"   Total de alocações: {total_alocacoes}")
        print(f"   Alocações SEM grupo: {alocacoes_sem_grupo}")
        print(f"   Alocações COM grupo: {alocacoes_com_grupo}")
        
        # Verificar etapas válidas
        etapas_validas = ['DADOS_PUXADOS', 'OTIMIZADA']
        pode_agrupar = escala.etapa in etapas_validas
        print(f"   Pode agrupar? {pode_agrupar} (etapa deve estar em {etapas_validas})")
        
        if alocacoes_sem_grupo > 0:
            print(f"\n📋 Alocações disponíveis para agrupamento:")
            for alocacao in escala.alocacoes.filter(grupo_info__isnull=True)[:5]:  # Mostrar apenas 5
                servico = alocacao.servico
                print(f"   - ID: {alocacao.id} | {servico.cliente} | {servico.servico} | {servico.horario}")
        
        # Verificar grupos existentes
        grupos_existentes = escala.grupos.count()
        print(f"\n🔗 Grupos existentes: {grupos_existentes}")
        
        if grupos_existentes > 0:
            print("   Grupos:")
            for grupo in escala.grupos.all()[:3]:  # Mostrar apenas 3
                print(f"   - Grupo {grupo.id}: {grupo.cliente_principal} ({grupo.servicos.count()} serviços)")
                
    except Escala.DoesNotExist:
        print("❌ Escala não encontrada!")
        
        # Verificar se existem escalas próximas
        print("📅 Escalas disponíveis:")
        escalas = Escala.objects.all().order_by('-data')[:5]
        for e in escalas:
            print(f"   - {e.data} (ID: {e.id}, Etapa: {e.etapa})")

if __name__ == "__main__":
    debug_agrupamento()