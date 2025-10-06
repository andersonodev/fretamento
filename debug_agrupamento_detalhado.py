#!/usr/bin/env python
"""
Script para debugar por que o agrupamento não está funcionando
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from escalas.models import Escala, AlocacaoVan, GrupoServico

def debug_agrupamento():
    """Debug detalhado do agrupamento"""
    print("=== DEBUG AGRUPAMENTO ===\n")
    
    # Pegar a escala de teste
    escala = Escala.objects.get(data='2025-10-02')
    print(f"Escala: {escala.data} - Etapa: {escala.etapa}")
    
    # Buscar alocações sem grupo
    alocacoes_sem_grupo = escala.alocacoes.filter(grupo_info__isnull=True)
    print(f"Alocações sem grupo: {alocacoes_sem_grupo.count()}")
    
    if alocacoes_sem_grupo.count() == 0:
        print("❌ Todas as alocações já estão agrupadas!")
        return
    
    print("\n--- PRIMEIRAS 10 ALOCAÇÕES SEM GRUPO ---")
    for i, alocacao in enumerate(alocacoes_sem_grupo[:10]):
        servico = alocacao.servico
        print(f"{i+1}. ID:{alocacao.id} | Cliente: {servico.cliente[:20]}... | "
              f"Serviço: {servico.servico[:30]}... | PAX: {servico.pax} | "
              f"Horário: {servico.horario} | Pickup: {servico.local_pickup[:20] if servico.local_pickup else 'N/A'}...")
    
    print("\n--- TENTANDO AGRUPAR PRIMEIRA ALOCAÇÃO ---")
    primeira_alocacao = alocacoes_sem_grupo.first()
    servico_base = primeira_alocacao.servico
    
    print(f"Serviço base: {servico_base.servico}")
    print(f"Cliente: {servico_base.cliente}")
    print(f"PAX: {servico_base.pax}")
    print(f"Horário: {servico_base.horario}")
    print(f"Pickup: {servico_base.local_pickup}")
    
    print("\n--- VERIFICANDO COMPATIBILIDADE COM OUTROS SERVIÇOS ---")
    compatibilidades = 0
    
    for i, outra_alocacao in enumerate(alocacoes_sem_grupo[1:6]):  # Primeiros 5
        outro_servico = outra_alocacao.servico
        
        print(f"\n{i+1}. Comparando com:")
        print(f"   Serviço: {outro_servico.servico}")
        print(f"   Cliente: {outro_servico.cliente}")
        print(f"   PAX: {outro_servico.pax}")
        print(f"   Horário: {outro_servico.horario}")
        print(f"   Pickup: {outro_servico.local_pickup}")
        
        # Verificar se são transfers OUT
        is_base_transfer_out = 'TRANSFER OUT' in servico_base.servico.upper()
        is_outro_transfer_out = 'TRANSFER OUT' in outro_servico.servico.upper()
        
        print(f"   Base é transfer OUT: {is_base_transfer_out}")
        print(f"   Outro é transfer OUT: {is_outro_transfer_out}")
        
        if is_base_transfer_out and is_outro_transfer_out:
            is_base_regular = 'REGULAR' in servico_base.servico.upper()
            is_outro_regular = 'REGULAR' in outro_servico.servico.upper()
            
            print(f"   Base é regular: {is_base_regular}")
            print(f"   Outro é regular: {is_outro_regular}")
            
            if is_base_regular and is_outro_regular:
                mesmo_pickup = servico_base.local_pickup == outro_servico.local_pickup
                pax_total = servico_base.pax + outro_servico.pax
                
                print(f"   Mesmo pickup: {mesmo_pickup}")
                print(f"   PAX total: {pax_total}")
                print(f"   PAX >= 4: {pax_total >= 4}")
                
                if mesmo_pickup and pax_total >= 4:
                    print(f"   ✅ COMPATÍVEL (Transfer OUT Regular)")
                    compatibilidades += 1
                else:
                    print(f"   ❌ NÃO COMPATÍVEL (Transfer OUT Regular)")
            else:
                print(f"   ❌ NÃO COMPATÍVEL (Transfer OUT mas não ambos regulares)")
        else:
            # Verificar nome de serviço
            def normalizar_nome(nome):
                return nome.upper().strip()
            
            nome_base_norm = normalizar_nome(servico_base.servico)
            nome_outro_norm = normalizar_nome(outro_servico.servico)
            
            print(f"   Nome base normalizado: {nome_base_norm[:50]}...")
            print(f"   Nome outro normalizado: {nome_outro_norm[:50]}...")
            print(f"   Nomes iguais: {nome_base_norm == nome_outro_norm}")
            
            if nome_base_norm == nome_outro_norm:
                # Verificar diferença de horário
                if servico_base.horario and outro_servico.horario:
                    # Simular cálculo de diferença
                    h1 = servico_base.horario
                    h2 = outro_servico.horario
                    
                    # Converter para minutos
                    min1 = h1.hour * 60 + h1.minute
                    min2 = h2.hour * 60 + h2.minute
                    diff_min = abs(min1 - min2)
                    
                    print(f"   Diferença horário: {diff_min} minutos")
                    print(f"   Diferença <= 40min: {diff_min <= 40}")
                    
                    if diff_min <= 40:
                        print(f"   ✅ COMPATÍVEL (Mesmo serviço + horário)")
                        compatibilidades += 1
                    else:
                        print(f"   ❌ NÃO COMPATÍVEL (Diferença horário > 40min)")
                else:
                    print(f"   ❌ NÃO COMPATÍVEL (Horário faltando)")
            else:
                print(f"   ❌ NÃO COMPATÍVEL (Nomes diferentes)")
    
    print(f"\n--- RESULTADO ---")
    print(f"Compatibilidades encontradas: {compatibilidades}")
    
    if compatibilidades == 0:
        print("❌ Nenhum serviço compatível encontrado!")
        print("Isso explica por que nenhum grupo foi criado.")
    else:
        print("✅ Compatibilidades encontradas, deveria ter criado grupos.")

if __name__ == '__main__':
    debug_agrupamento()