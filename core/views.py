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
        # Verificar se o usuário está autenticado
        if not request.user.is_authenticated:
            return redirect('authentication:login')
            
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
            'permissoes_especiais': request.user.is_superuser or request.user.is_staff
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
        # Importar ActivityLog do models principal
        from core.models import ActivityLog
        
        # Atividades recentes do sistema (últimas 10)
        atividades_recentes = ActivityLog.objects.select_related('user').order_by('-created_at')[:10]
        
        # Processamentos recentes (apenas 5)
        processamentos_recentes = ProcessamentoPlanilha.objects.select_related().order_by('-created_at')[:5]
        
        # Escalas recentes (apenas 5)
        escalas_recentes = Escala.objects.select_related('aprovada_por').order_by('-data')[:5]
        
        return {
            'atividades_recentes': atividades_recentes,
            'processamentos_recentes': processamentos_recentes,
            'escalas_recentes': escalas_recentes,
        }


class UploadPlanilhaView(View):
    """View para upload e processamento da planilha OS"""
    
    def get(self, request):
        # Log de acesso à página de upload
        from core.activity_utils import log_activity
        log_activity(
            request=request,
            activity_type='VIEW',
            description='Página de upload acessada',
            details='Usuário acessou a interface de upload de planilhas'
        )
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
            
            # Atualiza informações adicionais do processamento
            if processamento:
                processamento.tamanho_arquivo = arquivo.size
                processamento.usuario_upload = request.user.username
                processamento.total_servicos_criados = len(servicos)
                
                # Determina período dos serviços
                if servicos:
                    datas_servicos = [s.data_do_servico for s in servicos]
                    processamento.data_primeira_linha = min(datas_servicos)
                    processamento.data_ultima_linha = max(datas_servicos)
                
                processamento.save()
            
            # Limpa cache relacionado após nova importação
            cache.delete_many([
                f"dashboard_stats_{request.user.id}",
                "lista_servicos_stats_*"
            ])
            
            # Log da atividade de upload bem-sucedido
            from core.activity_utils import log_activity
            log_activity(
                request=request,
                activity_type='UPLOAD',
                description=f'Upload de planilha realizado: {arquivo.name}',
                details=f'Arquivo {arquivo.name} processado com {len(servicos)} serviços importados',
                object_type='Arquivo',
                object_id=str(processamento.id) if processamento else '',
                extra_data={
                    'arquivo_nome': arquivo.name,
                    'arquivo_tamanho': arquivo.size,
                    'servicos_importados': len(servicos)
                }
            )
            
            messages.success(
                request, 
                f'Planilha processada com sucesso! {len(servicos)} serviços foram importados.'
            )
            
            return redirect('core:lista_arquivos')
            
        except Exception as e:
            logger.error(f"Erro no upload: {e}")
            messages.error(request, f'Erro ao processar planilha: {str(e)}')
            return redirect('core:upload_planilha')


