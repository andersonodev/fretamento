from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class ActivityLog(models.Model):
    ACTIVITY_TYPES = [
        ('CREATE', 'Criação'),
        ('UPDATE', 'Atualização'),
        ('DELETE', 'Exclusão'),
        ('UPLOAD', 'Upload'),
        ('DOWNLOAD', 'Download'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('VIEW', 'Visualização'),
        ('EXPORT', 'Exportação'),
        ('IMPORT', 'Importação'),
        ('GENERATE', 'Geração'),
        ('PROCESS', 'Processamento'),
        ('ERROR', 'Erro'),
        ('SUCCESS', 'Sucesso'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    object_type = models.CharField(max_length=50, blank=True)  # Ex: 'Arquivo', 'Escala', 'Serviço'
    object_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'core_activity_log'
        verbose_name = 'Log de Atividade'
        verbose_name_plural = 'Logs de Atividades'

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.description}"

    def get_icon(self):
        """Retorna o ícone FontAwesome baseado no tipo de atividade"""
        icons = {
            'CREATE': 'fas fa-plus-circle',
            'UPDATE': 'fas fa-edit',
            'DELETE': 'fas fa-trash',
            'UPLOAD': 'fas fa-cloud-upload-alt',
            'DOWNLOAD': 'fas fa-download',
            'LOGIN': 'fas fa-sign-in-alt',
            'LOGOUT': 'fas fa-sign-out-alt',
            'VIEW': 'fas fa-eye',
            'EXPORT': 'fas fa-file-export',
            'IMPORT': 'fas fa-file-import',
            'GENERATE': 'fas fa-cogs',
            'PROCESS': 'fas fa-spinner',
            'ERROR': 'fas fa-exclamation-triangle',
            'SUCCESS': 'fas fa-check-circle',
        }
        return icons.get(self.activity_type, 'fas fa-circle')

    def get_color_class(self):
        """Retorna a classe de cor baseada no tipo de atividade"""
        colors = {
            'CREATE': 'success',
            'UPDATE': 'primary',
            'DELETE': 'danger',
            'UPLOAD': 'info',
            'DOWNLOAD': 'secondary',
            'LOGIN': 'success',
            'LOGOUT': 'warning',
            'VIEW': 'light',
            'EXPORT': 'info',
            'IMPORT': 'info',
            'GENERATE': 'primary',
            'PROCESS': 'warning',
            'ERROR': 'danger',
            'SUCCESS': 'success',
        }
        return colors.get(self.activity_type, 'secondary')

    @classmethod
    def log_activity(cls, user, activity_type, description, details='', object_type='', 
                    object_id='', request=None, extra_data=None):
        """Método helper para registrar atividades"""
        ip_address = None
        user_agent = ''
        
        if request:
            # Obter IP real considerando proxies
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        return cls.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            details=details,
            object_type=object_type,
            object_id=str(object_id) if object_id else '',
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data or {}
        )