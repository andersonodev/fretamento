#!/usr/bin/env python3
"""
Script para simular o processo de puxar dados e identificar o erro específico
"""
import os
import sys
import django
from decimal import Decimal, InvalidOperation

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.models import Servico
from escalas.models import Escala, AlocacaoVan
from datetime import date, time

def criar_servico_teste_real():
    """Cria um serviço real no banco de dados para testar"""
    print("🔧 Criando serviço de teste...")
    
    servico = Servico.objects.create(
        numero_venda="TEST001",
        cliente="Cliente Teste",
        local_pickup="Hotel Teste",
        pax=2,
        horario=time(10, 0),
        data_do_servico=date.today(),
        servico="TRANSFER IN REGULAR AEROPORTO GIG PARA ZONA SUL"
    )
    
    print(f"✅ Serviço criado: ID {servico.id}")
    return servico

def criar_escala_teste():
    """Cria uma escala de teste"""
    print("🔧 Criando escala de teste...")
    
    escala = Escala.objects.create(
        data=date.today(),
        etapa='ESTRUTURA'
    )
    
    print(f"✅ Escala criada: ID {escala.id}")
    return escala

def testar_alocacao_van():
    """Testa a criação de uma AlocacaoVan e o cálculo de preço"""
    print("\n🔍 TESTANDO ALOCAÇÃO VAN E CÁLCULO DE PREÇO")
    print("-" * 50)
    
    # Criar serviço e escala
    servico = criar_servico_teste_real()
    escala = criar_escala_teste()
    
    try:
        # Criar alocação
        print("🔧 Criando alocação...")
        alocacao = AlocacaoVan.objects.create(
            escala=escala,
            servico=servico,
            van='VAN1',
            ordem=1,
            automatica=True
        )
        
        print(f"✅ Alocação criada: ID {alocacao.id}")
        
        # Aqui é onde provavelmente está o erro
        print("🔧 Calculando preço e veículo...")
        veiculo, preco = alocacao.calcular_preco_e_veiculo()
        
        print(f"✅ Cálculo concluído: Veículo={veiculo}, Preço={preco}")
        
        # Verificar se os valores foram salvos corretamente
        alocacao.refresh_from_db()
        print(f"📊 Dados salvos:")
        print(f"   - Veículo: {alocacao.veiculo_recomendado}")
        print(f"   - Preço: {alocacao.preco_calculado} (tipo: {type(alocacao.preco_calculado)})")
        print(f"   - Lucratividade: {alocacao.lucratividade}")
        
        return True
        
    except InvalidOperation as e:
        print(f"❌ ERRO InvalidOperation: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    except Exception as e:
        print(f"❌ Outro erro: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Limpar dados de teste
        print("\n🧹 Limpando dados de teste...")
        try:
            AlocacaoVan.objects.filter(escala=escala).delete()
            escala.delete()
            servico.delete()
            print("✅ Limpeza concluída")
        except Exception as e:
            print(f"⚠️  Erro na limpeza: {e}")

def testar_varios_servicos():
    """Testa vários tipos de serviços diferentes"""
    print("\n🔍 TESTANDO VÁRIOS TIPOS DE SERVIÇOS")
    print("-" * 50)
    
    servicos_teste = [
        {
            "servico": "TRANSFER IN REGULAR AEROPORTO GIG PARA ZONA SUL",
            "pax": 2,
            "numero_venda": "1"
        },
        {
            "servico": "TRANSFER OUT REGULAR ZONA SUL PARA AEROPORTO SDU",
            "pax": 4,
            "numero_venda": "2"
        },
        {
            "servico": "TOUR PRIVATIVO RIO",
            "pax": 6,
            "numero_venda": "ABC123"
        },
        {
            "servico": "GUIA À DISPOSIÇÃO 08 HORAS",
            "pax": 8,
            "numero_venda": ""  # Teste com número de venda vazio
        },
        {
            "servico": "VEÍCULO + GUIA À DISPOSIÇÃO 06 HORAS",
            "pax": 0,  # Teste com PAX zero
            "numero_venda": None  # Teste com número de venda None
        }
    ]
    
    escala = criar_escala_teste()
    
    try:
        for i, dados in enumerate(servicos_teste):
            print(f"\n🔧 Teste {i+1}: {dados['servico'][:50]}...")
            
            # Criar serviço
            servico = Servico.objects.create(
                numero_venda=dados["numero_venda"] or f"TEST{i+1:03d}",
                cliente=f"Cliente Teste {i+1}",
                local_pickup="Hotel Teste",
                pax=dados["pax"],
                horario=time(10 + i, 0),
                data_do_servico=date.today(),
                servico=dados["servico"]
            )
            
            # Criar alocação e calcular preço
            try:
                alocacao = AlocacaoVan.objects.create(
                    escala=escala,
                    servico=servico,
                    van='VAN1',
                    ordem=i+1,
                    automatica=True
                )
                
                veiculo, preco = alocacao.calcular_preco_e_veiculo()
                print(f"   ✅ OK: Veículo={veiculo}, Preço={preco}")
                
            except Exception as e:
                print(f"   ❌ ERRO: {e}")
                
    finally:
        # Limpar todos os dados
        print("\n🧹 Limpando todos os dados de teste...")
        AlocacaoVan.objects.filter(escala=escala).delete()
        Servico.objects.filter(numero_venda__startswith="TEST").delete()
        escala.delete()

def main():
    """Função principal"""
    print("🔧 SIMULAÇÃO DO PROCESSO DE PUXAR DADOS")
    print("=" * 60)
    
    # Teste básico
    if testar_alocacao_van():
        print("\n✅ Teste básico passou")
    else:
        print("\n❌ Teste básico falhou")
    
    # Teste com vários serviços
    testar_varios_servicos()
    
    print("\n" + "=" * 60)
    print("🏁 SIMULAÇÃO CONCLUÍDA")

if __name__ == "__main__":
    main()