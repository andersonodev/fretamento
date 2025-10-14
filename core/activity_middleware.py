from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from core.models import ActivityLog, Servico, ProcessamentoPlanilha
from escalas.models import Escala
import logging

logger = logging.getLogger(__name__)

class ActivityLogMiddleware(MiddlewareMixin):
    """Middleware para registrar atividades automaticamente"""
    
    def process_request(self, request):
        # Adicionar informações de request ao contexto para uso posterior
        request._activity_context = {
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        return None
    
    def get_client_ip(self, request):
        """Obter o IP real do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

# Signals para registrar atividades automaticamente

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Registra quando um usuário faz login"""
    ActivityLog.log_activity(
        user=user,
        activity_type='LOGIN',
        description=f'Usuário {user.username} fez login no sistema',
        details=f'Login realizado com sucesso às {timezone.now().strftime("%H:%M:%S")}',
        request=request
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Registra quando um usuário faz logout"""
    if user and user.is_authenticated:
        ActivityLog.log_activity(
            user=user,
            activity_type='LOGOUT',
            description=f'Usuário {user.username} fez logout do sistema',
            details=f'Logout realizado às {timezone.now().strftime("%H:%M:%S")}',
            request=request
        )

@receiver(post_save, sender=Servico)
def log_servico_activity(sender, instance, created, **kwargs):
    """Registra atividades relacionadas a serviços"""
    if hasattr(instance, '_current_user'):
        user = instance._current_user
        if created:
            ActivityLog.log_activity(
                user=user,
                activity_type='CREATE',
                description=f'Novo serviço criado: {instance.os}',
                details=f'Serviço {instance.os} - {instance.tipo} criado para {instance.rota}',
                object_type='Serviço',
                object_id=instance.id,
                extra_data={'os': instance.os, 'tipo': instance.tipo, 'rota': instance.rota}
            )
        else:
            ActivityLog.log_activity(
                user=user,
                activity_type='UPDATE',
                description=f'Serviço atualizado: {instance.os}',
                details=f'Serviço {instance.os} foi modificado',
                object_type='Serviço',
                object_id=instance.id,
                extra_data={'os': instance.os, 'tipo': instance.tipo}
            )

@receiver(post_delete, sender=Servico)
def log_servico_deletion(sender, instance, **kwargs):
    """Registra exclusão de serviços"""
    if hasattr(instance, '_current_user'):
        user = instance._current_user
        ActivityLog.log_activity(
            user=user,
            activity_type='DELETE',
            description=f'Serviço excluído: {instance.os}',
            details=f'Serviço {instance.os} - {instance.tipo} foi removido do sistema',
            object_type='Serviço',
            object_id=instance.id,
            extra_data={'os': instance.os, 'tipo': instance.tipo, 'rota': instance.rota}
        )

@receiver(post_save, sender=ProcessamentoPlanilha)
def log_processamento_activity(sender, instance, created, **kwargs):
    """Registra atividades relacionadas a processamentos de planilhas"""
    if hasattr(instance, '_current_user'):
        user = instance._current_user
        if created:
            ActivityLog.log_activity(
                user=user,
                activity_type='PROCESS',
                description=f'Nova planilha processada: {instance.nome_arquivo}',
                details=f'Processamento iniciado para {instance.nome_arquivo}',
                object_type='Processamento',
                object_id=instance.id,
                extra_data={
                    'nome_arquivo': instance.nome_arquivo,
                    'status': instance.status
                }
            )

@receiver(post_save, sender=Escala)
def log_escala_activity(sender, instance, created, **kwargs):
    """Registra atividades relacionadas a escalas"""
    if hasattr(instance, '_current_user'):
        user = instance._current_user
        if created:
            ActivityLog.log_activity(
                user=user,
                activity_type='CREATE',
                description=f'Nova escala criada para {instance.data}',
                details=f'Escala para {instance.data} criada com {instance.servicos.count()} serviços',
                object_type='Escala',
                object_id=instance.id,
                extra_data={'data': str(instance.data)}
            )
        else:
            ActivityLog.log_activity(
                user=user,
                activity_type='UPDATE',
                description=f'Escala atualizada: {instance.data}',
                details=f'Escala de {instance.data} foi modificada',
                object_type='Escala',
                object_id=instance.id,
                extra_data={'data': str(instance.data)}
            )

# Função helper para registrar atividades manuais
def log_custom_activity(user, activity_type, description, details='', object_type='', object_id='', request=None, extra_data=None):
    """Função helper para registrar atividades customizadas"""
    return ActivityLog.log_activity(
        user=user,
        activity_type=activity_type,
        description=description,
        details=details,
        object_type=object_type,
        object_id=object_id,
        request=request,
        extra_data=extra_data
    )