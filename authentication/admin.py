from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline para mostrar o perfil junto com o usuário"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'
    fields = [
        'avatar', 'department',
        'theme_preference', 'language_preference', 'email_notifications'
    ]


class UserAdmin(BaseUserAdmin):
    """Admin customizado para incluir o perfil do usuário"""
    inlines = (UserProfileInline,)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin para gerenciar perfis de usuário"""
    list_display = [
        'user', 'get_display_name', 'department', 
        'theme_preference', 'created_at'
    ]
    list_filter = [
        'department', 'theme_preference', 'language_preference',
        'email_notifications', 'created_at'
    ]
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'user__email', 'department'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Informações Pessoais', {
            'fields': ('avatar', 'department')
        }),
        ('Preferências', {
            'fields': ('theme_preference', 'language_preference', 'email_notifications')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_display_name(self, obj):
        """Retorna o nome de exibição do usuário"""
        return obj.get_display_name
    get_display_name.short_description = 'Nome'
    get_display_name.admin_order_field = 'user__first_name'


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)