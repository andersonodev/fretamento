"""
Views relacionadas aos tarifários e cálculos de preços
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .tarifarios import (
    TARIFARIO_JW, TARIFARIO_MOTORISTAS, VEICULOS_DISPONIVEIS,
    buscar_preco_jw, buscar_preco_motoristas, calcular_preco_servico,
    calcular_veiculo_recomendado, gerar_chave_tarifario,
    obter_estatisticas_tarifario
)
from .models import Servico, CalculoPreco


def visualizar_tarifarios(request):
    """View para visualizar os tarifários disponíveis"""
    context = {
        'tarifario_jw': TARIFARIO_JW,
        'tarifario_motoristas': TARIFARIO_MOTORISTAS,
        'veiculos_disponiveis': VEICULOS_DISPONIVEIS,
        'estatisticas': obter_estatisticas_tarifario(),
    }
    return render(request, 'core/tarifarios.html', context)


def simulador_precos(request):
    """View para simular cálculos de preços"""
    resultado = None
    
    if request.method == 'POST':
        try:
            # Cria objeto temporário para simulação
            servico_temp = Servico(
                servico=request.POST.get('servico', ''),
                tipo=request.POST.get('tipo', 'TRANSFER'),
                aeroporto=request.POST.get('aeroporto', ''),
                regiao=request.POST.get('regiao', ''),
                pax=int(request.POST.get('pax', 1)),
                data_servico='2024-01-01',  # Data temporária
                horario='10:00'  # Horário temporário
            )
            
            # Calcula preço
            veiculo, preco = calcular_preco_servico(servico_temp)
            
            # Gera chave do tarifário
            chave_tarifario = gerar_chave_tarifario(servico_temp)
            
            resultado = {
                'servico': servico_temp,
                'veiculo_recomendado': veiculo,
                'preco_estimado': preco,
                'chave_tarifario': chave_tarifario,
                'pax': servico_temp.pax,
            }
            
            # Opcionalmente salva o cálculo no banco
            if request.POST.get('salvar_calculo'):
                CalculoPreco.objects.create(
                    chave_servico=chave_tarifario or servico_temp.servico,
                    tipo_servico=servico_temp.tipo,
                    aeroporto=servico_temp.aeroporto,
                    regiao=servico_temp.regiao,
                    pax=servico_temp.pax,
                    tipo_tarifario='AUTOMATICO',
                    veiculo_recomendado=veiculo,
                    preco_base=preco,
                    preco_final=preco,
                    custo_operacional=preco * 0.7,
                    margem=preco * 0.3,
                    rentabilidade=30.0,
                    detalhes_json={
                        'chave_tarifario': chave_tarifario,
                        'simulacao': True
                    }
                )
                messages.success(request, 'Cálculo salvo com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro no cálculo: {str(e)}')
    
    context = {
        'resultado': resultado,
        'tipos_servico': Servico.TIPO_CHOICES,
        'aeroportos': Servico.AEROPORTO_CHOICES,
        'regioes': ['ZONA SUL', 'BARRA', 'CENTRO', 'SANTOS DUMONT', 'RECREIO'],
        'veiculos_disponiveis': VEICULOS_DISPONIVEIS,
    }
    
    return render(request, 'core/simulador_precos.html', context)


@require_http_methods(["POST"])
@csrf_exempt
def api_calcular_preco(request):
    """API endpoint para calcular preços via AJAX"""
    try:
        data = json.loads(request.body)
        
        # Cria objeto temporário
        servico_temp = Servico(
            servico=data.get('servico', ''),
            tipo=data.get('tipo', 'TRANSFER'),
            aeroporto=data.get('aeroporto', ''),
            regiao=data.get('regiao', ''),
            pax=int(data.get('pax', 1)),
            data_servico='2024-01-01',
            horario='10:00'
        )
        
        # Calcula preço
        veiculo, preco = calcular_preco_servico(servico_temp)
        chave_tarifario = gerar_chave_tarifario(servico_temp)
        
        return JsonResponse({
            'success': True,
            'veiculo_recomendado': veiculo,
            'preco_estimado': preco,
            'chave_tarifario': chave_tarifario,
            'detalhes': {
                'pax': servico_temp.pax,
                'tipo_servico': servico_temp.tipo,
                'fonte_calculo': 'tarifarios_integrados'
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def buscar_preco_tarifario(request):
    """View para buscar preços específicos nos tarifários"""
    resultado = None
    
    if request.method == 'POST':
        chave_busca = request.POST.get('chave_busca', '').strip()
        tipo_tarifario = request.POST.get('tipo_tarifario', 'JW')
        veiculo = request.POST.get('veiculo', 'Executivo')
        pax = int(request.POST.get('pax', 1))
        
        if chave_busca:
            if tipo_tarifario == 'JW':
                preco = buscar_preco_jw(chave_busca, veiculo)
                fonte = 'Tarifário JW'
            else:
                preco = buscar_preco_motoristas(chave_busca, pax)
                fonte = 'Tarifário Motoristas'
            
            resultado = {
                'chave_busca': chave_busca,
                'tipo_tarifario': tipo_tarifario,
                'veiculo': veiculo,
                'pax': pax,
                'preco_encontrado': preco,
                'fonte': fonte,
                'encontrado': preco > 0
            }
            
            if preco == 0:
                messages.warning(request, f'Preço não encontrado para "{chave_busca}" no {fonte}')
            else:
                messages.success(request, f'Preço encontrado: R$ {preco:,.2f}')
    
    # Lista de chaves disponíveis para facilitar a busca
    chaves_jw = list(TARIFARIO_JW.keys())
    chaves_motoristas = list(TARIFARIO_MOTORISTAS.keys())
    
    context = {
        'resultado': resultado,
        'chaves_jw': sorted(chaves_jw),
        'chaves_motoristas': sorted(chaves_motoristas),
        'veiculos_disponiveis': VEICULOS_DISPONIVEIS,
    }
    
    return render(request, 'core/buscar_preco.html', context)


def historico_calculos(request):
    """View para exibir histórico de cálculos de preços"""
    calculos = CalculoPreco.objects.all()[:100]  # Últimos 100 cálculos
    
    # Filtros
    tipo_tarifario = request.GET.get('tipo_tarifario')
    veiculo = request.GET.get('veiculo')
    
    if tipo_tarifario:
        calculos = calculos.filter(tipo_tarifario=tipo_tarifario)
    
    if veiculo:
        calculos = calculos.filter(veiculo_recomendado=veiculo)
    
    context = {
        'calculos': calculos,
        'tipos_tarifario': CalculoPreco.TIPOS_TARIFARIO,
        'tipos_veiculo': CalculoPreco.TIPOS_VEICULO,
        'filtros_ativos': {
            'tipo_tarifario': tipo_tarifario,
            'veiculo': veiculo,
        }
    }
    
    return render(request, 'core/historico_calculos.html', context)