class ListaArquivosView(ListView):
    """View para listar arquivos uploadados"""
    
    model = ProcessamentoPlanilha
    template_name = 'core/lista_arquivos.html'
    context_object_name = 'arquivos'
    paginate_by = 20
    
    def get_queryset(self):
        return ProcessamentoPlanilha.objects.filter(
            status='CONCLUIDO'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Importar aqui para evitar dependência circular
        from escalas.models import AlocacaoVan
        
        # Estatísticas dos arquivos com queries otimizadas
        queryset = self.get_queryset()
        total_arquivos = queryset.count()
        
        # Calcular total de serviços de forma mais eficiente
        total_servicos_calculado = 0
        for arquivo in queryset:
            if arquivo.total_servicos_criados:
                total_servicos_calculado += arquivo.total_servicos_criados
            else:
                # Fallback: contar serviços reais
                servicos_count = Servico.objects.filter(arquivo_origem=arquivo.nome_arquivo).count()
                total_servicos_calculado += servicos_count
        
        # Adicionar informações sobre serviços escalados para cada arquivo
        arquivos_com_info = []
        arquivos_queryset = context.get('arquivos', []) or context.get('object_list', [])
        
        for arquivo in arquivos_queryset:
            # Buscar serviços relacionados
            servicos = Servico.objects.filter(arquivo_origem=arquivo.nome_arquivo)
            
            if not servicos.exists():
                # Fallback por data
                servicos = Servico.objects.filter(created_at__date=arquivo.created_at.date())
            
            # Contar serviços escalados
            servicos_escalados = 0
            for servico in servicos:
                if AlocacaoVan.objects.filter(servico=servico).exists():
                    servicos_escalados += 1
            
            # Adicionar informações ao arquivo
            arquivo.total_servicos = servicos.count()
            arquivo.servicos_escalados = servicos_escalados
            arquivo.servicos_deletaveis = arquivo.total_servicos - servicos_escalados
            arquivo.pode_deletar_completo = (servicos_escalados == 0 and arquivo.total_servicos > 0)
            
            # Adicionar propriedades auxiliares para o template
            if not hasattr(arquivo, 'tamanho_formatado'):
                arquivo.tamanho_formatado = f"{arquivo.tamanho_arquivo / 1024:.1f} KB" if arquivo.tamanho_arquivo else "N/A"
            
            if not hasattr(arquivo, 'periodo_servicos'):
                if arquivo.data_primeira_linha and arquivo.data_ultima_linha:
                    arquivo.periodo_servicos = f"{arquivo.data_primeira_linha.strftime('%d/%m')} - {arquivo.data_ultima_linha.strftime('%d/%m/%Y')}"
                elif arquivo.data_primeira_linha:
                    arquivo.periodo_servicos = arquivo.data_primeira_linha.strftime('%d/%m/%Y')
                else:
                    arquivo.periodo_servicos = "N/A"
            
            arquivos_com_info.append(arquivo)
        
        # Verificar se há dados reais e debug
        logger.info(f"Lista Arquivos - Total arquivos: {total_arquivos}, Total serviços: {total_servicos_calculado}")
        
        # Formatação da hora atual
        hora_atual = timezone.now().strftime('%d/%m/%Y às %H:%M')
        logger.info(f"Hora formatada: {hora_atual}")
        
        context.update({
            'total_arquivos': total_arquivos,
            'total_servicos': total_servicos_calculado,
            'arquivos': arquivos_com_info,
            'arquivos_ativos': len(arquivos_com_info),
            'ultima_atualizacao': hora_atual,
        })
        return context


class ServicosArquivoView(ListView):
    """View para listar serviços de um arquivo específico"""
    
    model = Servico
    template_name = 'core/lista_servicos.html'
    context_object_name = 'servicos'
    paginate_by = 50
    
    def get_queryset(self):
        arquivo_id = self.kwargs.get('arquivo_id')
        self.arquivo = get_object_or_404(ProcessamentoPlanilha, id=arquivo_id, status='CONCLUIDO')
        
        # Primeiro tenta usar o campo arquivo_origem para associação direta
        queryset = Servico.objects.filter(
            arquivo_origem=self.arquivo.nome_arquivo
        ).select_related()
        
        # Se não encontrar serviços com arquivo_origem, usa data como fallback
        if not queryset.exists():
            data_upload = self.arquivo.created_at.date()
            queryset = Servico.objects.filter(
                created_at__date=data_upload
            ).select_related()
        
        # Aplicar filtros da URL
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
        
        # Informações do arquivo
        context['arquivo'] = self.arquivo
        context['mostrar_info_arquivo'] = True
        
        # Cache das estatísticas por 5 minutos
        cache_key = f"servicos_arquivo_stats_{self.arquivo.id}_{hash(str(self.request.GET))}"
        stats = cache.get(cache_key)
        
        if not stats:
            queryset = self.get_queryset()
            stats = queryset.aggregate(
                total_transfers=Count('id', filter=Q(tipo='TRANSFER')),
                total_disposicoes=Count('id', filter=Q(tipo='DISPOSICAO')),
                total_tours=Count('id', filter=Q(tipo='TOUR'))
            )
            cache.set(cache_key, stats, 300)
        
        context.update(stats)
        return context


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
class DeletarArquivoView(View):
    """View para deletar arquivo e seus serviços relacionados"""
    
    def post(self, request, arquivo_id):
        try:
            arquivo = get_object_or_404(ProcessamentoPlanilha, id=arquivo_id)
            nome_arquivo = arquivo.nome_arquivo
            
            logger.info(f"Iniciando deleção do arquivo {nome_arquivo} pelo usuário {request.user.username}")
            
            # Busca serviços relacionados a este arquivo
            servicos_relacionados = Servico.objects.filter(arquivo_origem=arquivo.nome_arquivo)
            
            # Se não encontrar por nome do arquivo, tenta por data (fallback)
            if not servicos_relacionados.exists():
                data_upload = arquivo.created_at.date()
                servicos_relacionados = Servico.objects.filter(created_at__date=data_upload)
                logger.info(f"Usando fallback por data para arquivo {nome_arquivo}: {servicos_relacionados.count()} serviços encontrados")
            
            # Verifica se há serviços escalados (protegidos)
            from escalas.models import AlocacaoVan
            servicos_escalados = []
            servicos_deletaveis = []
            
            for servico in servicos_relacionados:
                # Verifica se o serviço tem alguma alocação de van (está escalado)
                tem_escala = AlocacaoVan.objects.filter(
                    servico_id=servico.id
                ).exists()
                
                if tem_escala:
                    servicos_escalados.append(servico)
                else:
                    servicos_deletaveis.append(servico)
            
            logger.info(f"Arquivo {nome_arquivo}: {len(servicos_deletaveis)} serviços deletáveis, {len(servicos_escalados)} protegidos")
            
            # Preparar mensagens de resposta
            mensagens = []
            
            # Informa sobre serviços escalados que não podem ser deletados
            if servicos_escalados:
                mensagem_protegidos = f'{len(servicos_escalados)} serviços não foram deletados pois já estão escalados e são protegidos.'
                mensagens.append({'tipo': 'warning', 'texto': mensagem_protegidos})
                
                if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    messages.warning(request, mensagem_protegidos)
            
            # Deleta serviços que não estão escalados
            if servicos_deletaveis:
                for servico in servicos_deletaveis:
                    servico.delete()
                
                logger.info(f"Deletados {len(servicos_deletaveis)} serviços do arquivo {nome_arquivo}")
                mensagem_deletados = f'{len(servicos_deletaveis)} serviços foram deletados com sucesso.'
                mensagens.append({'tipo': 'success', 'texto': mensagem_deletados})
                
                if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    messages.success(request, mensagem_deletados)
            
            # Se não há mais serviços relacionados, deleta o arquivo
            servicos_restantes = Servico.objects.filter(arquivo_origem=arquivo.nome_arquivo)
            if not servicos_restantes.exists():
                arquivo.delete()  # Deleta o arquivo físico e o registro
                logger.info(f"Arquivo {nome_arquivo} deletado completamente")
                mensagem_arquivo = f'Arquivo "{nome_arquivo}" foi deletado completamente.'
                mensagens.append({'tipo': 'success', 'texto': mensagem_arquivo})
                
                if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    messages.success(request, mensagem_arquivo)
            else:
                logger.info(f"Arquivo {nome_arquivo} mantido com {servicos_restantes.count()} serviços escalados")
                mensagem_mantido = f'Arquivo mantido pois ainda há {servicos_restantes.count()} serviços escalados relacionados.'
                mensagens.append({'tipo': 'info', 'texto': mensagem_mantido})
                
                if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    messages.info(request, mensagem_mantido)
            
            # Limpa cache relacionado
            cache.delete_many([
                f"dashboard_stats_{request.user.id}",
                "lista_servicos_stats_*"
            ])
            
            # Se for requisição AJAX, retorna JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'mensagens': mensagens,
                    'arquivo_deletado': not servicos_restantes.exists(),
                    'servicos_deletados': len(servicos_deletaveis),
                    'servicos_protegidos': len(servicos_escalados)
                })
            
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo {arquivo_id}: {e}")
            erro_msg = f'Erro ao deletar arquivo: {str(e)}'
            
            # Se for requisição AJAX, retorna erro JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'mensagem': erro_msg
                }, status=400)
            
            messages.error(request, erro_msg)
        
        return redirect('core:lista_arquivos')


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


