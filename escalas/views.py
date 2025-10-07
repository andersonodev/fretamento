from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import ListView, DetailView
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Count, Q, Sum, F
from django.db import transaction
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation
from calendar import monthrange
import re
import unicodedata
from core.models import Servico, ProcessamentoPlanilha
from escalas.models import Escala, AlocacaoVan, GrupoServico, ServicoGrupo, LogEscala
from core.processors import ProcessadorPlanilhaOS
from escalas.services import GerenciadorEscalas, ExportadorEscalas
from core.tarifarios import calcular_preco_servico
import json
import logging

logger = logging.getLogger(__name__)


def converter_para_decimal_seguro(valor, padrao=0):
    """
    Converte um valor para Decimal de forma segura
    
    Args:
        valor: Valor a ser convertido
        padrao: Valor padrão em caso de erro (default: 0)
        
    Returns:
        Decimal: Valor convertido ou valor padrão
    """
    if valor is None:
        return Decimal(str(padrao))
    
    try:
        # Converter para string e limpar
        valor_str = str(valor).strip()
        
        # Se string vazia, usar padrão
        if not valor_str:
            return Decimal(str(padrao))
        
        # Tentar converter diretamente
        return Decimal(valor_str)
        
    except (InvalidOperation, ValueError, TypeError):
        # Em caso de erro, usar o padrão
        logger.warning(f"Erro ao converter '{valor}' para Decimal. Usando padrão: {padrao}")
        return Decimal(str(padrao))
import random
import logging

logger = logging.getLogger(__name__)

# Dicionário com nomes dos meses em português
MESES_PORTUGUES = {
    1: 'Janeiro',
    2: 'Fevereiro', 
    3: 'Março',
    4: 'Abril',
    5: 'Maio',
    6: 'Junho',
    7: 'Julho',
    8: 'Agosto',
    9: 'Setembro',
    10: 'Outubro',
    11: 'Novembro',
    12: 'Dezembro'
}


def parse_data_brasileira(data_str):
    """
    Converte data do formato brasileiro (DD-MM-YYYY ou DD/MM/YYYY) ou formato ISO (YYYY-MM-DD) 
    para objeto date do Python
    """
    if not data_str:
        return None
    
    logger.debug(f"Parsing data: {data_str}")
    
    try:
        # Primeiro tenta formato brasileiro DD-MM-YYYY
        if '-' in data_str and len(data_str.split('-')[0]) <= 2:
            data_obj = datetime.strptime(data_str, '%d-%m-%Y').date()
            logger.debug(f"Formato brasileiro com hífen parseado: {data_obj}")
            return data_obj
        # Tenta formato brasileiro DD/MM/YYYY
        elif '/' in data_str and len(data_str.split('/')[0]) <= 2:
            data_obj = datetime.strptime(data_str, '%d/%m/%Y').date()
            logger.debug(f"Formato brasileiro com barra parseado: {data_obj}")
            return data_obj
        # Depois tenta formato ISO YYYY-MM-DD
        elif '-' in data_str and len(data_str.split('-')[0]) == 4:
            data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
            logger.debug(f"Formato ISO parseado: {data_obj}")
            return data_obj
        # Se nada funcionar, usa o parse_date do Django
        else:
            data_obj = parse_date(data_str)
            logger.debug(f"Django parse_date usado: {data_obj}")
            return data_obj
    except ValueError as e:
        logger.error(f"Erro ao fazer parse da data '{data_str}': {e}")
        # Fallback para parse_date do Django
        try:
            return parse_date(data_str)
        except:
            logger.error(f"Fallback também falhou para '{data_str}'")
            return None


class SelecionarAnoView(LoginRequiredMixin, View):
    """View para selecionar o ano antes de escolher o mês"""
    
    def get(self, request):
        hoje = date.today()
        ano_atual = hoje.year
        
        # Apenas anos 2025 e 2026
        anos = []
        for ano in [2025, 2026]:
            
            # Contar escalas do ano
            primeiro_dia_ano = date(ano, 1, 1)
            ultimo_dia_ano = date(ano, 12, 31)
            
            escalas_ano = Escala.objects.filter(
                data__gte=primeiro_dia_ano,
                data__lte=ultimo_dia_ano
            )
            
            # Estatísticas do ano
            total_escalas = escalas_ano.count()
            escalas_pendentes = escalas_ano.filter(status='PENDENTE').count()
            escalas_aprovadas = escalas_ano.filter(status='APROVADA').count()
            escalas_rejeitadas = escalas_ano.filter(status='REJEITADA').count()
            total_servicos = sum(e.alocacoes.count() for e in escalas_ano)
            total_valor = sum((e.total_van1_valor or 0) + (e.total_van2_valor or 0) for e in escalas_ano)
            
            # Contar meses com escalas
            meses_com_escalas = escalas_ano.values_list('data__month', flat=True).distinct().count()
            
            anos.append({
                'ano': ano,
                'eh_atual': ano == ano_atual,
                'total_escalas': total_escalas,
                'escalas_pendentes': escalas_pendentes,
                'escalas_aprovadas': escalas_aprovadas,
                'escalas_rejeitadas': escalas_rejeitadas,
                'total_servicos': total_servicos,
                'total_valor': total_valor,
                'meses_com_escalas': meses_com_escalas,
            })
        
        return render(request, 'escalas/selecionar_ano.html', {
            'anos': anos,
            'ano_atual': ano_atual
        })
    
    def post(self, request):
        """Processar criação de estrutura a partir da página de anos"""
        acao = request.POST.get('acao')
        
        if acao == 'criar_estrutura':
            data_str = request.POST.get('data')
            if data_str:
                try:
                    data = parse_date(data_str)  # date input do HTML5 usa formato YYYY-MM-DD
                    
                    # Verificar se já existe escala para esta data
                    if Escala.objects.filter(data=data).exists():
                        messages.warning(request, f'Já existe uma escala para o dia {data.strftime("%d/%m/%Y")}')
                    else:
                        # Criar nova escala
                        escala = Escala.objects.create(
                            data=data,
                            etapa='ESTRUTURA',
                            status='PENDENTE'
                        )
                        messages.success(request, f'Estrutura da escala criada para {data.strftime("%d/%m/%Y")}!')
                        
                        # Redirecionar para visualizar a escala criada
                        return redirect('escalas:visualizar_escala', data=data.strftime('%d-%m-%Y'))
                        
                except Exception as e:
                    logger.error(f"Erro ao criar escala: {e}")
                    messages.error(request, f'Erro ao criar escala: {e}')
            else:
                messages.error(request, 'Data é obrigatória')
        
        # Redirecionar de volta para a página
        return redirect('escalas:selecionar_ano')


class SelecionarMesView(LoginRequiredMixin, View):
    """View para selecionar o mês de um ano específico"""
    
    def get(self, request, ano=None):
        # Se não especificado, usar ano atual
        if not ano:
            ano = date.today().year
        else:
            ano = int(ano)
        
        hoje = date.today()
        
        # Gerar todos os 12 meses do ano
        meses = []
        for mes_numero in range(1, 13):
            mes_atual = date(ano, mes_numero, 1)
            
            # Contar escalas do mês
            primeiro_dia = date(ano, mes_numero, 1)
            ultimo_dia = date(ano, mes_numero, monthrange(ano, mes_numero)[1])
            
            escalas_mes = Escala.objects.filter(
                data__gte=primeiro_dia,
                data__lte=ultimo_dia
            )
            
            # Estatísticas do mês
            total_escalas = escalas_mes.count()
            escalas_pendentes = escalas_mes.filter(status='PENDENTE').count()
            escalas_aprovadas = escalas_mes.filter(status='APROVADA').count()
            total_servicos = sum(e.alocacoes.count() for e in escalas_mes)
            total_valor = sum((e.total_van1_valor or 0) + (e.total_van2_valor or 0) for e in escalas_mes)
            
            meses.append({
                'data': mes_atual,
                'nome': MESES_PORTUGUES[mes_numero],
                'mes_numero': mes_numero,
                'ano': ano,
                'eh_atual': mes_numero == hoje.month and ano == hoje.year,
                'total_escalas': total_escalas,
                'escalas_pendentes': escalas_pendentes,
                'escalas_aprovadas': escalas_aprovadas,
                'total_servicos': total_servicos,
                'total_valor': total_valor,
            })
        
        return render(request, 'escalas/selecionar_mes.html', {
            'meses': meses,
            'ano': ano,
            'ano_selecionado': ano,
            'mes_atual': hoje
        })
    
    def post(self, request, ano=None):
        """Processar criação de estrutura a partir da página de meses"""
        if not ano:
            ano = date.today().year
        else:
            ano = int(ano)
            
        acao = request.POST.get('acao')
        
        if acao == 'criar_estrutura':
            data_str = request.POST.get('data')
            if data_str:
                try:
                    data = parse_date(data_str)  # date input do HTML5 usa formato YYYY-MM-DD
                    
                    # Verificar se a data está no ano correto
                    if data.year != ano:
                        messages.error(request, f'A data deve ser do ano {ano}')
                    elif Escala.objects.filter(data=data).exists():
                        messages.warning(request, f'Já existe uma escala para o dia {data.strftime("%d/%m/%Y")}')
                    else:
                        # Criar nova escala
                        escala = Escala.objects.create(
                            data=data,
                            etapa='ESTRUTURA',
                            status='PENDENTE'
                        )
                        messages.success(request, f'Estrutura da escala criada para {data.strftime("%d/%m/%Y")}!')
                        
                        # Redirecionar para visualizar a escala criada
                        return redirect('escalas:visualizar_escala', data=data.strftime('%d-%m-%Y'))
                        
                except Exception as e:
                    logger.error(f"Erro ao criar escala: {e}")
                    messages.error(request, f'Erro ao criar escala: {e}')
            else:
                messages.error(request, 'Data é obrigatória')
        
        # Redirecionar de volta para a página
        return redirect('escalas:selecionar_mes_ano', ano=ano)


