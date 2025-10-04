from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import ListView, DetailView
from django.utils.dateparse import parse_date
from django.db.models import Count, Sum, Q, Avg, Prefetch
from django.utils import timezone
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from datetime import datetime, date, timedelta
from core.models import Servico, ProcessamentoPlanilha
from escalas.models import Escala, AlocacaoVan
from core.processors import ProcessadorPlanilhaOS
from escalas.services import GerenciadorEscalas, ExportadorEscalas
from escalas.views import parse_data_brasileira
import json
import logging

logger = logging.getLogger(__name__)


class HomeView(View):
    """View principal do sistema com dashboard completo otimizado"""
    
    def get(self, request):
        # Tenta buscar do cache primeiro
        cache_key = f"dashboard_stats_{request.user.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info("Dashboard carregado do cache")
            return render(request, 'core/home.html', cached_data)
        
        logger.info("Gerando dashboard com consultas otimizadas")
        
        # Estatísticas básicas com uma única consulta
        stats_basicas = self._get_stats_basicas()
        
        # Estatísticas dos últimos 30 dias
        stats_30_dias = self._get_stats_30_dias()
        
        # Estatísticas detalhadas
        stats_detalhadas = self._get_stats_detalhadas()
        
        # Dados recentes
        dados_recentes = self._get_dados_recentes()
        
        # Informações do usuário
        user_info = {
            'nome': request.user.get_full_name() or request.user.username,
            'username': request.user.username,
            'ultimo_login': request.user.last_login,
            'permissoes_especiais': request.user.username in ['cristiane.aguiar', 'lucy.leite']
        }
        
        context = {
            **stats_basicas,
            **stats_30_dias,
            **stats_detalhadas,
            **dados_recentes,
            'user_info': user_info,
            'data_atual': timezone.now(),
        }
        
        # Cache por 5 minutos
        cache.set(cache_key, context, 300)
        
        return render(request, 'core/home.html', context)
    
    def _get_stats_basicas(self):
        """Estatísticas básicas com consulta otimizada"""
        servicos_stats = Servico.objects.aggregate(
            total_servicos=Count('id'),
            pax_medio=Avg('pax'),
            servicos_prioritarios=Count('id', filter=Q(eh_prioritario=True))
        )
        
        escalas_stats = Escala.objects.aggregate(
            escalas_criadas=Count('id'),
            escalas_aprovadas=Count('id', filter=Q(status='APROVADA')),
            escalas_pendentes=Count('id', filter=Q(status='PENDENTE'))
        )
        
        return {
            'total_servicos': servicos_stats['total_servicos'] or 0,
            'pax_medio': round(servicos_stats['pax_medio'] or 0, 1),
            'servicos_prioritarios': servicos_stats['servicos_prioritarios'] or 0,
            'escalas_criadas': escalas_stats['escalas_criadas'] or 0,
            'escalas_aprovadas': escalas_stats['escalas_aprovadas'] or 0,
            'escalas_pendentes': escalas_stats['escalas_pendentes'] or 0,
        }
    
    def _get_stats_30_dias(self):
        """Estatísticas dos últimos 30 dias"""
        data_30_dias = timezone.now().date() - timedelta(days=30)
        data_60_dias = timezone.now().date() - timedelta(days=60)
        
        # Consultas otimizadas em batch
        servicos_30_dias = Servico.objects.filter(
            data_do_servico__gte=data_30_dias
        ).count()
        
        servicos_60_dias = Servico.objects.filter(
            data_do_servico__gte=data_60_dias,
            data_do_servico__lt=data_30_dias
        ).count()
        
        escalas_30_dias = Escala.objects.filter(
            data__gte=data_30_dias
        ).count()
        
        # Cálculo de crescimento
        crescimento_servicos = 0
        if servicos_60_dias > 0:
            crescimento_servicos = ((servicos_30_dias - servicos_60_dias) / servicos_60_dias) * 100
        
        # Eficiência das vans (últimos 30 dias)
        van_stats = AlocacaoVan.objects.filter(
            escala__data__gte=data_30_dias
        ).aggregate(
            van1_servicos=Count('id', filter=Q(van='VAN1')),
            van2_servicos=Count('id', filter=Q(van='VAN2'))
        )
        
        return {
            'servicos_30_dias': servicos_30_dias,
            'escalas_30_dias': escalas_30_dias,
            'crescimento_servicos': round(crescimento_servicos, 1),
            'van1_servicos': van_stats['van1_servicos'] or 0,
            'van2_servicos': van_stats['van2_servicos'] or 0,
            'total_van_servicos': (van_stats['van1_servicos'] or 0) + (van_stats['van2_servicos'] or 0),
        }
    
    def _get_stats_detalhadas(self):
        """Estatísticas detalhadas por tipo, aeroporto, direção"""
        # Estatísticas por tipo de serviço
        stats_tipo = list(Servico.objects.values('tipo').annotate(
            total=Count('id'),
            pax_total=Sum('pax')
        ).order_by('-total')[:5])  # Top 5 apenas
        
        # Estatísticas por aeroporto
        stats_aeroporto = list(Servico.objects.exclude(
            aeroporto='N/A'
        ).values('aeroporto').annotate(
            total=Count('id')
        ).order_by('-total')[:5])  # Top 5 apenas
        
        # Estatísticas por direção
        stats_direcao = list(Servico.objects.exclude(
            direcao='N/A'
        ).values('direcao').annotate(
            total=Count('id')
        ).order_by('-total'))
        
        return {
            'stats_tipo': stats_tipo,
            'stats_aeroporto': stats_aeroporto,
            'stats_direcao': stats_direcao,
        }
    
    def _get_dados_recentes(self):
        """Dados recentes com prefetch otimizado"""
        # Processamentos recentes (apenas 5)
        processamentos_recentes = ProcessamentoPlanilha.objects.select_related().order_by('-created_at')[:5]
        
        # Escalas recentes (apenas 5)
        escalas_recentes = Escala.objects.select_related('aprovada_por').order_by('-data')[:5]
        
        return {
            'processamentos_recentes': processamentos_recentes,
            'escalas_recentes': escalas_recentes,
        }


