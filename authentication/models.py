from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import os


class UserProfile(models.Model):
    """
    Perfil estendido do usuário para informações adicionais
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(
        upload_to='profiles/avatars/', 
        null=True, 
        blank=True,
        help_text="Foto de perfil do usuário"
    )
    department = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Departamento ou setor"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Configurações de preferências
    theme_preference = models.CharField(
        max_length=10,
        choices=[
            ('light', 'Claro'),
            ('dark', 'Escuro'),
        ],
        default='light',
        help_text="Tema preferido da interface"
    )
    language_preference = models.CharField(
        max_length=10,
        choices=[
            ('pt-br', 'Português (Brasil)'),
            ('en', 'English'),
        ],
        default='pt-br',
        help_text="Idioma preferido"
    )
    email_notifications = models.BooleanField(
        default=True,
        help_text="Receber notificações por email"
    )

    class Meta:
        verbose_name = "Perfil do Usuário"
        verbose_name_plural = "Perfis dos Usuários"
        ordering = ['-created_at']

    def __str__(self):
        return f"Perfil de {self.user.get_full_name() or self.user.username}"

    @property
    def get_avatar_url(self):
        """Retorna a URL do avatar ou uma imagem padrão"""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return '/static/images/default-avatar.svg'

    @property
    def get_display_name(self):
        """Retorna o nome completo ou username"""
        return self.user.get_full_name() or self.user.username

    @property
    def is_admin(self):
        """Verifica se o usuário é administrador"""
        return self.user.is_superuser or self.user.is_staff

    def delete(self, *args, **kwargs):
        """Override delete para remover avatar ao deletar perfil"""
        if self.avatar:
            # Remove o arquivo físico
            if os.path.isfile(self.avatar.path):
                os.remove(self.avatar.path)
        super().delete(*args, **kwargs)


# Signal para criar perfil automaticamente quando um usuário é criado
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Cria automaticamente um perfil quando um usuário é criado"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Salva o perfil quando o usuário é salvo"""
    if hasattr(instance, 'profile'):
        instance.profile.save()