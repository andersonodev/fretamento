#!/usr/bin/env python3
"""
Teste final completo - Validação de todos os requisitos implementados
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from escalas.models import Escala, AlocacaoVan, GrupoServico, ServicoGrupo
from core.models import Servico
from datetime import date, time
from django.db import transaction

def testar_implementacao_completa():
    """
    Teste completo de todos os requisitos implementados:
    1. Botão Agrupar - PAX total, números de venda concatenados
    2. Transfer OUT regulares - mesmo pickup + PAX >= 4
    3. Tours e variações - grouping por nome e horário
    4. GUIA À DISPOSIÇÃO - diferentes durações
    """
    
    data_teste = date.today()
    
    print(f"🔥 TESTE FINAL COMPLETO - SISTEMA DE AGRUPAMENTO")
    print(f"=" * 60)
    
    with transaction.atomic():
        # Limpar dados anteriores
        Escala.objects.filter(data=data_teste).delete()
        
        # Criar escala
        escala = Escala.objects.create(data=data_teste, etapa='CRIADA')
        
        # === CENÁRIO 1: TRANSFERS IN REGULARES ===
        print(f"\n📋 CENÁRIO 1: Transfers IN Regulares")
        
        servicos_transfer_in = [
            {
                'cliente': 'HOTELBEDS',
                'servico': 'TRANSFER IN REGULAR - AEROPORTO GALEÃO/RJ (GIG) X ZONA SUL',
                'pax': 4,
                'horario': time(10, 0),
                'pickup': 'Hotel A',
                'venda': 'HB001'
            },
            {
                'cliente': 'HOLIDAY',
                'servico': 'TRANSFER IN REGULAR - AEROPORTO GALEÃO/RJ (GIG) X ZONA SUL',
                'pax': 3,
                'horario': time(10, 20),
                'pickup': 'Hotel B',
                'venda': 'HL001'
            }
        ]
        
        for srv_data in servicos_transfer_in:
            servico = Servico.objects.create(
                cliente=srv_data['cliente'],
                servico=srv_data['servico'],
                pax=srv_data['pax'],
                horario=srv_data['horario'],
                local_pickup=srv_data['pickup'],
                numero_venda=srv_data['venda'],
                data_do_servico=data_teste
            )
            AlocacaoVan.objects.create(
                escala=escala,
                servico=servico,
                preco_calculado=100.00
            )
        
        # === CENÁRIO 2: TRANSFERS OUT REGULARES ===
        print(f"\n📋 CENÁRIO 2: Transfers OUT Regulares - Mesmo pickup")
        
        servicos_transfer_out = [
            {
                'cliente': 'CLIENTE_A',
                'servico': 'TRANSFER OUT REGULAR - ZONA SUL X AEROPORTO GALEÃO/RJ (GIG)',
                'pax': 2,
                'horario': time(14, 0),
                'pickup': 'Hotel Copacabana',  # MESMO PICKUP
                'venda': 'TO001'
            },
            {
                'cliente': 'CLIENTE_B',
                'servico': 'TRANSFER OUT REGULAR - ZONA SUL X AEROPORTO GALEÃO/RJ (GIG)',
                'pax': 3,
                'horario': time(14, 15),
                'pickup': 'Hotel Copacabana',  # MESMO PICKUP
                'venda': 'TO002'
            }
        ]
        
        for srv_data in servicos_transfer_out:
            servico = Servico.objects.create(
                cliente=srv_data['cliente'],
                servico=srv_data['servico'],
                pax=srv_data['pax'],
                horario=srv_data['horario'],
                local_pickup=srv_data['pickup'],
                numero_venda=srv_data['venda'],
                data_do_servico=data_teste
            )
            AlocacaoVan.objects.create(
                escala=escala,
                servico=servico,
                preco_calculado=120.00
            )
        
        # === CENÁRIO 3: TOURS ===
        print(f"\n📋 CENÁRIO 3: Tours e Variações")
        
        servicos_tours = [
            {
                'cliente': 'TOUR_CLIENTE',
                'servico': 'TOUR CIDADE MARAVILHOSA - 6H',
                'pax': 4,
                'horario': time(9, 0),
                'pickup': 'Ponto A',
                'venda': 'TR001'
            },
            {
                'cliente': 'VEIC_CLIENTE',
                'servico': 'VEÍCULO + GUIA À DISPOSIÇÃO - 8H',
                'pax': 3,
                'horario': time(9, 30),
                'pickup': 'Ponto B',
                'venda': 'VG001'
            }
        ]
        
        for srv_data in servicos_tours:
            servico = Servico.objects.create(
                cliente=srv_data['cliente'],
                servico=srv_data['servico'],
                pax=srv_data['pax'],
                horario=srv_data['horario'],
                local_pickup=srv_data['pickup'],
                numero_venda=srv_data['venda'],
                data_do_servico=data_teste
            )
            AlocacaoVan.objects.create(
                escala=escala,
                servico=servico,
                preco_calculado=250.00
            )
        
        # === CENÁRIO 4: GUIA À DISPOSIÇÃO ===
        print(f"\n📋 CENÁRIO 4: Guia à Disposição - Diferentes durações")
        
        servicos_guia = [
            {
                'cliente': 'GUIA_CLIENTE_1',
                'servico': 'GUIA À DISPOSIÇÃO 4 HORAS',
                'pax': 5,
                'horario': time(13, 0),
                'pickup': 'Local X',
                'venda': 'GD001'
            },
            {
                'cliente': 'GUIA_CLIENTE_2',
                'servico': 'GUIA À DISPOSIÇÃO 6 HORAS',
                'pax': 4,
                'horario': time(13, 20),
                'pickup': 'Local Y',
                'venda': 'GD002'
            }
        ]
        
        for srv_data in servicos_guia:
            servico = Servico.objects.create(
                cliente=srv_data['cliente'],
                servico=srv_data['servico'],
                pax=srv_data['pax'],
                horario=srv_data['horario'],
                local_pickup=srv_data['pickup'],
                numero_venda=srv_data['venda'],
                data_do_servico=data_teste
            )
            AlocacaoVan.objects.create(
                escala=escala,
                servico=servico,
                preco_calculado=150.00
            )
        
        print(f"\n✅ Criados {escala.alocacoes.count()} serviços de teste")
        
        # EXECUTAR AGRUPAMENTO
        print(f"\n🔗 EXECUTANDO AGRUPAMENTO...")
        from escalas.views import GerenciarEscalasView
        view = GerenciarEscalasView()
        grupos_criados = view._agrupar_servicos(escala)
        
        print(f"🎯 Resultado: {grupos_criados} grupos criados")
        
        # VALIDAR RESULTADOS
        print(f"\n📊 VALIDAÇÃO DOS RESULTADOS:")
        print(f"=" * 40)
        
        grupos = GrupoServico.objects.filter(escala=escala).order_by('id')
        
        for i, grupo in enumerate(grupos, 1):
            print(f"\n🔸 GRUPO {i}:")
            print(f"   Cliente: {grupo.cliente_principal}")
            print(f"   Serviço: {grupo.servico_principal}")
            print(f"   PAX Total: {grupo.total_pax}")
            print(f"   Valor Total: R$ {grupo.total_valor}")
            print(f"   Números Venda: '{grupo.numeros_venda}'")
            
            servicos_no_grupo = grupo.servicos.all()
            print(f"   Serviços ({len(servicos_no_grupo)}):")
            for sg in servicos_no_grupo:
                s = sg.alocacao.servico
                print(f"     • {s.cliente}: {s.numero_venda} ({s.pax} PAX)")
        
        # VALIDAÇÕES ESPECÍFICAS
        print(f"\n🔍 VALIDAÇÕES ESPECÍFICAS:")
        print(f"=" * 30)
        
        # Transfers IN devem estar agrupados
        grupo_transfer_in = None
        for grupo in grupos:
            if 'TRANSFER IN' in grupo.servico_principal:
                grupo_transfer_in = grupo
                break
        
        if grupo_transfer_in:
            if 'HB001 / HL001' in grupo_transfer_in.numeros_venda:
                print(f"✅ Transfers IN agrupados com vendas concatenadas")
            else:
                print(f"❌ Transfers IN - problema na concatenação")
            
            if grupo_transfer_in.total_pax == 7:
                print(f"✅ Transfers IN - PAX correto (7)")
            else:
                print(f"❌ Transfers IN - PAX incorreto: {grupo_transfer_in.total_pax}")
        
        # Transfers OUT devem estar agrupados (mesmo pickup + PAX >= 4)
        grupo_transfer_out = None
        for grupo in grupos:
            if 'TRANSFER OUT' in grupo.servico_principal and 'REGULAR' in grupo.servico_principal:
                grupo_transfer_out = grupo
                break
        
        if grupo_transfer_out:
            if 'TO001 / TO002' in grupo_transfer_out.numeros_venda:
                print(f"✅ Transfers OUT agrupados (mesmo pickup + PAX >= 4)")
            else:
                print(f"❌ Transfers OUT - problema na concatenação")
            
            if grupo_transfer_out.total_pax == 5:
                print(f"✅ Transfers OUT - PAX correto (5)")
            else:
                print(f"❌ Transfers OUT - PAX incorreto: {grupo_transfer_out.total_pax}")
        
        # Verificar se todos os tours foram agrupados ou ficaram individuais corretamente
        tours_agrupados = False
        for grupo in grupos:
            if ('TOUR' in grupo.servico_principal or 
                'VEÍCULO + GUIA' in grupo.servico_principal or
                'GUIA À DISPOSIÇÃO' in grupo.servico_principal):
                servicos_grupo = grupo.servicos.count()
                if servicos_grupo > 1:
                    tours_agrupados = True
                    print(f"✅ Tours/Guias agrupados: {servicos_grupo} serviços")
        
        if not tours_agrupados:
            print(f"ℹ️  Tours/Guias permaneceram individuais (correto se não compatíveis)")
        
        print(f"\n🎉 TESTE COMPLETO FINALIZADO!")
        print(f"   Total de grupos criados: {grupos.count()}")
        print(f"   Total de serviços agrupados: {sum(g.servicos.count() for g in grupos)}")

if __name__ == '__main__':
    testar_implementacao_completa()