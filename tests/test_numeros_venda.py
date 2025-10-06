#!/usr/bin/env python3
"""
Teste completo do agrupamento com concatenação de números de venda
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

def testar_agrupamento_com_numeros_venda():
    """Testa se a concatenação de números de venda está funcionando"""
    
    # Data de teste
    data_teste = date.today()
    
    print(f"🧪 TESTE: Agrupamento com números de venda")
    print(f"   Data: {data_teste}")
    
    with transaction.atomic():
        # Limpar dados de teste anteriores
        Escala.objects.filter(data=data_teste).delete()
        
        # Criar escala de teste
        escala = Escala.objects.create(
            data=data_teste,
            etapa='CRIADA'
        )
        
        # Criar serviços de teste com números de venda
        servico1 = Servico.objects.create(
            cliente='HOTELBEDS',
            servico='TRANSFER IN REGULAR - AEROPORTO GALEÃO/RJ (GIG) X ZONA SUL',
            pax=4,
            horario=time(10, 0),
            local_pickup='Hotel Copacabana',
            numero_venda='HB001',
            data_do_servico=data_teste
        )
        
        servico2 = Servico.objects.create(
            cliente='HOTELBEDS',
            servico='TRANSFER IN REGULAR - AEROPORTO GALEÃO/RJ (GIG) X ZONA SUL',
            pax=3,
            horario=time(10, 15),
            local_pickup='Hotel Ipanema',
            numero_venda='HB002',
            data_do_servico=data_teste
        )
        
        servico3 = Servico.objects.create(
            cliente='HOLIDAY',
            servico='TRANSFER IN REGULAR - AEROPORTO GALEÃO/RJ (GIG) X ZONA SUL',
            pax=2,
            horario=time(10, 30),
            local_pickup='Hotel Leme',
            numero_venda='HL003',
            data_do_servico=data_teste
        )
        
        # Criar alocações
        alocacao1 = AlocacaoVan.objects.create(
            escala=escala,
            servico=servico1,
            preco_calculado=100.00
        )
        
        alocacao2 = AlocacaoVan.objects.create(
            escala=escala,
            servico=servico2,
            preco_calculado=80.00
        )
        
        alocacao3 = AlocacaoVan.objects.create(
            escala=escala,
            servico=servico3,
            preco_calculado=60.00
        )
        
        print(f"✅ Criados 3 serviços compatíveis:")
        print(f"   - {servico1.cliente}: {servico1.numero_venda} ({servico1.pax} PAX)")
        print(f"   - {servico2.cliente}: {servico2.numero_venda} ({servico2.pax} PAX)")
        print(f"   - {servico3.cliente}: {servico3.numero_venda} ({servico3.pax} PAX)")
        
        # Importar e usar a view para agrupar
        from escalas.views import GerenciarEscalasView
        view = GerenciarEscalasView()
        
        # Executar agrupamento
        grupos_criados = view._agrupar_servicos(escala)
        
        print(f"🔗 Agrupamento executado: {grupos_criados} grupos criados")
        
        # Verificar resultados
        grupos = GrupoServico.objects.filter(escala=escala)
        
        for grupo in grupos:
            print(f"\n📊 GRUPO CRIADO:")
            print(f"   Cliente Principal: {grupo.cliente_principal}")
            print(f"   Serviço Principal: {grupo.servico_principal}")
            print(f"   Total PAX: {grupo.total_pax}")
            print(f"   Total Valor: R$ {grupo.total_valor}")
            print(f"   Números de Venda: '{grupo.numeros_venda}'")
            
            # Verificar se os números de venda foram concatenados corretamente
            servicos_grupo = grupo.servicos.all()
            print(f"   Serviços no grupo: {len(servicos_grupo)}")
            
            for sg in servicos_grupo:
                print(f"     - {sg.alocacao.servico.cliente}: {sg.alocacao.servico.numero_venda}")
        
        # Validações
        if grupos.count() > 0:
            primeiro_grupo = grupos.first()
            expected_vendas = "HB001 / HB002 / HL003"
            
            if primeiro_grupo.numeros_venda == expected_vendas:
                print(f"\n✅ SUCESSO: Números de venda concatenados corretamente!")
                print(f"   Esperado: '{expected_vendas}'")
                print(f"   Obtido: '{primeiro_grupo.numeros_venda}'")
            else:
                print(f"\n❌ ERRO: Concatenação incorreta")
                print(f"   Esperado: '{expected_vendas}'")
                print(f"   Obtido: '{primeiro_grupo.numeros_venda}'")
            
            if primeiro_grupo.total_pax == 9:
                print(f"✅ SUCESSO: PAX somados corretamente (9)")
            else:
                print(f"❌ ERRO: PAX incorreto - esperado 9, obtido {primeiro_grupo.total_pax}")
            
            if primeiro_grupo.total_valor == 240.00:
                print(f"✅ SUCESSO: Valor somado corretamente (R$ 240.00)")
            else:
                print(f"❌ ERRO: Valor incorreto - esperado R$ 240.00, obtido R$ {primeiro_grupo.total_valor}")
        else:
            print(f"\n❌ ERRO: Nenhum grupo foi criado!")

if __name__ == '__main__':
    testar_agrupamento_com_numeros_venda()