class ListaAtividadesView(ListView):
    """View para listar todas as atividades do sistema"""
    template_name = 'core/lista_atividades.html'
    context_object_name = 'atividades'
    paginate_by = 50
    
    def get_queryset(self):
        from core.models import ActivityLog
        self.model = ActivityLog
        queryset = ActivityLog.objects.select_related('user').order_by('-created_at')
        
        # Filtros opcionais
        activity_type = self.request.GET.get('tipo')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        user_id = self.request.GET.get('usuario')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import ActivityLog
        from django.contrib.auth.models import User
        
        # Log de acesso à página
        from core.activity_utils import log_activity
        log_activity(
            request=self.request,
            activity_type='VIEW',
            description='Lista de atividades acessada',
            details='Usuário visualizou o histórico completo de atividades'
        )
        
        # Adicionar opções de filtro
        context['tipos_atividade'] = ActivityLog.ACTIVITY_TYPES
        context['usuarios'] = User.objects.filter(
            activity_logs__isnull=False
        ).distinct().order_by('username')
        
        # Filtros aplicados
        context['filtro_tipo'] = self.request.GET.get('tipo', '')
        context['filtro_usuario'] = self.request.GET.get('usuario', '')
        
        return context


class TesteLoadingView(View):
    """View temporária para demonstrar o sistema de loading"""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('authentication:login')
            
        return render(request, 'core/teste_loading.html')
