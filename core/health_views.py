"""
Health Check Views para Fretamento Intertouring
"""
import json
import time
from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from escalas.models import Escala
from core.models import Servico
import logging

logger = logging.getLogger(__name__)


class HealthCheckView(View):
    """
    Endpoint de health check para monitoramento
    """
    
    def get(self, request):
        """
        Retorna status de saúde da aplicação
        """
        start_time = time.time()
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {}
        }
        
        # Verificar banco de dados
        health_data['checks']['database'] = self._check_database()
        
        # Verificar cache
        health_data['checks']['cache'] = self._check_cache()
        
        # Verificar aplicação
        health_data['checks']['application'] = self._check_application()
        
        # Verificar espaço em disco
        health_data['checks']['disk_space'] = self._check_disk_space()
        
        # Calcular tempo de resposta
        health_data['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        # Determinar status geral
        all_healthy = all(
            check.get('status') == 'healthy' 
            for check in health_data['checks'].values()
        )
        
        if not all_healthy:
            health_data['status'] = 'unhealthy'
        
        # Status code baseado na saúde
        status_code = 200 if all_healthy else 503
        
        return JsonResponse(health_data, status=status_code)
    
    def _check_database(self):
        """Verificar conexão com banco de dados"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Verificar se consegue contar registros
            escalas_count = Escala.objects.count()
            servicos_count = Servico.objects.count()
            
            return {
                'status': 'healthy',
                'message': 'Database connection successful',
                'escalas_count': escalas_count,
                'servicos_count': servicos_count
            }
        except Exception as e:
            logger.error(f'Database health check failed: {e}')
            return {
                'status': 'unhealthy',
                'message': f'Database error: {str(e)}'
            }
    
    def _check_cache(self):
        """Verificar cache"""
        try:
            # Testar escrita e leitura no cache
            test_key = 'health_check_test'
            test_value = f'test_{int(time.time())}'
            
            cache.set(test_key, test_value, 10)
            cached_value = cache.get(test_key)
            
            if cached_value == test_value:
                cache.delete(test_key)
                return {
                    'status': 'healthy',
                    'message': 'Cache working properly'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'Cache read/write test failed'
                }
        except Exception as e:
            logger.error(f'Cache health check failed: {e}')
            return {
                'status': 'unhealthy',
                'message': f'Cache error: {str(e)}'
            }
    
    def _check_application(self):
        """Verificar componentes da aplicação"""
        try:
            checks = {}
            
            # Verificar imports principais
            try:
                from core.busca_inteligente_precos import BuscadorInteligentePrecosCodigoDoAnalista
                checks['price_search'] = 'healthy'
            except ImportError as e:
                checks['price_search'] = f'error: {e}'
            
            try:
                from escalas.services import GerenciadorEscalas
                checks['schedule_manager'] = 'healthy'
            except ImportError as e:
                checks['schedule_manager'] = f'error: {e}'
            
            try:
                from core.processors import ProcessadorPlanilhaOS
                checks['spreadsheet_processor'] = 'healthy'
            except ImportError as e:
                checks['spreadsheet_processor'] = f'error: {e}'
            
            # Verificar settings importantes
            checks['debug_mode'] = settings.DEBUG
            checks['allowed_hosts'] = len(settings.ALLOWED_HOSTS)
            
            all_healthy = all(
                check == 'healthy' 
                for check in checks.values() 
                if isinstance(check, str)
            )
            
            return {
                'status': 'healthy' if all_healthy else 'unhealthy',
                'message': 'Application components check',
                'details': checks
            }
        except Exception as e:
            logger.error(f'Application health check failed: {e}')
            return {
                'status': 'unhealthy',
                'message': f'Application error: {str(e)}'
            }
    
    def _check_disk_space(self):
        """Verificar espaço em disco"""
        try:
            import shutil
            
            # Verificar espaço no diretório da aplicação
            total, used, free = shutil.disk_usage('.')
            
            # Converter para GB
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            used_percent = (used / total) * 100
            
            # Alertar se uso > 90%
            status = 'healthy' if used_percent < 90 else 'warning'
            if used_percent > 95:
                status = 'unhealthy'
            
            return {
                'status': status,
                'message': f'Disk usage: {used_percent:.1f}%',
                'total_gb': round(total_gb, 2),
                'used_gb': round(used_gb, 2),
                'free_gb': round(free_gb, 2),
                'used_percent': round(used_percent, 1)
            }
        except Exception as e:
            logger.error(f'Disk space health check failed: {e}')
            return {
                'status': 'unhealthy',
                'message': f'Disk check error: {str(e)}'
            }


class MetricsView(View):
    """
    Endpoint de métricas para monitoramento
    """
    
    def get(self, request):
        """
        Retorna métricas da aplicação
        """
        try:
            metrics = {
                'timestamp': timezone.now().isoformat(),
                'database': self._get_database_metrics(),
                'application': self._get_application_metrics(),
                'system': self._get_system_metrics()
            }
            
            return JsonResponse(metrics)
        except Exception as e:
            logger.error(f'Metrics collection failed: {e}')
            return JsonResponse({
                'error': 'Failed to collect metrics',
                'message': str(e)
            }, status=500)
    
    def _get_database_metrics(self):
        """Coletar métricas do banco de dados"""
        try:
            from django.db.models import Count, Sum
            from datetime import datetime, timedelta
            
            # Contar registros principais
            escalas_total = Escala.objects.count()
            servicos_total = Servico.objects.count()
            
            # Escalas por status
            escalas_por_status = dict(
                Escala.objects.values_list('etapa')
                .annotate(count=Count('id'))
                .values_list('etapa', 'count')
            )
            
            # Escalas dos últimos 30 dias
            data_limite = timezone.now() - timedelta(days=30)
            escalas_recentes = Escala.objects.filter(
                created_at__gte=data_limite
            ).count()
            
            return {
                'escalas_total': escalas_total,
                'servicos_total': servicos_total,
                'escalas_por_status': escalas_por_status,
                'escalas_ultimo_mes': escalas_recentes
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_application_metrics(self):
        """Coletar métricas da aplicação"""
        try:
            import os
            
            return {
                'django_version': settings.DJANGO_VERSION if hasattr(settings, 'DJANGO_VERSION') else 'Unknown',
                'debug_mode': settings.DEBUG,
                'timezone': str(settings.TIME_ZONE),
                'language': settings.LANGUAGE_CODE,
                'process_id': os.getpid()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_system_metrics(self):
        """Coletar métricas do sistema"""
        try:
            import psutil
            import platform
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memória
            memory = psutil.virtual_memory()
            
            # Disco
            disk = psutil.disk_usage('.')
            
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_percent': cpu_percent,
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'percent': round((disk.used / disk.total) * 100, 1)
                }
            }
        except ImportError:
            # psutil não está instalado
            return {
                'error': 'psutil not available for system metrics'
            }
        except Exception as e:
            return {'error': str(e)}