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
from decimal import Decimal
from calendar import monthrange
import re
from core.models import Servico, ProcessamentoPlanilha
from escalas.models import Escala, AlocacaoVan, GrupoServico, ServicoGrupo
from core.processors import ProcessadorPlanilhaOS
from escalas.services import GerenciadorEscalas, ExportadorEscalas
from core.tarifarios import calcular_preco_servico
import json
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
        
        escalas = Escala.objects.filter(
            data__gte=primeiro_dia,
            data__lte=ultimo_dia
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
                
            elif acao == 'otimizar':
                escala = get_object_or_404(Escala, data=data_alvo)
                if escala.etapa != 'DADOS_PUXADOS':
                    messages.error(request, 'Para otimizar, é necessário ter dados puxados.')
                    if mes and ano:
                        return redirect('escalas:gerenciar_escalas_mes', mes=mes, ano=ano)
                    return redirect('escalas:selecionar_ano')
                
                self._otimizar_escala(escala)
                messages.success(request, f'Escala para {data_alvo.strftime("%d/%m/%Y")} otimizada com sucesso!')
                
                return redirect('escalas:visualizar_escala', data=data_str)
                
        except Exception as e:
            logger.error(f"Erro no processamento POST: {e}")
            messages.error(request, f'Erro: {str(e)}')
        
        if mes and ano:
            return redirect('escalas:gerenciar_escalas_mes', mes=mes, ano=ano)
        return redirect('escalas:selecionar_ano')
    
    def _otimizar_escala(self, escala):
        """Otimiza a distribuição dos serviços nas vans baseado em lucratividade"""
        with transaction.atomic():
            # Recalcular todos os preços e lucratividade
            for alocacao in escala.alocacoes.all():
                alocacao.calcular_preco_e_veiculo()
            
            # Obter todos os serviços ordenados por lucratividade (maior primeiro)
            alocacoes = list(escala.alocacoes.order_by('-lucratividade', '-preco_calculado'))
            
            # Redistribuir de forma otimizada
            van1_servicos = []
            van2_servicos = []
            van1_pax = 0
            van2_pax = 0
            
            for alocacao in alocacoes:
                # Escolhe a van com menos PAX (balanceamento)
                # Prioriza serviços mais lucrativos para van com mais capacidade
                if van1_pax <= van2_pax:
                    van1_servicos.append(alocacao)
                    van1_pax += alocacao.servico.pax
                    alocacao.van = 'VAN1'
                    alocacao.ordem = len(van1_servicos)
                else:
                    van2_servicos.append(alocacao)
                    van2_pax += alocacao.servico.pax
                    alocacao.van = 'VAN2'
                    alocacao.ordem = len(van2_servicos)
                
                alocacao.automatica = True
                alocacao.save()
            
            # Atualizar status da escala
            escala.etapa = 'OTIMIZADA'
            escala.save()

    def _agrupar_servicos(self, escala):
        """Agrupa serviços compatíveis na escala"""
        print(f"DEBUG: Iniciando _agrupar_servicos para escala {escala.id}")
        grupos_criados = 0
        
        logger.debug(f"Iniciando agrupamento para escala {escala.id}")
        
        with transaction.atomic():
            # Buscar alocações que ainda não estão agrupadas
            alocacoes_disponiveis = escala.alocacoes.filter(
                grupo_info__isnull=True
            ).order_by('servico__horario')
            
            print(f"DEBUG: Encontradas {alocacoes_disponiveis.count()} alocações disponíveis")
            logger.debug(f"Encontradas {alocacoes_disponiveis.count()} alocações disponíveis para agrupamento")
            
            for alocacao in alocacoes_disponiveis:
                if hasattr(alocacao, 'grupo_info') and alocacao.grupo_info:
                    continue  # Já foi agrupada
                
                # Buscar serviços compatíveis para agrupamento
                servicos_compativeis = self._encontrar_servicos_compativeis(alocacao, alocacoes_disponiveis)
                
                if servicos_compativeis:
                    # Criar grupo
                    grupo = GrupoServico.objects.create(
                        escala=escala,
                        van=alocacao.van or 'VAN1',
                        cliente_principal=alocacao.servico.cliente,
                        servico_principal=alocacao.servico.servico,
                        local_pickup_principal=alocacao.servico.local_pickup or ''
                    )
                    
                    # Adicionar serviços ao grupo
                    total_pax = 0
                    total_valor = 0
                    
                    for servico_alocacao in [alocacao] + servicos_compativeis:
                        ServicoGrupo.objects.create(
                            grupo=grupo,
                            alocacao=servico_alocacao
                        )
                        total_pax += servico_alocacao.servico.pax
                        total_valor += servico_alocacao.preco_calculado or 0
                    
                    # Atualizar grupo com totais
                    grupo.total_pax = total_pax
                    grupo.total_valor = total_valor
                    grupo.save()
                    
                    grupos_criados += 1
                    
                    logger.info(f"Grupo criado: {grupo.cliente_principal} com {len(servicos_compativeis) + 1} serviços e {total_pax} PAX")
        
        logger.debug(f"Agrupamento finalizado. Total de grupos criados: {grupos_criados}")
        return grupos_criados
    
    def _encontrar_servicos_compativeis(self, alocacao_base, alocacoes_disponiveis):
        """Encontra serviços compatíveis para agrupamento"""
        servicos_compativeis = []
        servico_base = alocacao_base.servico
        
        for outra_alocacao in alocacoes_disponiveis:
            if outra_alocacao.id == alocacao_base.id:
                continue
            if hasattr(outra_alocacao, 'grupo_info') and outra_alocacao.grupo_info:
                continue
                
            outro_servico = outra_alocacao.servico
            
            # Verificar compatibilidade
            if self._servicos_sao_compativeis(servico_base, outro_servico):
                servicos_compativeis.append(outra_alocacao)
        
        return servicos_compativeis
    
    def _servicos_sao_compativeis(self, servico1, servico2):
        """Verifica se dois serviços podem ser agrupados"""
        # 1. Mesmo nome de serviço e diferença de até 40 minutos
        if self._normalizar_nome_servico(servico1.servico) == self._normalizar_nome_servico(servico2.servico):
            if self._diferenca_horario_minutos(servico1.horario, servico2.horario) <= 40:
                return True
        
        # 2. Transfers OUT regulares com mesmo local de pickup (≥ 4 PAX total)
        if (self._eh_transfer_out(servico1.servico) and 
            self._eh_transfer_out(servico2.servico) and
            servico1.local_pickup == servico2.local_pickup):
            if (servico1.pax + servico2.pax) >= 4:
                return True
        
        # 3. Serviços de TOUR (incluindo variações)
        if (self._eh_tour(servico1.servico) and 
            self._eh_tour(servico2.servico)):
            if self._diferenca_horario_minutos(servico1.horario, servico2.horario) <= 40:
                return True
        
        # 4. Serviços de GUIA À DISPOSIÇÃO (diferentes durações)
        if (self._eh_guia_disposicao(servico1.servico) and 
            self._eh_guia_disposicao(servico2.servico)):
            if self._diferenca_horario_minutos(servico1.horario, servico2.horario) <= 40:
                return True
        
        return False
    
    def _normalizar_nome_servico(self, nome):
        """Normaliza nome do serviço para comparação"""
        import re
        
        nome_normalizado = nome.upper().strip()
        
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
        nome_upper = nome_servico.upper()
        return 'TRANSFER' in nome_upper and 'OUT' in nome_upper
    
    def _eh_tour(self, nome_servico):
        """Verifica se é um serviço de tour"""
        nome_upper = nome_servico.upper()
        return ('TOUR' in nome_upper or 
                'VEÍCULO + GUIA À DISPOSIÇÃO' in nome_upper or
                'VEICULO + GUIA' in nome_upper)
    
    def _eh_guia_disposicao(self, nome_servico):
        """Verifica se é um serviço de guia à disposição"""
        nome_upper = nome_servico.upper()
        # Padrão: GUIA À DISPOSIÇÃO XX HORAS
        padrao = r'GUIA\s*À\s*DISPOSIÇÃO\s*\d+\s*HORAS?'
        return bool(re.search(padrao, nome_upper))
    

class VisualizarEscalaView(LoginRequiredMixin, View):
    """View para visualizar uma escala específica"""
    
    template_name = 'escalas/visualizar.html'
    
    def get_object(self):
        data_str = self.kwargs.get('data')
        data = parse_data_brasileira(data_str)
        return get_object_or_404(Escala, data=data)

    def get(self, request, data):
        """Exibe a escala"""
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
        
        # Obter todas as alocações
        all_van1_alocacoes = escala.alocacoes.filter(van='VAN1').order_by('ordem')
        all_van2_alocacoes = escala.alocacoes.filter(van='VAN2').order_by('ordem')
        
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
        
        # Informações sobre grupos
        grupos_van1 = escala.grupos.filter(van='VAN1').order_by('ordem')
        grupos_van2 = escala.grupos.filter(van='VAN2').order_by('ordem')
        
        context.update({
            'van1': van1_data,
            'van2': van2_data,
            'grupos_van1': grupos_van1,
            'grupos_van2': grupos_van2,
            'total_servicos': all_van1_alocacoes.count() + all_van2_alocacoes.count(),
        })
        
        return context

    def post(self, request, data):
        """Processa ações do botão Agrupar e Otimizar"""
        print(f"DEBUG: POST recebido na VisualizarEscalaView - data: {data}")
        print(f"DEBUG: POST data: {request.POST}")
        
        acao = request.POST.get('acao')
        print(f"DEBUG: Ação solicitada: {acao}")
        
        escala = self.get_object()
        print(f"DEBUG: Escala encontrada: {escala.id}")
        
        if acao == 'agrupar':
            logger.debug(f"Processando ação agrupar para escala {escala.id}")
            
            if escala.etapa != 'DADOS_PUXADOS':
                messages.error(request, 'Para agrupar, é necessário ter dados puxados.')
                return redirect('escalas:visualizar_escala', data=data)
            
            try:
                print(f"DEBUG: Tentando agrupar serviços para escala {escala.id}")
                # Mover a função _agrupar_servicos da GerenciarEscalasView para esta view
                grupos_criados = self._agrupar_servicos(escala)
                print(f"DEBUG: Agrupamento retornou {grupos_criados} grupos")
                logger.debug(f"Agrupamento concluído - Grupos criados: {grupos_criados}")
                messages.success(request, f'Agrupamento concluído! {grupos_criados} grupos criados.')
            except Exception as e:
                print(f"DEBUG: Erro no agrupamento: {e}")
                logger.error(f"Erro no agrupamento: {e}")
                messages.error(request, f'Erro ao agrupar serviços: {e}')
        
        elif acao == 'otimizar':
            if escala.etapa != 'DADOS_PUXADOS':
                messages.error(request, 'Para otimizar, é necessário ter dados puxados.')
                return redirect('escalas:visualizar_escala', data=data)
            
            try:
                # Mover a função _otimizar_escala da GerenciarEscalasView para esta view  
                self._otimizar_escala(escala)
                messages.success(request, 'Escala otimizada com sucesso!')
            except Exception as e:
                logger.error(f"Erro ao otimizar escala: {e}")
                messages.error(request, f'Erro ao otimizar escala: {e}')
        
        # Manter na mesma página de visualização
        return redirect('escalas:visualizar_escala', data=data)

    def _agrupar_servicos(self, escala):
        """Agrupa serviços compatíveis na escala"""
        print(f"DEBUG: ===== INICIANDO AGRUPAMENTO =====")
        print(f"DEBUG: Escala ID: {escala.id}")
        print(f"DEBUG: Escala data: {escala.data}")
        print(f"DEBUG: Escala etapa: {escala.etapa}")
        
        grupos_criados = 0
        
        logger.debug(f"Iniciando agrupamento para escala {escala.id}")
        
        with transaction.atomic():
            # Buscar alocações que ainda não estão agrupadas
            alocacoes_disponiveis = escala.alocacoes.filter(
                grupo_info__isnull=True
            ).order_by('servico__horario')
            
            print(f"DEBUG: Encontradas {alocacoes_disponiveis.count()} alocações disponíveis")
            logger.debug(f"Encontradas {alocacoes_disponiveis.count()} alocações disponíveis para agrupamento")
            
            for alocacao in alocacoes_disponiveis:
                if hasattr(alocacao, 'grupo_info') and alocacao.grupo_info:
                    continue  # Já foi agrupada
                
                # Buscar serviços compatíveis para agrupamento
                servicos_compativeis = self._encontrar_servicos_compativeis(alocacao, alocacoes_disponiveis)
                
                if servicos_compativeis:
                    # Criar grupo
                    grupo = GrupoServico.objects.create(
                        escala=escala,
                        van=alocacao.van or 'VAN1',
                        cliente_principal=alocacao.servico.cliente,
                        servico_principal=alocacao.servico.servico,
                        local_pickup_principal=alocacao.servico.local_pickup or ''
                    )
                    
                    # Adicionar serviços ao grupo
                    total_pax = 0
                    total_valor = 0
                    
                    for servico_alocacao in [alocacao] + servicos_compativeis:
                        ServicoGrupo.objects.create(
                            grupo=grupo,
                            alocacao=servico_alocacao
                        )
                        total_pax += servico_alocacao.servico.pax
                        total_valor += servico_alocacao.preco_calculado or 0
                    
                    # Atualizar grupo com totais
                    grupo.total_pax = total_pax
                    grupo.total_valor = total_valor
                    grupo.save()
                    
                    grupos_criados += 1
                    
                    logger.info(f"Grupo criado: {grupo.cliente_principal} com {len(servicos_compativeis) + 1} serviços e {total_pax} PAX")
        
        logger.debug(f"Agrupamento finalizado. Total de grupos criados: {grupos_criados}")
        return grupos_criados
    
    def _encontrar_servicos_compativeis(self, alocacao_base, alocacoes_disponiveis):
        """Encontra serviços compatíveis para agrupamento"""
        servicos_compativeis = []
        servico_base = alocacao_base.servico
        
        for outra_alocacao in alocacoes_disponiveis:
            if outra_alocacao.id == alocacao_base.id:
                continue
            if hasattr(outra_alocacao, 'grupo_info') and outra_alocacao.grupo_info:
                continue
                
            outro_servico = outra_alocacao.servico
            
            # Verificar compatibilidade
            if self._servicos_sao_compativeis(servico_base, outro_servico):
                servicos_compativeis.append(outra_alocacao)
        
        return servicos_compativeis
    
    def _servicos_sao_compativeis(self, servico1, servico2):
        """Verifica se dois serviços podem ser agrupados"""
        # 1. Mesmo nome de serviço e diferença de até 40 minutos
        if self._normalizar_nome_servico(servico1.servico) == self._normalizar_nome_servico(servico2.servico):
            if self._diferenca_horario_minutos(servico1.horario, servico2.horario) <= 40:
                return True
        
        # 2. Transfers OUT regulares com mesmo local de pickup (≥ 4 PAX total)
        if (self._eh_transfer_out(servico1.servico) and 
            self._eh_transfer_out(servico2.servico) and
            servico1.local_pickup == servico2.local_pickup):
            if (servico1.pax + servico2.pax) >= 4:
                return True
        
        # 3. Serviços de TOUR (incluindo variações)
        if (self._eh_tour(servico1.servico) and 
            self._eh_tour(servico2.servico)):
            if self._diferenca_horario_minutos(servico1.horario, servico2.horario) <= 40:
                return True
        
        # 4. Serviços de GUIA À DISPOSIÇÃO (diferentes durações)
        if (self._eh_guia_disposicao(servico1.servico) and 
            self._eh_guia_disposicao(servico2.servico)):
            if self._diferenca_horario_minutos(servico1.horario, servico2.horario) <= 40:
                return True
        
        return False
    
    def _normalizar_nome_servico(self, nome):
        """Normaliza nome do serviço para comparação"""
        return nome.upper().strip()
    
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
        nome_upper = nome_servico.upper()
        return 'TRANSFER' in nome_upper and 'OUT' in nome_upper
    
    def _eh_tour(self, nome_servico):
        """Verifica se é um serviço de tour"""
        nome_upper = nome_servico.upper()
        return ('TOUR' in nome_upper or 
                'VEÍCULO + GUIA À DISPOSIÇÃO' in nome_upper or
                'VEICULO + GUIA' in nome_upper)
    
    def _eh_guia_disposicao(self, nome_servico):
        """Verifica se é um serviço de guia à disposição"""
        nome_upper = nome_servico.upper()
        # Padrão: GUIA À DISPOSIÇÃO XX HORAS
        padrao = r'GUIA\s*À\s*DISPOSIÇÃO\s*\d+\s*HORAS?'
        return bool(re.search(padrao, nome_upper))

    def _otimizar_escala(self, escala):
        """Otimiza a distribuição dos serviços entre as vans"""
        logger.debug(f"Iniciando otimização para escala {escala.id}")
        
        # Implementação básica da otimização
        with transaction.atomic():
            escala.etapa = 'OTIMIZADA'
            escala.save()
            logger.info(f"Escala {escala.id} marcada como otimizada")


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
                
                # Calcular preço e veículo
                alocacao.calcular_preco_e_veiculo()
            
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
                    van_origem_alocacoes = AlocacaoVan.objects.filter(
                        escala=alocacao.escala,
                        van=van_origem
                    ).order_by('ordem')
                    
                    for i, alocacao_origem in enumerate(van_origem_alocacoes, 1):
                        if alocacao_origem.ordem != i:
                            alocacao_origem.ordem = i
                            alocacao_origem.save()
            
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


class ExcluirEscalaView(LoginRequiredMixin, View):
    """View para excluir uma escala"""
    
    def post(self, request, data):
        """Exclui uma escala específica"""
        try:
            data_obj = parse_data_brasileira(data)
            escala = get_object_or_404(Escala, data=data_obj)
            
            # Verificar se é seguro excluir
            if escala.etapa == 'OTIMIZADA':
                messages.warning(
                    request, 
                    f'Escala de {data_obj.strftime("%d/%m/%Y")} está otimizada. '
                    'Tem certeza que deseja excluir? Todos os dados serão perdidos permanentemente.'
                )
                
            # Salvar informações para a mensagem
            data_formatada = data_obj.strftime('%d/%m/%Y')
            total_servicos = escala.alocacoes.count()
            
            # Excluir escala (cascata exclui as alocações)
            with transaction.atomic():
                escala.delete()
            
            if total_servicos > 0:
                messages.success(
                    request,
                    f'Escala de {data_formatada} excluída com sucesso! '
                    f'{total_servicos} serviços foram removidos da escala.'
                )
            else:
                messages.success(
                    request,
                    f'Estrutura de escala de {data_formatada} excluída com sucesso!'
                )
            
        except Exception as e:
            messages.error(request, f'Erro ao excluir escala: {str(e)}')
            
        return redirect('escalas:gerenciar_escalas')
    
    def get(self, request, data):
        """Redireciona para gerenciamento se acessado via GET"""
        messages.info(request, 'Acesso inválido. Use o botão de exclusão na interface.')
        return redirect('escalas:gerenciar_escalas')


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
                
                # Reorganizar ordem das demais alocações na van
                alocacoes_restantes = AlocacaoVan.objects.filter(
                    escala=escala,
                    van=van
                ).order_by('ordem')
                
                for i, alocacao_restante in enumerate(alocacoes_restantes, 1):
                    if alocacao_restante.ordem != i:
                        alocacao_restante.ordem = i
                        alocacao_restante.save()
                
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
            
            novo_preco = Decimal(str(preco))
            
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
