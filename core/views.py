from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import ListView, DetailView
from django.utils.dateparse import parse_date
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import datetime, date, timedelta
from core.models import Servico, ProcessamentoPlanilha
from escalas.models import Escala, AlocacaoVan
from core.processors import ProcessadorPlanilhaOS
from escalas.services import GerenciadorEscalas, ExportadorEscalas
import json


class HomeView(View):
    """View principal do sistema com dashboard completo"""
    
    def get(self, request):
        # Estatísticas gerais do sistema
        total_servicos = Servico.objects.count()
        escalas_criadas = Escala.objects.count()
        escalas_aprovadas = Escala.objects.filter(status='APROVADA').count()
        escalas_pendentes = Escala.objects.filter(status='PENDENTE').count()
        
        # Estatísticas dos últimos 30 dias
        data_30_dias = timezone.now().date() - timedelta(days=30)
        servicos_recentes = Servico.objects.filter(data_do_servico__gte=data_30_dias)
        escalas_recentes = Escala.objects.filter(data__gte=data_30_dias)
        
        # Estatísticas por tipo de serviço
        stats_tipo = Servico.objects.values('tipo').annotate(
            total=Count('id'),
            pax_total=Sum('pax')
        ).order_by('-total')
        
        # Estatísticas por aeroporto
        stats_aeroporto = Servico.objects.exclude(aeroporto='N/A').values('aeroporto').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Estatísticas por direção
        stats_direcao = Servico.objects.exclude(direcao='N/A').values('direcao').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Processamentos recentes
        processamentos_recentes = ProcessamentoPlanilha.objects.order_by('-created_at')[:5]
        
        # Escalas recentes
        escalas_recentes_list = Escala.objects.order_by('-data')[:5]
        
        # Eficiência das vans (últimos 30 dias)
        van1_servicos = AlocacaoVan.objects.filter(
            escala__data__gte=data_30_dias,
            van='VAN1'
        ).count()
        
        van2_servicos = AlocacaoVan.objects.filter(
            escala__data__gte=data_30_dias,
            van='VAN2'
        ).count()
        
        # PAX médio por serviço
        pax_medio = Servico.objects.aggregate(Avg('pax'))['pax__avg'] or 0
        
        # Serviços prioritários
        servicos_prioritarios = Servico.objects.filter(eh_prioritario=True).count()
        
        # Taxa de crescimento (comparação com os 30 dias anteriores)
        data_60_dias = timezone.now().date() - timedelta(days=60)
        servicos_periodo_anterior = Servico.objects.filter(
            data_do_servico__gte=data_60_dias,
            data_do_servico__lt=data_30_dias
        ).count()
        
        crescimento_servicos = 0
        if servicos_periodo_anterior > 0:
            crescimento_servicos = ((servicos_recentes.count() - servicos_periodo_anterior) / servicos_periodo_anterior) * 100
        
        # Dados do usuário atual
        user_info = {
            'nome': request.user.get_full_name() or request.user.username,
            'username': request.user.username,
            'ultimo_login': request.user.last_login,
            'permissoes_especiais': request.user.username in ['cristiane.aguiar', 'lucy.leite']
        }
        
        context = {
            # Estatísticas principais
            'total_servicos': total_servicos,
            'escalas_criadas': escalas_criadas,
            'escalas_aprovadas': escalas_aprovadas,
            'escalas_pendentes': escalas_pendentes,
            
            # Estatísticas dos últimos 30 dias
            'servicos_30_dias': servicos_recentes.count(),
            'escalas_30_dias': escalas_recentes.count(),
            'crescimento_servicos': round(crescimento_servicos, 1),
            
            # Estatísticas detalhadas
            'stats_tipo': stats_tipo,
            'stats_aeroporto': stats_aeroporto,
            'stats_direcao': stats_direcao,
            'pax_medio': round(pax_medio, 1),
            'servicos_prioritarios': servicos_prioritarios,
            
            # Eficiência das vans
            'van1_servicos': van1_servicos,
            'van2_servicos': van2_servicos,
            'total_van_servicos': van1_servicos + van2_servicos,
            
            # Dados recentes
            'processamentos_recentes': processamentos_recentes,
            'escalas_recentes': escalas_recentes_list,
            
            # Informações do usuário
            'user_info': user_info,
            
            # Data atual
            'data_atual': timezone.now(),
        }
        
        return render(request, 'core/home.html', context)


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
            
            # Salva os serviços no banco
            Servico.objects.bulk_create(servicos)
            
            messages.success(
                request, 
                f'Planilha processada com sucesso! {len(servicos)} serviços foram importados.'
            )
            
            return redirect('core:lista_servicos')
            
        except Exception as e:
            messages.error(request, f'Erro ao processar planilha: {str(e)}')
            return redirect('core:upload_planilha')


class ListaServicosView(ListView):
    """View para listar serviços"""
    
    model = Servico
    template_name = 'core/lista_servicos.html'
    context_object_name = 'servicos'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')
        tipo = self.request.GET.get('tipo')
        
        if data_inicio:
            queryset = queryset.filter(data_do_servico__gte=parse_date(data_inicio))
        if data_fim:
            queryset = queryset.filter(data_do_servico__lte=parse_date(data_fim))
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        return queryset.order_by('-data_do_servico', 'horario')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Aplica os mesmos filtros para estatísticas
        queryset = self.get_queryset()
        
        # Calcula estatísticas
        context['total_transfers'] = queryset.filter(tipo='TRANSFER').count()
        context['total_disposicoes'] = queryset.filter(tipo='DISPOSICAO').count()
        context['total_tours'] = queryset.filter(tipo='TOUR').count()
        
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
            data_alvo = parse_date(data_str)
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
        data = parse_date(data_str)
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
        data_obj = parse_date(data)
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
            data_key = servico.data_do_servico.strftime('%Y-%m-%d')
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