class GerenciarEscalasView(LoginRequiredMixin, View):
    """View para gerenciar escalas de um mês específico"""
    
    def get(self, request, mes=None, ano=None):
        # Se não especificado, usar mês atual
        if not mes or not ano:
            hoje = date.today()
            mes = hoje.month
            ano = hoje.year
        else:
            mes = int(mes)
            ano = int(ano)
        
        # Filtrar escalas do mês
        primeiro_dia = date(ano, mes, 1)
        ultimo_dia = date(ano, mes, monthrange(ano, mes)[1])
        
        # Filtrar escalas do mês com otimização de queries
        escalas = Escala.objects.filter(
            data__gte=primeiro_dia,
            data__lte=ultimo_dia
        ).select_related(
            'aprovada_por'
        ).prefetch_related(
            'alocacoes__servico',
            'grupos__servicos__alocacao__servico',
            'logs__usuario'
        ).annotate(
            total_servicos=Count('alocacoes'),
            total_pax=Sum('alocacoes__servico__pax'),
            total_valor=Sum('alocacoes__preco_calculado')
        ).order_by('-data')
        
        # Informações do mês
        mes_nome = f"{MESES_PORTUGUES[mes]} {ano}"
        
        return render(request, 'escalas/gerenciar.html', {
            'escalas': escalas,
            'mes_atual': {'numero': mes, 'ano': ano, 'nome': mes_nome},
            'mes': mes,
            'ano': ano,
            'primeiro_dia': primeiro_dia,
            'ultimo_dia': ultimo_dia
        })
    
    def post(self, request, mes=None, ano=None):
        acao = request.POST.get('acao')
        data_str = request.POST.get('data')
        
        logger.debug(f"GerenciarEscalasView POST - Acao: {acao}, Data: {data_str}, Mes: {mes}, Ano: {ano}")
        
        if not data_str:
            messages.error(request, 'Data é obrigatória.')
            if mes and ano:
                return redirect('escalas:gerenciar_escalas_mes', mes=mes, ano=ano)
            return redirect('escalas:selecionar_ano')
        
        try:
            data_alvo = parse_data_brasileira(data_str)
            
            if acao == 'criar_estrutura':
                # Etapa 1: Criar apenas a estrutura
                escala, created = Escala.objects.get_or_create(
                    data=data_alvo,
                    defaults={'etapa': 'ESTRUTURA'}
                )
                
                if created:
                    messages.success(request, f'Estrutura criada para {data_alvo.strftime("%d/%m/%Y")}! Agora você pode puxar os dados.')
                else:
                    messages.info(request, f'Estrutura para {data_alvo.strftime("%d/%m/%Y")} já existe.')
                
                return redirect('escalas:visualizar_escala', data=data_str)
                
            elif acao == 'agrupar':
                logger.debug(f"Processando ação agrupar para data: {data_alvo}")
                escala = get_object_or_404(Escala, data=data_alvo)
                logger.debug(f"Escala encontrada - ID: {escala.id}, Etapa: {escala.etapa}")
                
                if escala.etapa != 'DADOS_PUXADOS':
                    messages.error(request, 'Para agrupar, é necessário ter dados puxados.')
                    if mes and ano:
                        return redirect('escalas:gerenciar_escalas_mes', mes=mes, ano=ano)
                    return redirect('escalas:selecionar_ano')
                
                try:
                    print(f"DEBUG: Tentando agrupar serviços para escala {escala.id}")
                    grupos_criados = self._agrupar_servicos(escala)
                    print(f"DEBUG: Agrupamento retornou {grupos_criados} grupos")
                    logger.debug(f"Agrupamento concluído - Grupos criados: {grupos_criados}")
                    messages.success(request, f'Agrupamento concluído! {grupos_criados} grupos criados para {data_alvo.strftime("%d/%m/%Y")}.')
                except Exception as e:
                    print(f"DEBUG: Erro no agrupamento: {e}")
                    logger.error(f"Erro no agrupamento: {e}")
                    messages.error(request, f'Erro ao agrupar serviços: {e}')
                
                return redirect('escalas:visualizar_escala', data=data_str)
                
            elif acao in {'otimizar', 'escalar'}:
                escala = get_object_or_404(Escala, data=data_alvo)
                if escala.etapa not in ['DADOS_PUXADOS', 'OTIMIZADA']:
                    messages.error(request, 'Para escalar, é necessário ter dados puxados.')
                    if mes and ano:
                        return redirect('escalas:gerenciar_escalas_mes', mes=mes, ano=ano)
                    return redirect('escalas:selecionar_ano')
                
                # Usar a função de otimização da VisualizarEscalaView
                visualizar_view = VisualizarEscalaView()
                visualizar_view._otimizar_escala(escala)
                messages.success(request, f'Escala para {data_alvo.strftime("%d/%m/%Y")} escalada com sucesso!')
                
                return redirect('escalas:visualizar_escala', data=data_str)
                
        except Exception as e:
            logger.error(f"Erro no processamento POST: {e}")
            messages.error(request, f'Erro: {str(e)}')
        
        if mes and ano:
            return redirect('escalas:gerenciar_escalas_mes', mes=mes, ano=ano)
        return redirect('escalas:selecionar_ano')
    
    def _otimizar_escala(self, escala):
        """
        Sistema de escalar completo seguindo as regras especificadas:
        
        1. SELEÇÃO INICIAL: Selecionar todos os serviços agrupados que tenham entre 4 e 10 PAX
        2. PRIORIZAÇÃO: 
           - Serviços IN e OUT da Hotelbeds e Holiday
           - Serviços com destino à Barra da Tijuca
           - Serviços que tenham um preço alto "tours"
        3. ALOCAÇÃO INICIAL: Prioritários são distribuídos primeiro entre Van 1 e Van 2
           - Intervalo mínimo de 3 horas entre serviços
           - Tours ocupam o tempo especificado no nome (6H, 8H, 10H, etc.)
        4. AJUSTE RESTANTES: Não prioritários nos intervalos livres
        5. STATUS: Marca como 'Alocado' ou 'Não alocado'
        """
        logger.info(f"🚀 INICIANDO ESCALAR - Sistema de otimização avançado para escala {escala.id}")
        
        with transaction.atomic():
            # RESETAR TODOS OS STATUS PARA NÃO ALOCADO
            logger.info("📋 Resetando status de todas as alocações para 'Não alocado'")
            escala.alocacoes.update(status_alocacao='NAO_ALOCADO', ordem=0)
            
            # ETAPA 1: SELEÇÃO INICIAL (4-10 PAX)
            candidatos = self._selecionar_candidatos_4_10_pax(escala)
            logger.info(f"✅ ETAPA 1 - Encontrados {len(candidatos)} candidatos (4-10 PAX)")
            
            if not candidatos:
                logger.warning("⚠️ Nenhum candidato encontrado com 4-10 PAX")
                escala.etapa = 'OTIMIZADA'
                escala.save()
                return
            
            # ETAPA 2: PRIORIZAÇÃO
            prioritarios, nao_prioritarios = self._aplicar_priorizacao(candidatos)
            logger.info(f"✅ ETAPA 2 - Prioritários: {len(prioritarios)} | Não prioritários: {len(nao_prioritarios)}")
            
            # ETAPA 3: ALOCAÇÃO INICIAL NAS VANS (Prioritários)
            logger.info("🎯 ETAPA 3 - Alocando serviços prioritários...")
            van1_schedule = []  # [(horario_inicio, horario_fim)]
            van2_schedule = []
            
            alocados_prioritarios = 0
            for candidato in prioritarios:
                if self._alocar_candidato_respeitando_intervalo_3h(candidato, van1_schedule, van2_schedule):
                    alocados_prioritarios += 1
                    
            logger.info(f"✅ ETAPA 3 - {alocados_prioritarios}/{len(prioritarios)} prioritários alocados")
            
            # ETAPA 4: AJUSTE DE SERVIÇOS RESTANTES (Não prioritários)
            logger.info("🔄 ETAPA 4 - Tentando alocar não prioritários nos intervalos livres...")
            alocados_nao_prioritarios = 0
            for candidato in nao_prioritarios:
                if self._alocar_candidato_respeitando_intervalo_3h(candidato, van1_schedule, van2_schedule):
                    alocados_nao_prioritarios += 1
                    
            logger.info(f"✅ ETAPA 4 - {alocados_nao_prioritarios}/{len(nao_prioritarios)} não prioritários alocados")
            
            # ETAPA 5: PREENCHIMENTO COM SERVIÇOS PEQUENOS (1-3 PAX)
            logger.info("🔧 ETAPA 5 - Preenchendo furos com serviços de 1-3 PAX...")
            candidatos_pequenos = self._selecionar_candidatos_1_3_pax(escala)
            logger.info(f"✅ ETAPA 5 - Encontrados {len(candidatos_pequenos)} candidatos pequenos (1-3 PAX)")
            
            if candidatos_pequenos:
                # Aplicar priorização também nos serviços pequenos
                prioritarios_pequenos, nao_prioritarios_pequenos = self._aplicar_priorizacao(candidatos_pequenos)
                
                # Tentar alocar prioritários pequenos primeiro
                alocados_pequenos_prioritarios = 0
                for candidato in prioritarios_pequenos:
                    if self._alocar_candidato_respeitando_intervalo_3h(candidato, van1_schedule, van2_schedule):
                        alocados_pequenos_prioritarios += 1
                
                # Depois tentar não prioritários pequenos
                alocados_pequenos_nao_prioritarios = 0
                for candidato in nao_prioritarios_pequenos:
                    if self._alocar_candidato_respeitando_intervalo_3h(candidato, van1_schedule, van2_schedule):
                        alocados_pequenos_nao_prioritarios += 1
                
                total_pequenos_alocados = alocados_pequenos_prioritarios + alocados_pequenos_nao_prioritarios
                logger.info(f"✅ ETAPA 5 - {total_pequenos_alocados}/{len(candidatos_pequenos)} serviços pequenos alocados")
                logger.info(f"   📊 Prioritários: {alocados_pequenos_prioritarios}")
                logger.info(f"   📊 Não prioritários: {alocados_pequenos_nao_prioritarios}")
            else:
                logger.info("ℹ️ ETAPA 5 - Nenhum serviço pequeno (1-3 PAX) encontrado")
            
            # MARCAR ESCALA COMO OTIMIZADA
            escala.etapa = 'OTIMIZADA'
            escala.save()
            
            # ESTATÍSTICAS FINAIS
            total_alocados = escala.alocacoes.filter(status_alocacao='ALOCADO').count()
            total_nao_alocados = escala.alocacoes.filter(status_alocacao='NAO_ALOCADO').count()
            
            logger.info(f"🎉 ESCALAR CONCLUÍDO!")
            logger.info(f"   📊 Alocados: {total_alocados}")
            logger.info(f"   📊 Não alocados: {total_nao_alocados}")
            logger.info(f"   📊 Van 1: {escala.alocacoes.filter(status_alocacao='ALOCADO', van='VAN1').count()} serviços")
            logger.info(f"   📊 Van 2: {escala.alocacoes.filter(status_alocacao='ALOCADO', van='VAN2').count()} serviços")

    def _agrupar_servicos(self, escala):
        """Agrupa serviços compatíveis na escala"""
        print(f"DEBUG: Iniciando _agrupar_servicos para escala {escala.id}")
        grupos_criados = 0
        
        logger.debug(f"Iniciando agrupamento para escala {escala.id}")
        
        with transaction.atomic():
            # Buscar alocações que ainda não estão agrupadas
            alocacoes_disponiveis = list(
                escala.alocacoes.filter(grupo_info__isnull=True)
                .select_related('servico')
                .order_by('servico__horario', 'id')
            )

            logger.debug(
                "Encontradas %s alocações disponíveis para agrupamento",
                len(alocacoes_disponiveis)
            )

            for alocacao in alocacoes_disponiveis:
                if getattr(alocacao, 'grupo_info', None):
                    # Já foi agrupada em uma iteração anterior
                    continue

                # Buscar serviços compatíveis para agrupamento
                print(f"Analisando alocação {alocacao.id}: {alocacao.servico.cliente} - {alocacao.servico.servico}")
                servicos_compativeis, regra_agrupamento = self._encontrar_servicos_compativeis(
                    alocacao,
                    alocacoes_disponiveis
                )
                print(f"Encontrados {len(servicos_compativeis)} serviços compatíveis com regra: {regra_agrupamento}")

                if not servicos_compativeis:
                    continue

                # Criar grupo consolidado
                grupo = GrupoServico.objects.create(
                    escala=escala,
                    van=alocacao.van or 'VAN1',
                    cliente_principal=alocacao.servico.cliente,
                    servico_principal=alocacao.servico.servico,
                    local_pickup_principal=alocacao.servico.local_pickup or '',
                    ordem=alocacao.ordem,
                )

                total_pax = 0
                total_valor = Decimal('0')
                vendas = []

                for servico_alocacao in [alocacao] + servicos_compativeis:
                    ServicoGrupo.objects.create(
                        grupo=grupo,
                        alocacao=servico_alocacao
                    )

                    pax_atual = servico_alocacao.servico.pax or 0
                    total_pax += pax_atual

                    valor_atual = servico_alocacao.preco_calculado or Decimal('0')
                    total_valor += Decimal(valor_atual)

                    numero_venda = servico_alocacao.servico.numero_venda
                    if numero_venda:
                        numero_venda_str = str(numero_venda).strip()
                        if numero_venda_str.endswith('.0'):
                            numero_venda_str = numero_venda_str[:-2]
                        vendas.append(numero_venda_str)

                grupo.total_pax = total_pax
                grupo.total_valor = total_valor
                if vendas:
                    vendas_unicas = list(dict.fromkeys(vendas))
                    grupo.numeros_venda = ' / '.join(vendas_unicas)
                else:
                    grupo.numeros_venda = ''
                grupo.save()

                grupos_criados += 1

                logger.info(
                    "Grupo criado (%s): %s com %s serviços e %s PAX",
                    regra_agrupamento,
                    grupo.cliente_principal,
                    len(servicos_compativeis) + 1,
                    total_pax
                )
        
        logger.debug(f"Agrupamento finalizado. Total de grupos criados: {grupos_criados}")
        return grupos_criados
    
    def _encontrar_servicos_compativeis(self, alocacao_base, alocacoes_disponiveis):
        """Encontra serviços compatíveis para agrupamento"""
        servicos_compativeis = []
        servico_base = alocacao_base.servico
        regra_agrupamento = self._detectar_regra_agrupamento(servico_base)
        
        print(f"  Base: {servico_base.servico} | Regra: {regra_agrupamento}")

        considerar_total_pax = regra_agrupamento != 'TRANSFER_OUT_REGULAR'

        for outra_alocacao in alocacoes_disponiveis:
            if outra_alocacao.id == alocacao_base.id:
                continue
            if getattr(outra_alocacao, 'grupo_info', None):
                continue

            outro_servico = outra_alocacao.servico
            
            compativel = self._servicos_sao_compativeis(
                servico_base,
                outro_servico,
                considerar_total_pax=considerar_total_pax
            )
            
            if compativel:
                print(f"    ✅ Compatível: {outro_servico.servico}")
                servicos_compativeis.append(outra_alocacao)
            else:
                print(f"    ❌ Incompatível: {outro_servico.servico}")

        if not servicos_compativeis:
            print(f"    Nenhum serviço compatível encontrado")
            return [], regra_agrupamento

        if regra_agrupamento == 'TRANSFER_OUT_REGULAR':
            total_pax = (servico_base.pax or 0) + sum(
                outra.servico.pax or 0 for outra in servicos_compativeis
            )
            print(f"    Transfer OUT: PAX total = {total_pax}")
            if total_pax < 4:
                print(f"    PAX insuficiente para transfer OUT ({total_pax} < 4)")
                return [], regra_agrupamento

        return servicos_compativeis, regra_agrupamento

    def _servicos_sao_compativeis(self, servico1, servico2, considerar_total_pax=True):
        """Verifica se dois serviços podem ser agrupados"""
        # 1. Mesmo nome de serviço e diferença de até 40 minutos
        if self._nomes_equivalentes(servico1.servico, servico2.servico):
            if self._diferenca_horario_minutos(servico1.horario, servico2.horario) <= 40:
                return True

        # 2. Transfers OUT regulares com mesmo local de pickup
        if (
            self._eh_transfer_out_regular(servico1.servico)
            and self._eh_transfer_out_regular(servico2.servico)
            and self._mesmo_local_pickup(servico1, servico2)
            and self._diferenca_horario_minutos(servico1.horario, servico2.horario) <= 40
        ):
            total_pax = (servico1.pax or 0) + (servico2.pax or 0)
            if considerar_total_pax and total_pax < 4:
                return False
            return True

        # 3. Serviços de TOUR / GUIA À DISPOSIÇÃO (qualquer variação)
        if (
            self._eh_servico_tour_equivalente(servico1.servico)
            and self._eh_servico_tour_equivalente(servico2.servico)
            and self._diferenca_horario_minutos(servico1.horario, servico2.horario) <= 40
        ):
            return True

        return False

    def _normalizar_nome_servico(self, nome):
        """Normaliza nome do serviço para comparação"""
        import re

        nome_normalizado = self._remover_acentos(nome).upper().strip()
        
        # 1. Normalizar espaços múltiplos
        nome_normalizado = re.sub(r'\s+', ' ', nome_normalizado)
        
        # 2. Normalizar códigos de aeroportos
        nome_normalizado = re.sub(r'RJ\s*\(GIG\)', 'GIG', nome_normalizado)
        nome_normalizado = re.sub(r'RJ\s*\(SDU\)', 'SDU', nome_normalizado)
        nome_normalizado = re.sub(r'\(GIG\)', 'GIG', nome_normalizado)
        nome_normalizado = re.sub(r'\(SDU\)', 'SDU', nome_normalizado)
        
        # 3. Normalizar aeroportos
        nome_normalizado = re.sub(r'AEROPORTO\s+INTER\.\s+GALEÃO', 'AEROPORTO GALEAO', nome_normalizado)
        nome_normalizado = re.sub(r'AEROPORTO\s+SANTOS\s+DUMONT', 'AEROPORTO SDU', nome_normalizado)
        
        # 4. Remover pontuações desnecessárias
        nome_normalizado = re.sub(r'[,\.](?!\d)', '', nome_normalizado)
        nome_normalizado = re.sub(r'\s+', ' ', nome_normalizado)  # Limpar espaços novamente
        
        # 5. Normalizar variações específicas comuns
        nome_normalizado = re.sub(r'TRANSFER\s+IN\s+REGULAR', 'TRANSFER IN REGULAR', nome_normalizado)
        nome_normalizado = re.sub(r'TRANSFER\s+OUT\s+REGULAR', 'TRANSFER OUT REGULAR', nome_normalizado)
        nome_normalizado = re.sub(r'TRANSFER\s+IN\s+VEÍCULO\s+PRIVATIVO', 'TRANSFER IN PRIVATIVO', nome_normalizado)
        nome_normalizado = re.sub(r'TRANSFER\s+OUT\s+VEÍCULO\s+PRIVATIVO', 'TRANSFER OUT PRIVATIVO', nome_normalizado)
        
        return nome_normalizado.strip()

    def _nomes_equivalentes(self, nome1, nome2):
        """Compara nomes de serviço considerando normalização"""
        return self._normalizar_nome_servico(nome1) == self._normalizar_nome_servico(nome2)

    def _detectar_regra_agrupamento(self, servico):
        """Define qual regra de agrupamento aplicar para o serviço base"""
        if self._eh_transfer_out_regular(servico.servico):
            return 'TRANSFER_OUT_REGULAR'
        if self._eh_servico_tour_equivalente(servico.servico):
            return 'TOUR'
        return 'NOME'

    def _remover_acentos(self, texto):
        """Remove acentos para comparações resilientes"""
        if not texto:
            return ''
        if isinstance(texto, str):
            texto_normalizado = unicodedata.normalize('NFKD', texto)
            return ''.join(c for c in texto_normalizado if not unicodedata.combining(c))
        return str(texto)

    def _mesmo_local_pickup(self, servico1, servico2):
        """Compara o local de pickup considerando normalização"""
        pickup1 = self._remover_acentos(getattr(servico1, 'local_pickup', '')).strip().upper()
        pickup2 = self._remover_acentos(getattr(servico2, 'local_pickup', '')).strip().upper()
        if not pickup1 or not pickup2:
            return False
        return pickup1 == pickup2
    def _diferenca_horario_minutos(self, horario1, horario2):
        """Calcula diferença em minutos entre dois horários"""
        if not horario1 or not horario2:
            return float('inf')
        
        # Se forem strings, converter para datetime
        if isinstance(horario1, str):
            horario1 = datetime.strptime(horario1, '%H:%M').time()
        if isinstance(horario2, str):
            horario2 = datetime.strptime(horario2, '%H:%M').time()
            
        # Converter time para datetime para cálculo
        data_base = date.today()
        dt1 = datetime.combine(data_base, horario1)
        dt2 = datetime.combine(data_base, horario2)
        
        diferenca = abs((dt2 - dt1).total_seconds() / 60)
        return diferenca
    
    def _eh_transfer_out(self, nome_servico):
        """Verifica se é um transfer OUT"""
        nome_upper = self._remover_acentos(nome_servico).upper()
        return 'TRANSFER' in nome_upper and 'OUT' in nome_upper

    def _eh_transfer_out_regular(self, nome_servico):
        """Identifica transfers OUT regulares"""
        nome_upper = self._remover_acentos(nome_servico).upper()
        return 'TRANSFER' in nome_upper and 'OUT' in nome_upper and 'REGULAR' in nome_upper

    def _eh_servico_tour_equivalente(self, nome_servico):
        """Verifica se o nome indica um tour ou guia à disposição"""
        nome_upper = self._remover_acentos(nome_servico).upper()
        palavras_chave = [
            'TOUR',
            'GUIA A DISPOSICAO',
            'VEICULO + GUIA',
            'VEICULO E GUIA',
        ]
        return any(chave in nome_upper for chave in palavras_chave)

    def _eh_tour(self, nome_servico):
        """Mantido para compatibilidade com testes anteriores"""
        return self._eh_servico_tour_equivalente(nome_servico)

    def _eh_guia_disposicao(self, nome_servico):
        """Verifica se é um serviço de guia à disposição"""
        nome_upper = self._remover_acentos(nome_servico).upper()
        padrao = r'GUIA\s*A\s*DISPOSICAO\s*\d+\s*HORAS?'
        return bool(re.search(padrao, nome_upper))
    
    def _selecionar_candidatos_4_10_pax(self, escala):
        """
        ETAPA 1: Selecionar todos os serviços agrupados que tenham entre 4 e 10 PAX
        """
        candidatos = []
        alocacoes_processadas = set()
        
        # Primeiro: processar grupos (prioridade sobre individuais)
        grupos = escala.grupos.all()
        for grupo in grupos:
            if 4 <= grupo.total_pax <= 10:
                alocacoes_grupo = [sg.alocacao for sg in grupo.servicos.all()]
                candidatos.append({
                    'tipo': 'grupo',
                    'grupo': grupo,
                    'alocacoes': alocacoes_grupo,
                    'pax_total': grupo.total_pax,
                    'horario_principal': self._obter_horario_mais_cedo(alocacoes_grupo),
                    'cliente_principal': grupo.cliente_principal,
                    'servico_principal': grupo.servico_principal,
                    'eh_in_out': self._verificar_servico_in_out(grupo.servico_principal)
                })
                
                # Marcar alocações como processadas
                for alocacao in alocacoes_grupo:
                    alocacoes_processadas.add(alocacao.id)
        
        # Segundo: processar serviços individuais não agrupados
        alocacoes_individuais = escala.alocacoes.filter(grupo_info__isnull=True)
        for alocacao in alocacoes_individuais:
            if (alocacao.id not in alocacoes_processadas and 
                4 <= alocacao.servico.pax <= 10):
                candidatos.append({
                    'tipo': 'individual',
                    'grupo': None,
                    'alocacoes': [alocacao],
                    'pax_total': alocacao.servico.pax,
                    'horario_principal': alocacao.servico.horario,
                    'cliente_principal': alocacao.servico.cliente,
                    'servico_principal': alocacao.servico.servico,
                    'eh_in_out': self._verificar_servico_in_out(alocacao.servico.servico)
                })
        
        return candidatos
    
    def _selecionar_candidatos_1_3_pax(self, escala):
        """
        ETAPA 5: Selecionar todos os serviços agrupados que tenham entre 1 e 3 PAX
        para preencher os "furos" nas vans após a alocação principal
        """
        candidatos = []
        alocacoes_processadas = set()
        
        logger.debug(f"🔍 Buscando candidatos 1-3 PAX...")
        
        # Primeiro: processar grupos pequenos
        grupos = escala.grupos.all()
        for grupo in grupos:
            if 1 <= grupo.total_pax <= 3:
                alocacoes_grupo = [sg.alocacao for sg in grupo.servicos.all()]
                
                # Verificar se já não estão alocadas
                if not any(alocacao.status_alocacao == 'ALOCADO' for alocacao in alocacoes_grupo):
                    candidatos.append({
                        'tipo': 'grupo',
                        'grupo': grupo,
                        'alocacoes': alocacoes_grupo,
                        'pax_total': grupo.total_pax,
                        'horario_principal': self._obter_horario_mais_cedo(alocacoes_grupo),
                        'cliente_principal': grupo.cliente_principal,
                        'servico_principal': grupo.servico_principal,
                        'eh_in_out': self._verificar_servico_in_out(grupo.servico_principal)
                    })
                    
                    # Marcar alocações como processadas
                    for alocacao in alocacoes_grupo:
                        alocacoes_processadas.add(alocacao.id)
        
        # Segundo: processar serviços individuais pequenos não agrupados
        alocacoes_individuais = escala.alocacoes.filter(grupo_info__isnull=True)
        for alocacao in alocacoes_individuais:
            if (alocacao.id not in alocacoes_processadas and 
                1 <= alocacao.servico.pax <= 3 and
                alocacao.status_alocacao != 'ALOCADO'):
                candidatos.append({
                    'tipo': 'individual',
                    'grupo': None,
                    'alocacoes': [alocacao],
                    'pax_total': alocacao.servico.pax,
                    'horario_principal': alocacao.servico.horario,
                    'cliente_principal': alocacao.servico.cliente,
                    'servico_principal': alocacao.servico.servico,
                    'eh_in_out': self._verificar_servico_in_out(alocacao.servico.servico)
                })
        
        logger.debug(f"✅ Encontrados {len(candidatos)} candidatos 1-3 PAX")
        return candidatos
    
    def _obter_horario_mais_cedo(self, alocacoes):
        """Obtém o horário mais cedo de uma lista de alocações"""
        horarios = []
        for alocacao in alocacoes:
            if alocacao.servico.horario:
                horarios.append(alocacao.servico.horario)
        return min(horarios) if horarios else None
    
    def _verificar_servico_in_out(self, nome_servico):
        """Verifica se é serviço IN ou OUT"""
        nome_upper = nome_servico.upper()
        return ('TRANSFER' in nome_upper and ('IN' in nome_upper or 'OUT' in nome_upper))
    
    def _aplicar_priorizacao(self, candidatos):
        """
        ETAPA 2: Dentro desse conjunto, dar prioridade para:
        - Serviços IN e OUT da Hotelbeds e Holiday
        - Serviços com destino à Barra da Tijuca  
        - Serviços que tenham um preço alto "tours"
        """
        for candidato in candidatos:
            score = self._calcular_score_prioridade_negocio(candidato)
            candidato['score_prioridade'] = score
        
        # Separar em prioritários (score > 0) e não prioritários
        prioritarios = [c for c in candidatos if c['score_prioridade'] > 0]
        nao_prioritarios = [c for c in candidatos if c['score_prioridade'] == 0]
        
        # Ordenar prioritários por score (maior primeiro)
        prioritarios.sort(key=lambda x: x['score_prioridade'], reverse=True)
        
        # Ordenar não prioritários por horário (mais cedo primeiro)
        nao_prioritarios.sort(key=lambda x: x['horario_principal'] or timezone.time(23, 59))
        
        return prioritarios, nao_prioritarios
    
    def _calcular_score_prioridade_negocio(self, candidato):
        """
        Calcula score de prioridade baseado nas regras de negócio:
        - Hotelbeds e Holiday: +100 pontos
        - Barra da Tijuca: +50 pontos  
        - Tours: +75 pontos
        """
        score = 0
        cliente = candidato['cliente_principal'].upper()
        servico = candidato['servico_principal'].upper()
        
        # PRIORIDADE 1: Serviços IN e OUT da Hotelbeds e Holiday
        if candidato['eh_in_out']:
            if 'HOTELBEDS' in cliente or 'HOLIDAY' in cliente:
                score += 100
                logger.debug(f"   🏆 Hotelbeds/Holiday IN/OUT: {candidato['cliente_principal']} (+100)")
        
        # PRIORIDADE 2: Serviços com destino à Barra da Tijuca
        if 'BARRA' in servico or 'BARRA DA TIJUCA' in servico or 'RECREIO' in servico:
            score += 50
            logger.debug(f"   🏖️ Destino Barra: {candidato['servico_principal'][:50]}... (+50)")
        
        # PRIORIDADE 3: Serviços que tenham preço alto "tours"
        if self._eh_tour_alto_valor(servico):
            score += 75
            logger.debug(f"   🎯 Tour alto valor: {candidato['servico_principal'][:50]}... (+75)")
        
        # Bonus menor por PAX (desempate)
        score += candidato['pax_total'] * 1
        
        return score
    
    def _eh_tour_alto_valor(self, nome_servico):
        """Verifica se é um tour de alto valor"""
        nome_upper = nome_servico.upper()
        return (
            'TOUR' in nome_upper or 
            'VEÍCULO + GUIA À DISPOSIÇÃO' in nome_upper or
            'VEICULO + GUIA A DISPOSICAO' in nome_upper or
            'GUIA À DISPOSIÇÃO' in nome_upper or
            'GUIA A DISPOSICAO' in nome_upper
        )
    
    def _alocar_candidato_respeitando_intervalo_3h(self, candidato, van1_schedule, van2_schedule):
        """
        ETAPA 3 & 4: Alocação nas vans respeitando:
        - Intervalo mínimo de 3 horas
        - Tours ocupam toda sua duração especificada
        """
        horario_inicio = candidato['horario_principal']
        
        if not horario_inicio:
            logger.debug(f"   ⚠️ {candidato['cliente_principal']} - sem horário, não alocado")
            return False
        
        # Calcular duração baseada no tipo de serviço
        duracao_minutos = self._calcular_duracao_ocupacao_van(candidato['servico_principal'])
        horario_fim = self._somar_minutos_ao_horario(horario_inicio, duracao_minutos)
        
        logger.debug(f"   🕐 {candidato['cliente_principal']} - {horario_inicio} a {horario_fim} ({duracao_minutos}min)")
        
        # Tentar Van 1 primeiro
        if self._van_pode_aceitar_servico(horario_inicio, horario_fim, van1_schedule):
            self._confirmar_alocacao_na_van(candidato, 'VAN1', van1_schedule, horario_inicio, horario_fim)
            return True
        
        # Tentar Van 2
        elif self._van_pode_aceitar_servico(horario_inicio, horario_fim, van2_schedule):
            self._confirmar_alocacao_na_van(candidato, 'VAN2', van2_schedule, horario_inicio, horario_fim)
            return True
        
        # Não conseguiu alocar em nenhuma van
        logger.debug(f"   ❌ {candidato['cliente_principal']} - não coube em nenhuma van")
        return False
    
    def _calcular_duracao_ocupacao_van(self, nome_servico):
        """
        Calcula quantos minutos a van ficará ocupada.
        Tours especiais: conforme especificado no nome (6H, 8H, 10H)
        Outros serviços: 3 horas padrão
        """
        nome_upper = nome_servico.upper()
        
        # Buscar padrões de horas nos tours
        import re
        
        # Padrão: "VEÍCULO + GUIA À DISPOSIÇÃO 06 HORAS"
        match = re.search(r'(\d+)\s*HORAS?', nome_upper)
        if match:
            horas = int(match.group(1))
            logger.debug(f"     ⏱️ Tour de {horas} horas detectado")
            return horas * 60
        
        # Padrão: "GUIA À DISPOSIÇÃO 08 HORAS"  
        match = re.search(r'GUIA.*DISPOSIÇÃO.*(\d+)\s*HORAS?', nome_upper)
        if match:
            horas = int(match.group(1))
            logger.debug(f"     ⏱️ Guia {horas} horas detectado")
            return horas * 60
        
        # Padrão: "DISPOSIÇÃO 10H" ou variações
        match = re.search(r'DISPOSIÇÃO.*(\d+)H', nome_upper)
        if match:
            horas = int(match.group(1))
            logger.debug(f"     ⏱️ Disposição {horas}H detectado")
            return horas * 60
        
        # Transfers e outros: 3 horas padrão
        logger.debug(f"     ⏱️ Serviço padrão: 3 horas")
        return 180  # 3 horas = 180 minutos
    
    def _somar_minutos_ao_horario(self, horario, minutos):
        """Adiciona minutos a um horário"""
        from datetime import datetime, timedelta
        dt = datetime.combine(datetime.today(), horario)
        dt_fim = dt + timedelta(minutes=minutos)
        return dt_fim.time()
    
    def _van_pode_aceitar_servico(self, inicio, fim, schedule_van):
        """
        Verifica se a van pode aceitar o serviço:
        - Não pode haver sobreposição
        - Deve ter 3 horas de intervalo após o último serviço
        """
        INTERVALO_MINIMO_MINUTOS = 180  # 3 horas
        
        for agendado_inicio, agendado_fim in schedule_van:
            # Verificar sobreposição
            if not (fim <= agendado_inicio or inicio >= agendado_fim):
                logger.debug(f"     ❌ Conflito de horário: {inicio}-{fim} vs {agendado_inicio}-{agendado_fim}")
                return False
            
            # Verificar intervalo mínimo (3 horas após o fim do último)
            if agendado_fim <= inicio:
                diferenca_minutos = self._calcular_diferenca_minutos(agendado_fim, inicio)
                if diferenca_minutos < INTERVALO_MINIMO_MINUTOS:
                    logger.debug(f"     ❌ Intervalo insuficiente: {diferenca_minutos}min < 180min")
                    return False
        
        return True
    
    def _calcular_diferenca_minutos(self, horario1, horario2):
        """Calcula diferença em minutos entre dois horários"""
        from datetime import datetime, timedelta
        
        dt1 = datetime.combine(datetime.today(), horario1)
        dt2 = datetime.combine(datetime.today(), horario2)
        
        # Lidar com horários que passam da meia-noite
        if dt2 < dt1:
            dt2 += timedelta(days=1)
        
        return (dt2 - dt1).total_seconds() / 60
    
    def _confirmar_alocacao_na_van(self, candidato, van_nome, schedule_van, horario_inicio, horario_fim):
        """Confirma alocação do candidato na van especificada"""
        # Adicionar ao schedule da van
        schedule_van.append((horario_inicio, horario_fim))
        schedule_van.sort()
        
        # Marcar todas as alocações do candidato como alocadas
        ordem = len([s for s in schedule_van if s[0] <= horario_inicio])
        
        for alocacao in candidato['alocacoes']:
            alocacao.status_alocacao = 'ALOCADO'
            alocacao.van = van_nome
            alocacao.ordem = ordem
            alocacao.save()
        
        logger.info(f"✅ ALOCADO: {candidato['cliente_principal']} ({candidato['pax_total']} PAX) -> {van_nome} #{ordem}")