class UploadPlanilhaView(View):
    """View para upload e processamento da planilha OS"""
    
    def get(self, request):
        return render(request, 'core/upload_planilha.html')
    
    def post(self, request):
        if 'arquivo' not in request.FILES:
            messages.error(request, 'Nenhum arquivo foi enviado.')
            return redirect('core:upload_planilha')
        
        arquivo = request.FILES['arquivo']
        
        # Valida tipo de arquivo
        if not arquivo.name.endswith(('.xlsx', '.xls', '.csv')):
            messages.error(request, 'Formato de arquivo não suportado. Use .xlsx, .xls ou .csv')
            return redirect('core:upload_planilha')
        
        try:
            # Processa a planilha
            processador = ProcessadorPlanilhaOS()
            servicos, processamento = processador.processar_planilha(arquivo)
            
            # Limpa cache relacionado após nova importação
            cache.delete_many([
                f"dashboard_stats_{request.user.id}",
                "lista_servicos_stats_*"
            ])
            
            messages.success(
                request, 
                f'Planilha processada com sucesso! {len(servicos)} serviços foram importados.'
            )
            
            return redirect('core:lista_servicos')
            
        except Exception as e:
            logger.error(f"Erro no upload: {e}")
            messages.error(request, f'Erro ao processar planilha: {str(e)}')
            return redirect('core:upload_planilha')


class ListaServicosView(ListView):
    """View para listar serviços com otimizações"""
    
    model = Servico
    template_name = 'core/lista_servicos.html'
    context_object_name = 'servicos'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related()
        
        # Filtros
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')
        tipo = self.request.GET.get('tipo')
        
        if data_inicio:
            queryset = queryset.filter(data_do_servico__gte=parse_data_brasileira(data_inicio))
        if data_fim:
            queryset = queryset.filter(data_do_servico__lte=parse_data_brasileira(data_fim))
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        return queryset.order_by('-data_do_servico', 'horario')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Cache das estatísticas por 5 minutos
        cache_key = f"lista_servicos_stats_{hash(str(self.request.GET))}"
        stats = cache.get(cache_key)
        
        if not stats:
            # Calcula estatísticas com uma única consulta
            queryset = self.get_queryset()
            stats = queryset.aggregate(
                total_transfers=Count('id', filter=Q(tipo='TRANSFER')),
                total_disposicoes=Count('id', filter=Q(tipo='DISPOSICAO')),
                total_tours=Count('id', filter=Q(tipo='TOUR'))
            )
            cache.set(cache_key, stats, 300)
        
        context.update(stats)
        return context