class FormatarEscalaView(LoginRequiredMixin, View):
    """View para formatação de escala com autenticação por senha"""
    
    def post(self, request):
        data_str = request.POST.get('data')
        senha = request.POST.get('senha')
        
        if not data_str:
            messages.error(request, 'Data é obrigatória.')
            return redirect('escalas:selecionar_ano')
        
        if not senha:
            messages.error(request, 'Senha é obrigatória para formatar escala.')
            return redirect('escalas:visualizar_escala', data=data_str)
        
        try:
            data_alvo = parse_data_brasileira(data_str)
            escala = get_object_or_404(Escala, data=data_alvo)
            
            # Verificar senha do usuário
            from django.contrib.auth import authenticate
            user = authenticate(username=request.user.username, password=senha)
            
            if not user:
                # Log de tentativa de acesso negado
                logger.warning(
                    f'FORMATAÇÃO NEGADA - Senha incorreta | '
                    f'Usuário: {request.user.username} | '
                    f'Data: {data_alvo.strftime("%d/%m/%Y") if "data_alvo" in locals() else data_str} | '
                    f'IP: {self._get_client_ip(request)} | '
                    f'Timestamp: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}'
                )
                messages.error(request, 'Senha incorreta. Formatação não autorizada.')
                return redirect('escalas:visualizar_escala', data=data_str)
            
            # Obter IP do usuário
            ip_address = self._get_client_ip(request)
            
            # Log de início da formatação
            logger.warning(
                f'FORMATAÇÃO INICIADA | '
                f'Usuário: {request.user.username} | '
                f'Data: {data_alvo.strftime("%d/%m/%Y")} | '
                f'IP: {ip_address} | '
                f'Timestamp: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}'
            )
            
            # Salvar estado antes da formatação
            dados_antes = {
                'total_alocacoes': escala.alocacoes.count(),
                'total_van1': escala.alocacoes.filter(van='VAN1').count(),
                'total_van2': escala.alocacoes.filter(van='VAN2').count(),
                'total_grupos': escala.grupos.count(),
                'alocacoes_com_preco': escala.alocacoes.filter(preco_calculado__isnull=False).count(),
                'etapa': escala.etapa,
                'status': escala.status,
            }
            
            # === FORMATAÇÃO NÃO DESTRUTIVA ===
            # 1. Desfazer todos os grupos (mas manter alocações individuais)
            grupos_removidos = 0
            for grupo in escala.grupos.all():
                # Contar serviços no grupo antes de deletar
                servicos_no_grupo = grupo.servicos.count()
                grupos_removidos += 1
                # Deletar o grupo automaticamente remove os ServicoGrupo relacionados
                grupo.delete()
            
            # 2. Desprecificar todas as alocações
            alocacoes_desprecificadas = 0
            for alocacao in escala.alocacoes.all():
                if alocacao.preco_calculado is not None or alocacao.veiculo_recomendado:
                    logger.info(f"Desprecificando alocação {alocacao.id}: preço={alocacao.preco_calculado}, veículo={alocacao.veiculo_recomendado}")
                    alocacao.preco_calculado = None
                    alocacao.veiculo_recomendado = None
                    alocacao.lucratividade = None
                    alocacao.detalhes_precificacao = None
                    alocacao.save()
                    alocacoes_desprecificadas += 1
            
            logger.info(f"Total de alocações desprecificadas: {alocacoes_desprecificadas}")
            
            # 3. Resetar etapa da escala para DADOS_PUXADOS (desfazer otimização)
            escala.etapa = 'DADOS_PUXADOS'
            escala.save()
            
            # Forçar atualização do cache do objeto
            escala.refresh_from_db()
            
            # Salvar estado após formatação
            dados_depois = {
                'total_alocacoes': escala.alocacoes.count(),  # Deve ser igual ao anterior
                'total_van1': escala.alocacoes.filter(van='VAN1').count(),
                'total_van2': escala.alocacoes.filter(van='VAN2').count(),
                'total_grupos': 0,  # Todos os grupos foram removidos
                'alocacoes_com_preco': 0,  # Todas foram desprecificadas
                'etapa': escala.etapa,
                'status': escala.status,
                'grupos_removidos': grupos_removidos,
                'alocacoes_desprecificadas': alocacoes_desprecificadas,
            }
            
            # Registrar no log
            LogEscala.objects.create(
                escala=escala,
                acao='FORMATAR',
                usuario=request.user,
                ip_address=ip_address,
                descricao=f'Escala formatada - {grupos_removidos} grupos removidos, {alocacoes_desprecificadas} alocações desprecificadas (dados mantidos)',
                dados_antes=dados_antes,
                dados_depois=dados_depois
            )
            
            # Log de aplicação detalhado
            logger.warning(
                f'FORMATAÇÃO CONCLUÍDA | '
                f'Usuário: {request.user.username} ({request.user.get_full_name() or request.user.username}) | '
                f'Data Escala: {data_alvo.strftime("%d/%m/%Y")} | '
                f'IP: {ip_address} | '
                f'Timestamp: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")} | '
                f'Grupos removidos: {grupos_removidos} | '
                f'Alocações desprecificadas: {alocacoes_desprecificadas} | '
                f'Total alocações: {escala.alocacoes.count()} | '
                f'Etapa anterior: {dados_antes.get("etapa")} → Nova etapa: {escala.etapa} | '
                f'Status: {escala.status}'
            )
            
            # Limpar qualquer cache relacionado
            from django.core.cache import cache
            cache.clear()
            
            messages.success(
                request, 
                f'Escala de {data_alvo.strftime("%d/%m/%Y")} formatada com sucesso! '
                f'{grupos_removidos} grupos removidos, {alocacoes_desprecificadas} alocações desprecificadas. '
                f'Os dados dos serviços foram mantidos. A escala pode agora ser reagrupada e reotimizada.'
            )
            
        except Exception as e:
            # Log detalhado do erro
            logger.error(
                f'ERRO NA FORMATAÇÃO | '
                f'Usuário: {request.user.username} | '
                f'Data: {data_str} | '
                f'IP: {self._get_client_ip(request)} | '
                f'Timestamp: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")} | '
                f'Erro: {str(e)} | '
                f'Tipo: {type(e).__name__}'
            )
            messages.error(request, f'Erro ao formatar escala: {str(e)}')
        
        return redirect('escalas:visualizar_escala', data=data_str)
    
    def _get_client_ip(self, request):
        """Obtém o IP do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    

class VisualizarEscalaView(LoginRequiredMixin, View):
    """View para visualizar uma escala específica"""
    
    template_name = 'escalas/visualizar.html'
    
    def get_object(self):
        data_str = self.kwargs.get('data')
        data = parse_data_brasileira(data_str)
        return get_object_or_404(
            Escala.objects.select_related(
                'aprovada_por'
            ).prefetch_related(
                'alocacoes__servico',
                'alocacoes__grupo_info__grupo__servicos__alocacao__servico',
                'grupos__servicos__alocacao__servico',
                'logs__usuario'
            ),
            data=data
        )

    def get(self, request, data):
        """Exibe a escala"""
        import sys
        print(f"🟢 GET CHAMADO! VisualizarEscalaView - Data: {data}", file=sys.stderr)
        
        escala = self.get_object()
        context = self.get_context_data(escala=escala)
        return render(request, self.template_name, context)
    
    def get_context_data(self, **kwargs):
        escala = kwargs.get('escala')
        context = {}
        
        # Adicionar ano e mês da escala para navegação
        context['escala'] = escala
        context['ano'] = escala.data.year
        context['mes'] = escala.data.month
        
        # Obter todas as alocações com otimização de queries - ordenar por status de alocação primeiro
        # ALOCADO vem antes de NAO_ALOCADO (ordenação ascendente alfabética)
        all_van1_alocacoes = escala.alocacoes.filter(van='VAN1').select_related(
            'servico', 
            'escala__aprovada_por'
        ).prefetch_related(
            'grupo_info__grupo__servicos__alocacao__servico'
        ).order_by('status_alocacao', 'ordem')
        
        all_van2_alocacoes = escala.alocacoes.filter(van='VAN2').select_related(
            'servico', 
            'escala__aprovada_por'
        ).prefetch_related(
            'grupo_info__grupo__servicos__alocacao__servico'
        ).order_by('status_alocacao', 'ordem')
        
        # Filtrar para mostrar apenas um representante por grupo
        def get_unique_alocacoes(alocacoes):
            """Retorna apenas um representante por grupo + alocações não agrupadas"""
            grupos_vistos = set()
            alocacoes_unicas = []
            
            for alocacao in alocacoes:
                try:
                    # Se tem grupo_info, verificar se já mostramos este grupo
                    grupo_id = alocacao.grupo_info.grupo.id
                    if grupo_id not in grupos_vistos:
                        grupos_vistos.add(grupo_id)
                        alocacoes_unicas.append(alocacao)
                except:
                    # Se não tem grupo_info, é uma alocação individual
                    alocacoes_unicas.append(alocacao)
            
            return alocacoes_unicas
        
        # Obter alocações únicas (representantes de grupos)
        van1_alocacoes_unicas = get_unique_alocacoes(all_van1_alocacoes)
        van2_alocacoes_unicas = get_unique_alocacoes(all_van2_alocacoes)
        
        # Dados da Van 1
        van1_data = {
            'servicos': van1_alocacoes_unicas,  # Usar alocações únicas
            'total_pax': sum(a.servico.pax for a in all_van1_alocacoes),  # Totais baseados em todas
            'total_valor': sum(a.preco_calculado or 0 for a in all_van1_alocacoes),
            'count': all_van1_alocacoes.count()
        }
        
        # Dados da Van 2
        van2_data = {
            'servicos': van2_alocacoes_unicas,  # Usar alocações únicas
            'total_pax': sum(a.servico.pax for a in all_van2_alocacoes),  # Totais baseados em todas
            'total_valor': sum(a.preco_calculado or 0 for a in all_van2_alocacoes),
            'count': all_van2_alocacoes.count()
        }
        
        # Informações sobre grupos com otimização
        grupos_van1 = escala.grupos.filter(van='VAN1').select_related().prefetch_related(
            'servicos__alocacao__servico'
        ).order_by('ordem')
        grupos_van2 = escala.grupos.filter(van='VAN2').select_related().prefetch_related(
            'servicos__alocacao__servico'
        ).order_by('ordem')
        
        # Adicionar data formatada para JavaScript
        data_str = self.kwargs.get('data')
        
        context.update({
            'van1': van1_data,
            'van2': van2_data,
            'grupos_van1': grupos_van1,
            'grupos_van2': grupos_van2,
            'total_servicos': all_van1_alocacoes.count() + all_van2_alocacoes.count(),
            'data': data_str,  # Adicionar data formatada
        })
        
        return context

    def post(self, request, data):
        """Processa ações do botão Agrupar e Otimizar"""
        import sys
        print(f"\n" + "="*60, file=sys.stderr)
        print(f"🔥 POST CHAMADO! VisualizarEscalaView", file=sys.stderr)
        print(f"🔥 Data: {data}", file=sys.stderr)
        print(f"🔥 Método: {request.method}", file=sys.stderr)
        print(f"🔥 User: {request.user}", file=sys.stderr)
        print(f"🔥 POST keys: {list(request.POST.keys())}", file=sys.stderr)
        print(f"🔥 POST items: {dict(request.POST.items())}", file=sys.stderr)
        print("="*60, file=sys.stderr)
        
        print(f"\n=== DEBUG POST VisualizarEscalaView ===")
        print(f"Data recebida: {data}")
        print(f"Método: {request.method}")
        print(f"POST keys: {list(request.POST.keys())}")
        print(f"POST items: {dict(request.POST.items())}")
        
        # Verificar se há parâmetro acao
        acao = request.POST.get('acao')
        print(f"Parâmetro 'acao': '{acao}'")
        
        if not acao:
            print("ERRO: Parâmetro 'acao' não encontrado!")
            messages.error(request, 'Ação não especificada.')
            return redirect('escalas:visualizar_escala', data=data)
        
        escala = self.get_object()
        print(f"Escala ID: {escala.id}, Etapa: {escala.etapa}")
        
        # Log detalhado das alocações
        total_alocacoes = escala.alocacoes.count()
        alocacoes_sem_grupo = escala.alocacoes.filter(grupo_info__isnull=True).count()
        print(f"Total alocações: {total_alocacoes}, Sem grupo: {alocacoes_sem_grupo}")
        
        if acao == 'agrupar':
            print("=== PROCESSANDO AGRUPAMENTO ===")
            print(f"Etapa da escala: '{escala.etapa}'")
            print(f"Etapas válidas: ['DADOS_PUXADOS', 'OTIMIZADA']")
            print(f"Etapa é válida? {escala.etapa in ['DADOS_PUXADOS', 'OTIMIZADA']}")
            
            if escala.etapa not in ['DADOS_PUXADOS', 'OTIMIZADA']:
                error_msg = f'Para agrupar, é necessário ter dados puxados ou estar otimizada. Etapa atual: {escala.etapa}'
                print(f"ERRO ETAPA: {error_msg}")
                messages.error(request, error_msg)
                return redirect('escalas:visualizar_escala', data=data)

            if alocacoes_sem_grupo == 0:
                print("AVISO: Não há alocações disponíveis para agrupamento")
                messages.warning(request, 'Não há serviços disponíveis para agrupamento.')
                return redirect('escalas:visualizar_escala', data=data)

            try:
                print(f"Iniciando agrupamento com {alocacoes_sem_grupo} alocações disponíveis...")
                gerenciar_view = GerenciarEscalasView()
                grupos_criados = gerenciar_view._agrupar_servicos(escala)
                print(f"Agrupamento concluído: {grupos_criados} grupos criados")
                if grupos_criados > 0:
                    messages.success(request, f'Agrupamento concluído! {grupos_criados} grupos criados.')
                else:
                    messages.info(request, 'Nenhum grupo foi criado. Verifique se há serviços compatíveis para agrupamento.')
            except Exception as e:
                print(f"ERRO no agrupamento: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'Erro ao agrupar serviços: {e}')

            return redirect('escalas:visualizar_escala', data=data)

        elif acao == 'teste':
            print("=== TESTE EXECUTADO COM SUCESSO ===")
            messages.success(request, '🔥 TESTE: Botão funcionando perfeitamente!')
            return redirect('escalas:visualizar_escala', data=data)
            
        elif acao == 'debug':
            print("=== DEBUG EXECUTADO COM SUCESSO ===")
            messages.info(request, '🛠️ DEBUG: Formulário com input hidden funcionando!')
            return redirect('escalas:visualizar_escala', data=data)

        elif acao in {'otimizar', 'escalar'}:
            print("=== PROCESSANDO ESCALONAMENTO ===")
            print(f"Etapa da escala: '{escala.etapa}'")
            print(f"Etapas válidas: ['DADOS_PUXADOS', 'OTIMIZADA']")
            print(f"Etapa é válida? {escala.etapa in ['DADOS_PUXADOS', 'OTIMIZADA']}")
            
            if escala.etapa not in ['DADOS_PUXADOS', 'OTIMIZADA']:
                error_msg = f'Para escalar, é necessário ter dados puxados. Etapa atual: {escala.etapa}'
                print(f"ERRO ETAPA: {error_msg}")
                messages.error(request, error_msg)
                return redirect('escalas:visualizar_escala', data=data)

            try:
                print(f"Iniciando escalonamento/otimização da escala {escala.id}...")
                gerenciar_view = GerenciarEscalasView()
                gerenciar_view._otimizar_escala(escala)
                print("Escalonamento concluído com sucesso")
                messages.success(request, 'Escala escalada com sucesso!')
            except Exception as e:
                print(f"ERRO no escalonamento: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'Erro ao escalar: {e}')

            return redirect('escalas:visualizar_escala', data=data)

        else:
            print(f"AÇÃO DESCONHECIDA: '{acao}'")
            messages.error(request, f'Ação desconhecida: {acao}')

        print("=== REDIRECIONANDO ===")
        return redirect('escalas:visualizar_escala', data=data)

class PuxarDadosView(LoginRequiredMixin, View):
    """View para puxar dados específicos da data indicada pelo usuário"""
    
    def get(self, request, data):
        """Exibe interface para puxar dados de uma data específica"""
        data_obj = parse_data_brasileira(data)
        escala = get_object_or_404(Escala, data=data_obj)
        
        if escala.etapa != 'ESTRUTURA':
            messages.warning(request, 'Esta escala já tem dados puxados.')
            return redirect('escalas:visualizar_escala', data=data)
        
        # Obter datas disponíveis com estatísticas
        datas_disponiveis = []
        datas_com_servicos = (Servico.objects
                             .values('data_do_servico')
                             .annotate(
                                 total_servicos=Count('id'),
                                 com_horario=Count('id', filter=Q(horario__isnull=False)),
                                 total_pax=Sum('pax')
                             )
                             .order_by('-data_do_servico'))
        
        for data_info in datas_com_servicos:
            datas_disponiveis.append({
                'data': data_info['data_do_servico'],
                'total_servicos': data_info['total_servicos'],
                'com_horario': data_info['com_horario'],
                'total_pax': data_info['total_pax'] or 0
            })
        
        context = {
            'escala': escala,
            'datas_disponiveis': datas_disponiveis
        }
        
        return render(request, 'escalas/puxar_dados.html', context)
    
    def post(self, request, data):
        """Puxa dados da data selecionada"""
        data_obj = parse_data_brasileira(data)
        escala = get_object_or_404(Escala, data=data_obj)
        data_origem_str = request.POST.get('data_origem')
        
        if not data_origem_str:
            messages.error(request, 'Selecione uma data de origem para puxar os dados.')
            return redirect('escalas:puxar_dados', data=data)
        
        try:
            data_origem = parse_data_brasileira(data_origem_str)
            
            # Buscar serviços da data de origem
            servicos = Servico.objects.filter(data_do_servico=data_origem)
            
            if not servicos.exists():
                messages.error(request, f'Nenhum serviço encontrado para {data_origem.strftime("%d/%m/%Y")}.')
                return redirect('escalas:puxar_dados', data=data)
            
            # Puxar dados e distribuir automaticamente
            self._puxar_e_distribuir_servicos(escala, servicos, data_origem)
            
            messages.success(request, 
                f'Dados puxados com sucesso! '
                f'{servicos.count()} serviços de {data_origem.strftime("%d/%m/%Y")} '
                f'distribuídos automaticamente entre as vans.')
            
            return redirect('escalas:visualizar_escala', data=data)
            
        except Exception as e:
            messages.error(request, f'Erro ao puxar dados: {str(e)}')
            return redirect('escalas:puxar_dados', data=data)
    
    def _puxar_e_distribuir_servicos(self, escala, servicos, data_origem):
        """Puxa dados e distribui automaticamente entre as vans"""
        with transaction.atomic():
            # Limpar alocações existentes
            escala.alocacoes.all().delete()
            
            # Converter para lista para poder embaralhar
            lista_servicos = list(servicos)
            
            # Embaralhar para distribuição mais equilibrada
            random.shuffle(lista_servicos)
            
            # Distribuir entre as vans
            for i, servico in enumerate(lista_servicos):
                van = 'VAN1' if i % 2 == 0 else 'VAN2'
                ordem = (i // 2) + 1
                
                alocacao = AlocacaoVan.objects.create(
                    escala=escala,
                    servico=servico,
                    van=van,
                    ordem=ordem,
                    automatica=True
                )
                
                # NÃO calcular preço automaticamente - será feito sob demanda
                # O preço ficará como R$ 0 até ser precificado manualmente
            
            # Atualizar escala
            escala.data_origem = data_origem
            escala.etapa = 'DADOS_PUXADOS'
            escala.save()


class MoverServicoView(LoginRequiredMixin, View):
    """View para mover serviços entre vans (funcionalidade Kanban)"""
    
    def post(self, request):
        """Move um serviço de uma van para outra"""
        try:
            data = json.loads(request.body)
            alocacao_id = data.get('alocacao_id')
            nova_van = data.get('nova_van')
            nova_posicao = data.get('nova_posicao', 0)
            
            alocacao = get_object_or_404(AlocacaoVan, id=alocacao_id)
            
            # Verificar se a escala permite movimentação
            if alocacao.escala.etapa == 'ESTRUTURA':
                return JsonResponse({'success': False, 'error': 'Escala não tem dados puxados'})
            
            with transaction.atomic():
                # Guardar van de origem antes da mudança
                van_origem = alocacao.van
                
                # Verificar se a alocação pertence a um grupo
                try:
                    servico_grupo = alocacao.grupo_info
                    grupo = servico_grupo.grupo
                    
                    # Se pertence a um grupo, mover TODO o grupo
                    alocacoes_do_grupo = AlocacaoVan.objects.filter(
                        grupo_info__grupo=grupo
                    )
                    
                    # Atualizar posições na van de destino
                    AlocacaoVan.objects.filter(
                        escala=alocacao.escala,
                        van=nova_van,
                        ordem__gte=nova_posicao
                    ).update(ordem=F('ordem') + alocacoes_do_grupo.count())
                    
                    # Mover todas as alocações do grupo
                    for i, alocacao_grupo in enumerate(alocacoes_do_grupo):
                        alocacao_grupo.van = nova_van
                        alocacao_grupo.ordem = nova_posicao + i
                        alocacao_grupo.automatica = False
                        alocacao_grupo.save()
                    
                    # Atualizar van do grupo
                    grupo.van = nova_van
                    grupo.save()
                    
                    mensagem_sucesso = f'Grupo com {alocacoes_do_grupo.count()} serviços movido com sucesso'
                    
                except ServicoGrupo.DoesNotExist:
                    # Se não pertence a um grupo, mover apenas a alocação individual
                    
                    # Atualizar posições na van de destino
                    AlocacaoVan.objects.filter(
                        escala=alocacao.escala,
                        van=nova_van,
                        ordem__gte=nova_posicao
                    ).update(ordem=F('ordem') + 1)
                    
                    # Mover o serviço
                    alocacao.van = nova_van
                    alocacao.ordem = nova_posicao
                    alocacao.automatica = False  # Marca como movido manualmente
                    alocacao.save()
                    
                    mensagem_sucesso = 'Serviço movido com sucesso'
                
                # Reorganizar a van de origem apenas se for diferente da destino
                if van_origem != nova_van:
                    reorganizar_ordem_por_status(alocacao.escala, van_origem)
                
                # Reorganizar também a van de destino se houve mudança
                reorganizar_ordem_por_status(alocacao.escala, nova_van)
            
            return JsonResponse({
                'success': True, 
                'message': mensagem_sucesso
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class AgruparServicosView(LoginRequiredMixin, View):
    """
    View para agrupar serviços quando um é solto sobre outro (Kanban avançado)
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            alocacao_origem_id = data.get('alocacao_origem_id')  # Alocação sendo arrastada
            alocacao_destino_id = data.get('alocacao_destino_id')  # Alocação sobre a qual foi solta
            
            if not alocacao_origem_id or not alocacao_destino_id:
                return JsonResponse({'success': False, 'error': 'IDs de alocações não fornecidos'})
            
            if alocacao_origem_id == alocacao_destino_id:
                return JsonResponse({'success': False, 'error': 'Não é possível agrupar um serviço com ele mesmo'})
            
            # Buscar as alocações
            alocacao_origem = get_object_or_404(AlocacaoVan, id=alocacao_origem_id)
            alocacao_destino = get_object_or_404(AlocacaoVan, id=alocacao_destino_id)
            
            # Verificar se pertencem à mesma escala
            if alocacao_origem.escala_id != alocacao_destino.escala_id:
                return JsonResponse({'success': False, 'error': 'Serviços de escalas diferentes não podem ser agrupados'})
            
            # Verificar se destino já está em um grupo
            grupo_destino = None
            try:
                # Se destino já tem grupo, usar esse grupo
                grupo_destino = alocacao_destino.grupo_info.grupo
            except ServicoGrupo.DoesNotExist:
                # Se destino não tem grupo, criar novo
                grupo_destino = GrupoServico.objects.create(
                    escala=alocacao_destino.escala,
                    van=alocacao_destino.van,
                    ordem=alocacao_destino.ordem,
                    cliente_principal=alocacao_destino.servico.cliente,
                    servico_principal=alocacao_destino.servico.servico,
                    local_pickup_principal=alocacao_destino.servico.local_pickup or ''
                )
                
                # Adicionar o serviço destino ao grupo
                ServicoGrupo.objects.create(
                    grupo=grupo_destino,
                    alocacao=alocacao_destino
                )
            
            # Verificar se origem já está em um grupo
            try:
                grupo_origem = alocacao_origem.grupo_info.grupo
                # Se origem está em outro grupo, mover todos os serviços do grupo origem para grupo destino
                if grupo_origem.id != grupo_destino.id:
                    servicos_origem = grupo_origem.servicos.all()
                    for servico_grupo in servicos_origem:
                        servico_grupo.grupo = grupo_destino
                        servico_grupo.save()
                        # Atualizar van da alocação para seguir o grupo
                        servico_grupo.alocacao.van = grupo_destino.van
                        servico_grupo.alocacao.save()
                    
                    # Deletar grupo origem vazio
                    grupo_origem.delete()
                
            except ServicoGrupo.DoesNotExist:
                # Se origem não tem grupo, simplesmente adicionar ao grupo destino
                ServicoGrupo.objects.create(
                    grupo=grupo_destino,
                    alocacao=alocacao_origem
                )
                
                # Atualizar van da origem para seguir o grupo
                alocacao_origem.van = grupo_destino.van
                alocacao_origem.save()
            
            # Recalcular totais do grupo
            grupo_destino.recalcular_totais()
            
            return JsonResponse({
                'success': True,
                'message': f'Serviços agrupados com sucesso',
                'grupo_id': grupo_destino.id,
                'total_servicos': grupo_destino.servicos.count()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class PrecificarEscalaView(LoginRequiredMixin, View):
    """
    View para precificar todos os serviços de uma escala usando sistema inteligente
    que consulta tarifários JW e Motoristas com busca fuzzy avançada
    """
    
    def post(self, request, data):
        """Precifica todos os serviços da escala usando busca inteligente"""
        try:
            # Buscar a escala
            data_obj = parse_data_brasileira(data)
            escala = get_object_or_404(Escala, data=data_obj)
            
            # Verificar se a escala tem dados puxados
            if escala.etapa == 'ESTRUTURA':
                return JsonResponse({
                    'status': 'error',
                    'success': False,
                    'message': 'Esta escala não tem dados puxados ainda.',
                    'error': 'Esta escala não tem dados puxados ainda.'
                })
            
            # Inicializar contadores e estatísticas detalhadas
            servicos_precificados = 0
            servicos_com_erro = 0
            total_valor = 0.0
            estatisticas_fonte = {'JW': 0, 'Motoristas': 0, 'padrão': 0}
            
            logger.info(f"🚀 INICIANDO PRECIFICAÇÃO INTELIGENTE - Escala {escala.data}")
            
            with transaction.atomic():
                # Buscar todas as alocações da escala
                alocacoes = escala.alocacoes.all()
                logger.info(f"📋 Total de alocações a precificar: {alocacoes.count()}")
                
                for alocacao in alocacoes:
                    try:
                        # Calcular preço e veículo usando sistema inteligente
                        veiculo_anterior = alocacao.veiculo_recomendado
                        preco_anterior = alocacao.preco_calculado
                        
                        veiculo, preco = alocacao.calcular_preco_e_veiculo()
                        
                        # Estatísticas por fonte (extrair do log)
                        # O log é gerado no modelo, então vamos inferir a fonte baseada no preço
                        if preco > 0:
                            # Busca inteligente para determinar fonte
                            from core.busca_inteligente_precos import BuscadorInteligentePrecosCodigoDoAnalista
                            buscador = BuscadorInteligentePrecosCodigoDoAnalista()
                            _, _, fonte = buscador.buscar_preco_inteligente(
                                alocacao.servico.servico, 
                                alocacao.servico.pax, 
                                str(alocacao.servico.numero_venda or "1")
                            )
                            
                            # Categorizar fonte
                            if 'JW' in fonte:
                                estatisticas_fonte['JW'] += 1
                            elif 'Motoristas' in fonte:
                                estatisticas_fonte['Motoristas'] += 1
                            else:
                                estatisticas_fonte['padrão'] += 1
                        
                        servicos_precificados += 1
                        total_valor += preco
                        
                        # Log detalhado de mudanças
                        if veiculo != veiculo_anterior or abs(preco - (preco_anterior or 0)) > 0.01:
                            logger.info(f"🔄 Atualização - {alocacao.servico.servico[:30]}... | "
                                       f"{veiculo_anterior or 'N/A'} → {veiculo} | "
                                       f"R$ {preco_anterior or 0:.2f} → R$ {preco:.2f}")
                        
                    except Exception as e:
                        logger.error(f"❌ Erro ao precificar alocação {alocacao.id}: {e}")
                        servicos_com_erro += 1
                
                # Recalcular totais de grupos se existirem
                grupos = escala.grupos.all()
                if grupos.exists():
                    logger.info(f"🔄 Recalculando totais de {grupos.count()} grupos...")
                    for grupo in grupos:
                        try:
                            grupo.recalcular_totais()
                        except Exception as e:
                            logger.error(f"❌ Erro ao calcular totais do grupo {grupo.id}: {e}")
            
            # Preparar mensagem detalhada
            valor_medio = total_valor / max(servicos_precificados, 1)
            
            if servicos_com_erro == 0:
                mensagem = (f"✅ Precificação inteligente concluída! "
                          f"{servicos_precificados} serviços precificados. "
                          f"Valor total: R$ {total_valor:,.2f} | "
                          f"Valor médio: R$ {valor_medio:.2f}")
            else:
                mensagem = (f"⚠️ Precificação concluída com avisos: "
                          f"{servicos_precificados} serviços OK, {servicos_com_erro} com erro. "
                          f"Valor total: R$ {total_valor:,.2f}")
            
            # Log das estatísticas finais
            logger.info(f"📊 ESTATÍSTICAS DA PRECIFICAÇÃO:")
            logger.info(f"   • Tarifário JW: {estatisticas_fonte['JW']} serviços")
            logger.info(f"   • Tarifário Motoristas: {estatisticas_fonte['Motoristas']} serviços")
            logger.info(f"   • Preços padrão: {estatisticas_fonte['padrão']} serviços")
            logger.info(f"   • Valor total: R$ {total_valor:,.2f}")
            logger.info(f"   • Valor médio por serviço: R$ {valor_medio:.2f}")
            
            return JsonResponse({
                'status': 'success',
                'success': True,
                'message': mensagem,
                'servicos_precificados': servicos_precificados,
                'servicos_com_erro': servicos_com_erro,
                'valor_total': round(total_valor, 2),
                'valor_medio': round(valor_medio, 2),
                'estatisticas_fonte': estatisticas_fonte
            })
            
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO na precificação da escala {data}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return JsonResponse({
                'status': 'error',
                'success': False,
                'message': f'Erro na precificação: {str(e)}',
                'error': f'Erro na precificação: {str(e)}'
            })


class DesagruparServicoView(View):
    """
    View para remover um serviço de um grupo
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            alocacao_id = data.get('alocacao_id')
            
            if not alocacao_id:
                return JsonResponse({'success': False, 'error': 'ID da alocação não fornecido'})
            
            # Buscar a alocação
            alocacao = get_object_or_404(AlocacaoVan, id=alocacao_id)
            
            # Verificar se está em um grupo
            try:
                servico_grupo = alocacao.grupo_info
                grupo = servico_grupo.grupo
                
                # Remover do grupo
                servico_grupo.delete()
                
                # Se o grupo ficou com menos de 2 serviços, desagrupar todos
                if grupo.servicos.count() < 2:
                    # Desagrupar todos os serviços restantes
                    for sg in grupo.servicos.all():
                        sg.delete()
                    # Deletar grupo vazio
                    grupo.delete()
                else:
                    # Recalcular totais do grupo
                    grupo.recalcular_totais()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Serviço removido do grupo'
                })
                
            except ServicoGrupo.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Serviço não está em nenhum grupo'})
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class ApiDetalhesPrecificacaoView(LoginRequiredMixin, View):
    """
    API para retornar detalhes completos da precificação de uma alocação
    """
    
    def get(self, request, alocacao_id):
        """Retorna detalhes da precificação"""
        try:
            alocacao = get_object_or_404(AlocacaoVan, id=alocacao_id)
            logger.info(f"📊 Buscando detalhes para alocação {alocacao_id}")
            
            # Extrair detalhes da precificação salvos
            detalhes = alocacao.detalhes_precificacao or {}
            logger.info(f"📊 Detalhes encontrados: {detalhes}")
            
            # Construir resposta no formato que o JavaScript espera
            dados = {
                # Informações básicas do serviço
                'numero_venda': alocacao.servico.numero_venda or 'N/A',
                'servico_nome': alocacao.servico.servico,
                'cliente': alocacao.servico.cliente,
                'pax': alocacao.servico.pax,
                'origem': alocacao.servico.local_pickup or 'N/A',
                'destino': f"{alocacao.servico.regiao} ({alocacao.servico.aeroporto})" if alocacao.servico.regiao != 'N/A' else 'N/A',
                'tipo_servico': alocacao.servico.get_tipo_display(),
                'direcao': alocacao.servico.direcao,
                
                # Informações de precificação
                'preco_calculado': f"{float(alocacao.preco_calculado):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if alocacao.preco_calculado else "0,00",
                'veiculo_recomendado': alocacao.veiculo_recomendado or 'N/A',
                'lucratividade': f"{float(alocacao.lucratividade):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if alocacao.lucratividade else "0,00",
                
                # Detalhes do tarifário
                'fonte_tarifario': detalhes.get('fonte', detalhes.get('tarifario', 'Não especificado')),
                'metodo_calculo': detalhes.get('metodo', detalhes.get('metodo_calculo', 'Cálculo padrão')),
                'tarifa_encontrada': detalhes.get('tarifa_encontrada', detalhes.get('chave_encontrada', detalhes.get('servico_encontrado', ''))),
                'score_similaridade': detalhes.get('score_similaridade', detalhes.get('similaridade', detalhes.get('score', None))),
                'preco_tabela': f"{float(detalhes.get('preco_tabela', 0)):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if detalhes.get('preco_tabela') else None,
                'multiplicador': detalhes.get('multiplicador', 1),
                
                # Informações adicionais
                'observacoes': detalhes.get('observacoes', 'Preço calculado com sucesso' if alocacao.preco_calculado else 'Sem observações disponíveis'),
                'data_calculo': detalhes.get('data_calculo', 'N/A'),
                'historico_busca': detalhes.get('historico_busca', []),
                
                # Status e debug
                'tem_detalhes_salvos': bool(alocacao.detalhes_precificacao),
                'todos_detalhes': detalhes  # Para debug, pode ser removido depois
            }
            
            logger.info(f"📊 Retornando dados expandidos: {len(str(dados))} caracteres")
            return JsonResponse(dados)
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar detalhes da precificação para alocação {alocacao_id}: {e}")
            return JsonResponse({
                'error': f'Erro interno: {str(e)}'
            }, status=500)


class ExportarEscalaView(LoginRequiredMixin, View):
    """View para exportar escala em Excel"""
    
    def get(self, request, data):
        data_obj = parse_data_brasileira(data)
        escala = get_object_or_404(Escala, data=data_obj)
        
        # Exporta para Excel
        exportador = ExportadorEscalas()
        excel_data = exportador.exportar_para_excel(escala)
        
        # Resposta HTTP
        response = HttpResponse(
            excel_data,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="escala_{data}.xlsx"'
        
        return response


class ExportarMesView(LoginRequiredMixin, View):
    """View para exportar escalas mensais em Excel"""
    
    def get(self, request, ano, mes):
        """
        Exporta todas as escalas de um mês específico
        :param ano: Ano (ex: 2024)
        :param mes: Mês (ex: 01, 02, ..., 12)
        """
        try:
            ano = int(ano)
            mes = int(mes)
            
            if mes < 1 or mes > 12:
                messages.error(request, "Mês inválido. Use valores entre 1 e 12.")
                return redirect('escalas:listar')
            
            # Busca todas as escalas do mês ordenadas por data
            escalas_mes = Escala.objects.filter(
                data__year=ano,
                data__month=mes
            ).order_by('data')
            
            if not escalas_mes.exists():
                messages.warning(request, f"Nenhuma escala encontrada para {MESES_PORTUGUES[mes]}/{ano}")
                return redirect('escalas:listar')
            
            # Exporta para Excel
            exportador = ExportadorEscalas()
            excel_data = exportador.exportar_mes_para_excel(list(escalas_mes))
            
            # Resposta HTTP
            nome_arquivo = f"escalas_{MESES_PORTUGUES[mes].lower()}_{ano}.xlsx"
            response = HttpResponse(
                excel_data,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
            
            return response
            
        except ValueError:
            messages.error(request, "Ano ou mês inválido. Use formato numérico.")
            return redirect('escalas:listar')
        except Exception as e:
            logger.error(f"Erro ao exportar escalas mensais: {str(e)}")
            messages.error(request, "Erro interno. Tente novamente.")
            return redirect('escalas:listar')


class VerificarSenhaExclusaoView(LoginRequiredMixin, View):
    """View para verificar senha antes da exclusão"""
    
    def get(self, request):
        """Teste de conectividade"""
        return JsonResponse({
            'status': 'ok',
            'usuario': request.user.username,
            'mensagem': 'Endpoint funcionando'
        })
    
    def post(self, request):
        import json
        from django.contrib.auth import authenticate
        
        try:
            logger.info(f"🔍 Verificação de senha iniciada para usuário: {request.user.username}")
            
            data = json.loads(request.body)
            senha = data.get('senha')
            data_escala = data.get('data')
            
            logger.info(f"📊 Dados recebidos - Usuário: {request.user.username}, Data escala: {data_escala}")
            
            # Verificar senha do usuário atual
            user = authenticate(username=request.user.username, password=senha)
            senha_correta = user is not None
            
            logger.info(f"🔐 Resultado verificação senha: {'✅ Correta' if senha_correta else '❌ Incorreta'}")
            
            return JsonResponse({
                'senha_correta': senha_correta,
                'usuario': request.user.username if senha_correta else None,
                'debug': f'Usuario: {request.user.username}, Verificacao: {senha_correta}'
            })
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar senha para exclusão: {e}")
            logger.error(f"❌ Request body: {request.body}")
            logger.error(f"❌ Usuario: {request.user.username if request.user else 'Anonimo'}")
            return JsonResponse({
                'senha_correta': False, 
                'erro': str(e),
                'debug': f'Erro: {str(e)}'
            })


class ExcluirEscalaView(LoginRequiredMixin, View):
    """View para excluir uma escala"""
    
    def post(self, request, data):
        """Exclui uma escala específica"""
        try:
            data_obj = parse_data_brasileira(data)
            escala = get_object_or_404(Escala, data=data_obj)
            
            # Salvar mês e ano para redirecionamento
            mes = data_obj.month
            ano = data_obj.year
            
            # Coletar dados para log antes da exclusão
            dados_log = {
                'data_escala': data_obj.strftime('%d/%m/%Y'),
                'etapa': escala.etapa,
                'total_servicos': escala.alocacoes.count(),
                'usuario': request.user.username,
                'ip_usuario': request.META.get('REMOTE_ADDR', 'N/A'),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'N/A')[:200]
            }
            
            # Verificar se é uma escala otimizada
            escala_otimizada = escala.etapa == 'OTIMIZADA'
            
            # Salvar informações para a mensagem
            data_formatada = data_obj.strftime('%d/%m/%Y')
            total_servicos = escala.alocacoes.count()
            
            # Registrar log ANTES da exclusão
            logger.warning(
                f"🗑️ EXCLUSÃO DE ESCALA INICIADA | "
                f"Data: {dados_log['data_escala']} | "
                f"Etapa: {dados_log['etapa']} | "
                f"Serviços: {dados_log['total_servicos']} | "
                f"Usuário: {dados_log['usuario']} | "
                f"IP: {dados_log['ip_usuario']}"
            )
            
            # Excluir escala (cascata exclui as alocações)
            with transaction.atomic():
                escala.delete()
            
            # Log de sucesso
            logger.error(
                f"❌ ESCALA EXCLUÍDA COM SUCESSO | "
                f"Data: {dados_log['data_escala']} | "
                f"Total serviços excluídos: {dados_log['total_servicos']} | "
                f"Era otimizada: {'Sim' if escala_otimizada else 'Não'} | "
                f"Usuário responsável: {dados_log['usuario']} | "
                f"IP: {dados_log['ip_usuario']}"
            )
            
            if total_servicos > 0:
                if escala_otimizada:
                    messages.success(
                        request,
                        f'Escala de {data_formatada} excluída com sucesso! '
                        f'{total_servicos} serviços otimizados foram removidos permanentemente. '
                        f'Exclusão registrada no log do sistema.'
                    )
                else:
                    messages.success(
                        request,
                        f'Escala de {data_formatada} excluída com sucesso! '
                        f'{total_servicos} serviços foram removidos da escala. '
                        f'Exclusão registrada no log do sistema.'
                    )
            else:
                messages.success(
                    request,
                    f'Estrutura de escala de {data_formatada} excluída com sucesso! '
                    f'Exclusão registrada no log do sistema.'
                )
            
            # Redirecionar para a página do mês específico
            return redirect('escalas:gerenciar_escalas_mes', mes=mes, ano=ano)
            
        except Exception as e:
            # Log de erro
            logger.error(
                f"❌ ERRO AO EXCLUIR ESCALA | "
                f"Data: {data} | "
                f"Usuário: {request.user.username} | "
                f"Erro: {str(e)} | "
                f"IP: {request.META.get('REMOTE_ADDR', 'N/A')}"
            )
            
            messages.error(request, f'Erro ao excluir escala: {str(e)}')
            # Em caso de erro, redirecionar para o ano atual
            return redirect('escalas:selecionar_ano')
    
    def get(self, request, data):
        """Redireciona para gerenciamento se acessado via GET"""
        messages.info(request, 'Acesso inválido. Use o botão de exclusão na interface.')
        # Tentar extrair mês e ano da data para redirecionamento mais específico
        try:
            data_obj = parse_data_brasileira(data)
            mes = data_obj.month
            ano = data_obj.year
            return redirect('escalas:gerenciar_escalas_mes', mes=mes, ano=ano)
        except:
            return redirect('escalas:selecionar_ano')


class DesagruparGrupoCompletoView(View):
    """
    View para desagrupar um grupo completo de serviços
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            alocacao_id = data.get('alocacao_id')
            
            if not alocacao_id:
                return JsonResponse({'success': False, 'error': 'ID da alocação não fornecido'})
            
            # Buscar a alocação
            alocacao = get_object_or_404(AlocacaoVan, id=alocacao_id)
            
            # Verificar se está em um grupo
            try:
                servico_grupo = alocacao.grupo_info
                grupo = servico_grupo.grupo
                
                # Contar serviços no grupo
                total_servicos = grupo.servicos.count()
                
                # Remover todos os serviços do grupo
                grupo.servicos.all().delete()
                
                # Deletar o grupo vazio
                grupo.delete()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Grupo com {total_servicos} serviços foi completamente desagrupado'
                })
                
            except ServicoGrupo.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Serviço não está em nenhum grupo'})
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class ExcluirServicoView(LoginRequiredMixin, View):
    """View para excluir um serviço/alocação"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            alocacao_id = data.get('alocacao_id')
            
            if not alocacao_id:
                return JsonResponse({'success': False, 'error': 'ID da alocação não fornecido'})
            
            # Buscar a alocação
            alocacao = get_object_or_404(AlocacaoVan, id=alocacao_id)
            servico = alocacao.servico
            
            with transaction.atomic():
                # Verificar se está em um grupo
                try:
                    servico_grupo = alocacao.grupo_info
                    grupo = servico_grupo.grupo
                    
                    # Remover do grupo primeiro
                    servico_grupo.delete()
                    
                    # Se o grupo ficou com menos de 2 serviços, desagrupar todos
                    if grupo.servicos.count() < 2:
                        for sg in grupo.servicos.all():
                            sg.delete()
                        grupo.delete()
                        
                except ServicoGrupo.DoesNotExist:
                    # Não está em grupo, pode excluir diretamente
                    pass
                
                # Guardar informações para a mensagem
                cliente = servico.cliente
                pax = servico.pax
                van = alocacao.van
                escala = alocacao.escala
                
                # Excluir a alocação (o serviço pode ser reutilizado em outras escalas)
                alocacao.delete()
                
                # Reorganizar ordem das demais alocações na van respeitando status
                reorganizar_ordem_por_status(escala, van)
                
                return JsonResponse({
                    'success': True,
                    'message': f'Serviço {cliente} ({pax} PAX) foi excluído da {van}'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class DetalhesServicoView(View):
    """
    View para carregar detalhes de um serviço para edição
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            alocacao_id = data.get('alocacao_id')
            
            if not alocacao_id:
                return JsonResponse({'success': False, 'error': 'ID da alocação não fornecido'})
            
            # Buscar a alocação e serviço
            alocacao = get_object_or_404(AlocacaoVan, id=alocacao_id)
            servico = alocacao.servico
            
            # Preparar dados do serviço
            servico_data = {
                'id': servico.id,
                'cliente': servico.cliente,
                'pax': servico.pax,
                'servico': servico.servico,
                'local_pickup': servico.local_pickup,
                'horario': servico.horario.strftime('%H:%M') if servico.horario else '',
                'data_do_servico': servico.data_do_servico.strftime('%d-%m-%Y') if servico.data_do_servico else '',
                'numero_venda': servico.numero_venda,
                'tipo': servico.tipo,
                'direcao': servico.direcao,
                'aeroporto': servico.aeroporto,
                'regiao': servico.regiao,
                'eh_regular': servico.eh_regular,
                'eh_prioritario': servico.eh_prioritario,
                # Campos que não existem no modelo - usar valores padrão
                'numero_da_compra': '',
                'valor_venda': 0,
                'valor_repasse': 0,
                'categoria': '',
                'observacoes': '',
            }
            
            # Dados da alocação
            alocacao_data = {
                'id': alocacao.id,
                'van': alocacao.van,
                'ordem': alocacao.ordem,
            }
            
            return JsonResponse({
                'success': True,
                'servico': servico_data,
                'alocacao': alocacao_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class SalvarEdicaoServicoView(View):
    """
    View para salvar edições de um serviço
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            servico_id = data.get('servico_id')
            alocacao_id = data.get('alocacao_id')
            
            if not servico_id or not alocacao_id:
                return JsonResponse({'success': False, 'error': 'IDs não fornecidos'})
            
            # Buscar serviço e alocação
            servico = get_object_or_404(Servico, id=servico_id)
            alocacao = get_object_or_404(AlocacaoVan, id=alocacao_id)
            
            with transaction.atomic():
                # Atualizar dados do serviço que existem no modelo
                servico.cliente = data.get('cliente', servico.cliente)
                servico.pax = int(data.get('pax', servico.pax))
                servico.servico = data.get('servico', servico.servico)
                servico.local_pickup = data.get('local_pickup', servico.local_pickup)
                servico.numero_venda = data.get('numero_venda', servico.numero_venda)
                
                # Horário
                horario_str = data.get('horario')
                if horario_str:
                    from datetime import datetime
                    servico.horario = datetime.strptime(horario_str, '%H:%M').time()
                
                # Data do serviço
                data_str = data.get('data_do_servico')
                if data_str:
                    servico.data_do_servico = parse_date(data_str)
                
                # Campos específicos do modelo
                if data.get('tipo') and data.get('tipo') in ['TRANSFER', 'DISPOSICAO', 'TOUR', 'OUTRO']:
                    servico.tipo = data.get('tipo')
                
                if data.get('direcao') and data.get('direcao') in ['IN', 'OUT', 'N/A']:
                    servico.direcao = data.get('direcao')
                
                if data.get('aeroporto') and data.get('aeroporto') in ['GIG', 'SDU', 'N/A']:
                    servico.aeroporto = data.get('aeroporto')
                
                if data.get('regiao'):
                    servico.regiao = data.get('regiao')
                
                # Campos booleanos
                servico.eh_regular = bool(data.get('eh_regular', False))
                servico.eh_prioritario = bool(data.get('eh_prioritario', False))
                
                servico.save()
                
                # Atualizar van se mudou
                nova_van = data.get('van')
                if nova_van and nova_van != alocacao.van:
                    alocacao.van = nova_van
                    alocacao.save()
                
                # Recalcular preço
                from core.tarifarios import calcular_preco_servico
                veiculo_recomendado, preco_calculado = calcular_preco_servico(servico)
                alocacao.preco_calculado = preco_calculado
                alocacao.veiculo_recomendado = veiculo_recomendado
                alocacao.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Serviço atualizado com sucesso'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class DetalhesGrupoView(View):
    """
    View para carregar detalhes de um grupo para edição
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            alocacao_id = data.get('alocacao_id')
            
            if not alocacao_id:
                return JsonResponse({'success': False, 'error': 'ID da alocação não fornecido'})
            
            # Buscar a alocação e verificar se está em um grupo
            alocacao = get_object_or_404(AlocacaoVan, id=alocacao_id)
            
            try:
                servico_grupo = alocacao.grupo_info
                grupo = servico_grupo.grupo
            except ServicoGrupo.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Serviço não está em nenhum grupo'})
            
            # Dados do grupo
            grupo_data = {
                'id': grupo.id,
                'cliente_principal': grupo.cliente_principal,
                'servico_principal': grupo.servico_principal,
                'local_pickup_principal': grupo.local_pickup_principal,
                'van': grupo.van,
                'total_pax': grupo.total_pax,
                'total_valor': float(grupo.total_valor) if grupo.total_valor else 0,
            }
            
            # Dados dos serviços do grupo
            servicos_data = []
            for sg in grupo.servicos.all():
                servico = sg.alocacao.servico
                servicos_data.append({
                    'alocacao_id': sg.alocacao.id,
                    'cliente': servico.cliente,
                    'pax': servico.pax,
                    'servico': servico.servico,
                    'local_pickup': servico.local_pickup,
                    'horario': servico.horario.strftime('%H:%M') if servico.horario else '',
                    'numero_venda': servico.numero_venda or '',
                })
            
            return JsonResponse({
                'success': True,
                'grupo': grupo_data,
                'servicos': servicos_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class SalvarEdicaoGrupoView(View):
    """
    View para salvar edições de um grupo
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            grupo_id = data.get('grupo_id')
            
            if not grupo_id:
                return JsonResponse({'success': False, 'error': 'ID do grupo não fornecido'})
            
            # Buscar grupo
            grupo = get_object_or_404(GrupoServico, id=grupo_id)
            
            with transaction.atomic():
                # Atualizar dados do grupo
                grupo.cliente_principal = data.get('cliente_principal', grupo.cliente_principal)
                grupo.servico_principal = data.get('servico_principal', grupo.servico_principal)
                grupo.local_pickup_principal = data.get('local_pickup_principal', grupo.local_pickup_principal)
                
                # Atualizar van do grupo e de todas as alocações
                nova_van = data.get('van')
                if nova_van and nova_van != grupo.van:
                    grupo.van = nova_van
                    # Atualizar van de todas as alocações do grupo
                    for sg in grupo.servicos.all():
                        sg.alocacao.van = nova_van
                        sg.alocacao.save()
                
                grupo.save()
                
                # Recalcular totais do grupo
                grupo.recalcular_totais()
            
            return JsonResponse({
                'success': True,
                'message': 'Grupo atualizado com sucesso'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })



class AprovarEscalaView(LoginRequiredMixin, View):
    """View para aprovar ou rejeitar escalas"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            escala_id = data.get("escala_id")
            acao = data.get("acao")  # "aprovar" ou "rejeitar"
            observacoes = data.get("observacoes", "")
            
            escala = get_object_or_404(Escala, id=escala_id)
            
            # Verificar se a escala pode ser aprovada
            if not escala.pode_aprovar:
                return JsonResponse({
                    "success": False,
                    "error": "Esta escala não pode ser aprovada no momento"
                })
            
            # Verificar se o usuário tem permissão (cristiane.aguiar ou lucy.leite)
            if request.user.username not in ["cristiane.aguiar", "lucy.leite"]:
                return JsonResponse({
                    "success": False,
                    "error": "Você não tem permissão para aprovar escalas"
                })
            
            # Atualizar status da escala
            if acao == "aprovar":
                escala.status = "APROVADA"
                message = "Escala aprovada com sucesso!"
            elif acao == "rejeitar":
                escala.status = "REJEITADA"
                message = "Escala rejeitada."
            else:
                return JsonResponse({
                    "success": False,
                    "error": "Ação inválida"
                })
            
            escala.aprovada_por = request.user
            escala.data_aprovacao = timezone.now()
            escala.observacoes_aprovacao = observacoes
            escala.save()
            
            return JsonResponse({
                "success": True,
                "message": message,
                "status": escala.get_status_display()
            })
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            })


class ApiServicoDetailView(LoginRequiredMixin, View):
    """
    API para buscar detalhes de um serviço específico
    """
    
    def get(self, request, alocacao_id):
        try:
            alocacao = get_object_or_404(AlocacaoVan, id=alocacao_id)
            servico = alocacao.servico
            
            data = {
                'success': True,
                'servico': {
                    'id': servico.id,
                    'cliente': servico.cliente,
                    'servico': servico.servico,
                    'pax': servico.pax,
                    'horario': servico.horario.strftime('%H:%M') if servico.horario else '',
                    'local_pickup': servico.local_pickup or '',
                    'numero_venda': servico.numero_venda or '',
                    'data_do_servico': servico.data_do_servico.strftime('%d-%m-%Y') if servico.data_do_servico else '',
                },
                'alocacao': {
                    'id': alocacao.id,
                    'van': alocacao.van,
                    'preco_calculado': str(alocacao.preco_calculado or 0),
                    'veiculo_recomendado': alocacao.veiculo_recomendado or '',
                    'lucratividade': str(alocacao.lucratividade or 0),
                    'automatica': alocacao.automatica,
                }
            }
            
            return JsonResponse(data)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class ApiTarifariosView(LoginRequiredMixin, View):
    """
    API para buscar tarifários JW e Motoristas
    """
    
    def get(self, request):
        from core.tarifarios import TARIFARIO_JW, TARIFARIO_MOTORISTAS
        
        return JsonResponse({
            'success': True,
            'tarifario_jw': TARIFARIO_JW,
            'tarifario_motoristas': TARIFARIO_MOTORISTAS
        })


class ApiAtualizarPrecoView(LoginRequiredMixin, View):
    """
    API para atualizar preço de uma alocação ou grupo
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            servico_id = data.get('servico_id')
            preco = data.get('preco')
            tipo = data.get('tipo', 'individual')
            fonte = data.get('fonte', 'Manual')
            grupo_id = data.get('grupo_id')
            
            if not servico_id or not preco:
                return JsonResponse({
                    'success': False,
                    'error': 'Dados incompletos'
                })
            
            novo_preco = converter_para_decimal_seguro(preco)
            
            if tipo == 'grupo' and grupo_id:
                # Atualizar preço do grupo
                try:
                    grupo = GrupoServico.objects.get(id=grupo_id)
                    grupo.total_valor = novo_preco
                    grupo.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Preço do grupo atualizado para R$ {novo_preco:.2f}',
                        'tipo': 'grupo',
                        'grupo_id': grupo_id
                    })
                except GrupoServico.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Grupo não encontrado'
                    })
            else:
                # Atualizar preço individual
                try:
                    # Buscar alocação por serviço
                    alocacao = AlocacaoVan.objects.filter(servico_id=servico_id).first()
                    
                    if not alocacao:
                        return JsonResponse({
                            'success': False,
                            'error': 'Alocação não encontrada'
                        })
                    
                    # Atualizar preço
                    alocacao.preco_calculado = novo_preco
                    alocacao.automatica = False  # Marcar como manual quando editado
                    alocacao.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Preço atualizado para R$ {novo_preco:.2f}',
                        'tipo': 'individual',
                        'servico_id': servico_id
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': f'Erro ao atualizar preço individual: {str(e)}'
                    })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class DesfazerAgrupamentosAutomaticosView(LoginRequiredMixin, View):
    """
    View para desfazer todos os agrupamentos criados automaticamente
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            escala_id = data.get('escala_id')
            
            if not escala_id:
                return JsonResponse({
                    'success': False,
                    'error': 'ID da escala não fornecido'
                })
            
            # Buscar escala
            escala = get_object_or_404(Escala, id=escala_id)
            
            # Buscar todas as alocações automáticas que estão em grupos
            alocacoes_automaticas = escala.alocacoes.filter(
                automatica=True,
                grupo_info__isnull=False
            )
            
            grupos_para_remover = set()
            grupos_desfeitos = 0
            
            with transaction.atomic():
                # Coletar grupos que serão afetados
                for alocacao in alocacoes_automaticas:
                    try:
                        grupo = alocacao.grupo_info.grupo
                        grupos_para_remover.add(grupo.id)
                    except:
                        pass
                
                # Remover serviços dos grupos
                ServicoGrupo.objects.filter(
                    alocacao__in=alocacoes_automaticas
                ).delete()
                
                # Remover grupos que ficaram vazios ou só com serviços automáticos
                for grupo_id in grupos_para_remover:
                    try:
                        grupo = GrupoServico.objects.get(id=grupo_id)
                        
                        # Verificar se o grupo ainda tem serviços
                        if grupo.servicos.count() == 0:
                            grupo.delete()
                            grupos_desfeitos += 1
                        elif grupo.servicos.filter(alocacao__automatica=False).count() == 0:
                            # Se só tem serviços automáticos, desfazer o grupo todo
                            grupo.delete()
                            grupos_desfeitos += 1
                        else:
                            # Grupo tem serviços manuais, só contar como desfeito parcial
                            grupos_desfeitos += 1
                            
                    except GrupoServico.DoesNotExist:
                        pass
            
            return JsonResponse({
                'success': True,
                'message': f'{grupos_desfeitos} agrupamentos automáticos foram desfeitos',
                'grupos_desfeitos': grupos_desfeitos
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class EditarHorarioServicoView(LoginRequiredMixin, View):
    """
    View para editar horário de um serviço específico
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            alocacao_id = data.get('alocacao_id')
            horario_str = data.get('horario')
            
            if not alocacao_id:
                return JsonResponse({
                    'success': False,
                    'error': 'ID da alocação não fornecido'
                })
            
            # Buscar alocação
            alocacao = get_object_or_404(AlocacaoVan, id=alocacao_id)
            servico = alocacao.servico
            
            with transaction.atomic():
                # Atualizar horário
                if horario_str:
                    from datetime import datetime
                    try:
                        servico.horario = datetime.strptime(horario_str, '%H:%M').time()
                    except ValueError:
                        return JsonResponse({
                            'success': False,
                            'error': 'Formato de horário inválido. Use HH:MM'
                        })
                else:
                    servico.horario = None
                
                servico.save()
                
                # Se o serviço estiver em um grupo, recalcular totais
                try:
                    grupo_info = alocacao.grupo_info
                    if grupo_info:
                        grupo_info.grupo.recalcular_totais()
                except ServicoGrupo.DoesNotExist:
                    pass  # Serviço não está em grupo
            
            return JsonResponse({
                'success': True,
                'message': f'Horário atualizado para {horario_str if horario_str else "sem horário"}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })



def reorganizar_ordem_por_status(escala, van):
    """
    Reorganiza a ordem das alocações de uma van priorizando serviços alocados
    """
    # Buscar alocações da van ordenadas por status (ALOCADO primeiro) e depois por ordem atual
    alocacoes = AlocacaoVan.objects.filter(
        escala=escala, 
        van=van
    ).order_by('status_alocacao', 'ordem')
    
    # Reorganizar as ordens sequencialmente
    for i, alocacao in enumerate(alocacoes, 1):
        if alocacao.ordem != i:
            alocacao.ordem = i
            alocacao.save()


class ToggleStatusAlocacaoView(LoginRequiredMixin, View):
    """View para alternar o status de alocação de um serviço"""
    
    def post(self, request):
        import json
        
        try:
            data = json.loads(request.body)
            alocacao_id = data.get("alocacao_id")
            novo_status = data.get("novo_status")
            
            if not alocacao_id or not novo_status:
                return JsonResponse({
                    "success": False,
                    "message": "Dados incompletos"
                })
            
            # Verificar se o status é válido
            if novo_status not in ["ALOCADO", "NAO_ALOCADO"]:
                return JsonResponse({
                    "success": False,
                    "message": "Status inválido"
                })
            
            # Buscar a alocação
            try:
                alocacao = AlocacaoVan.objects.get(id=alocacao_id)
            except AlocacaoVan.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "message": "Serviço não encontrado"
                })
            
            # Atualizar o status
            alocacao.status_alocacao = novo_status
            alocacao.save()
            
            # Reorganizar a ordem da van para manter alocados primeiro
            reorganizar_ordem_por_status(alocacao.escala, alocacao.van)
            
            # Log da alteração
            logger.info(f"📝 Status de alocação alterado: {alocacao.servico.servico[:50]}... -> {novo_status} (usuário: {request.user.username})")
            
            return JsonResponse({
                "success": True,
                "message": f"Status alterado para {novo_status}",
                "reorganizado": True
            })
            
        except Exception as e:
            logger.error(f"❌ Erro ao alterar status de alocação: {e}")
            return JsonResponse({
                "success": False,
                "message": f"Erro interno: {str(e)}"
            })