class GerenciarEscalasView(View):
    """View para gerenciar escalas"""
    
    def get(self, request):
        escalas = Escala.objects.order_by('-data')[:20]
        return render(request, 'escalas/gerenciar.html', {'escalas': escalas})
    
    def post(self, request):
        acao = request.POST.get('acao')
        data_str = request.POST.get('data')
        
        if not data_str:
            messages.error(request, 'Data é obrigatória.')
            return redirect('escalas:gerenciar_escalas')
        
        try:
            data_alvo = parse_data_brasileira(data_str)
            gerenciador = GerenciadorEscalas()
            
            if acao == 'criar':
                escala = gerenciador.criar_escala_do_dia(data_alvo)
                messages.success(request, f'Escala para {data_alvo.strftime("%d/%m/%Y")} criada com sucesso!')
                
            elif acao == 'puxar':
                escala = gerenciador.criar_escala_do_dia(data_alvo, force_recreate=True)
                messages.success(request, f'Dados puxados para {data_alvo.strftime("%d/%m/%Y")}!')
                
            elif acao == 'otimizar':
                escala = Escala.objects.get(data=data_alvo)
                escala = gerenciador.otimizar_escala(escala)
                messages.success(request, f'Escala para {data_alvo.strftime("%d/%m/%Y")} otimizada!')
                
            return redirect('escalas:visualizar_escala', data=data_str)
            
        except Escala.DoesNotExist:
            messages.error(request, 'Escala não encontrada. Crie a estrutura primeiro.')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
        
        return redirect('escalas:gerenciar_escalas')


class VisualizarEscalaView(DetailView):
    """View para visualizar uma escala específica"""
    
    model = Escala
    template_name = 'escalas/visualizar.html'
    context_object_name = 'escala'
    
    def get_object(self):
        data_str = self.kwargs.get('data')
        data = parse_data_brasileira(data_str)
        return get_object_or_404(Escala, data=data)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtém dados formatados da escala
        gerenciador = GerenciadorEscalas()
        dados_escala = gerenciador.obter_dados_escala(self.object)
        
        context.update(dados_escala)
        return context


class ExportarEscalaView(View):
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


class DiagnosticoView(View):
    """View para diagnóstico do sistema"""
    
    def get(self, request):
        # Coleta informações de diagnóstico
        diagnostico = {
            'total_servicos': Servico.objects.count(),
            'servicos_sem_horario': Servico.objects.filter(horario__isnull=True).count(),
            'servicos_prioritarios': Servico.objects.filter(eh_prioritario=True).count(),
            'escalas_criadas': Escala.objects.count(),
            'escalas_aprovadas': Escala.objects.filter(status='APROVADA').count(),
            'escalas_otimizadas': Escala.objects.filter(etapa='OTIMIZADA').count(),
            'processamentos': ProcessamentoPlanilha.objects.count(),
            'processamentos_erro': ProcessamentoPlanilha.objects.filter(status='ERRO').count(),
        }
        
        # Dados por data
        servicos_por_data = {}
        for servico in Servico.objects.all():
            data_key = servico.data_do_servico.strftime('%d-%m-%Y')
            if data_key not in servicos_por_data:
                servicos_por_data[data_key] = {'total': 0, 'com_horario': 0, 'prioritarios': 0}
            
            servicos_por_data[data_key]['total'] += 1
            if servico.horario:
                servicos_por_data[data_key]['com_horario'] += 1
            if servico.eh_prioritario:
                servicos_por_data[data_key]['prioritarios'] += 1
        
        context = {
            'diagnostico': diagnostico,
            'servicos_por_data': servicos_por_data,
        }
        
        return render(request, 'core/diagnostico.html', context)


# Views AJAX para melhor experiência do usuário
class StatusProcessamentoView(View):
    """View AJAX para verificar status de processamento"""
    
    def get(self, request, processamento_id):
        try:
            processamento = ProcessamentoPlanilha.objects.get(id=processamento_id)
            return JsonResponse({
                'status': processamento.status,
                'linhas_processadas': processamento.linhas_processadas,
                'linhas_erro': processamento.linhas_erro,
                'log': processamento.log_processamento,
            })
        except ProcessamentoPlanilha.DoesNotExist:
            return JsonResponse({'error': 'Processamento não encontrado'}, status=404)
