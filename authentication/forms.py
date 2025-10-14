from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from .models import UserProfile


class UserForm(forms.ModelForm):
    """Formulário para dados básicos do usuário"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite seu primeiro nome'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite seu sobrenome'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite seu email'
            }),
        }
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'Email',
        }

    def clean_email(self):
        """Validar email único (exceto para o usuário atual)"""
        email = self.cleaned_data['email']
        user_id = self.instance.id if self.instance else None
        
        if User.objects.exclude(id=user_id).filter(email=email).exists():
            raise forms.ValidationError('Este email já está sendo usado por outro usuário.')
        
        return email


class UserProfileForm(forms.ModelForm):
    """Formulário para dados do perfil estendido"""
    
    class Meta:
        model = UserProfile
        fields = [
            'department',
            'theme_preference', 'language_preference', 'email_notifications'
        ]
        widgets = {
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Operações, Administração, etc.'
            }),
            'theme_preference': forms.Select(attrs={
                'class': 'form-select'
            }),
            'language_preference': forms.Select(attrs={
                'class': 'form-select'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'department': 'Departamento',
            'theme_preference': 'Tema Preferido',
            'language_preference': 'Idioma',
            'email_notifications': 'Receber notificações por email',
        }


class AvatarUploadForm(forms.Form):
    """Formulário específico para upload de avatar"""
    avatar = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Formatos aceitos: JPEG, PNG, GIF, WEBP. Tamanho máximo: 5MB.'
    )

    def clean_avatar(self):
        """Validar arquivo de avatar"""
        avatar = self.cleaned_data.get('avatar')
        
        if avatar:
            # Validar tamanho (5MB)
            if avatar.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Arquivo muito grande. Máximo 5MB.')
            
            # Validar tipo
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if avatar.content_type not in allowed_types:
                raise forms.ValidationError('Tipo de arquivo não permitido. Use JPEG, PNG, GIF ou WEBP.')
        
        return avatar


class PreferencesForm(forms.ModelForm):
    """Formulário apenas para preferências do usuário"""
    
    class Meta:
        model = UserProfile
        fields = ['theme_preference', 'language_preference', 'email_notifications']
        widgets = {
            'theme_preference': forms.Select(attrs={
                'class': 'form-select'
            }),
            'language_preference': forms.Select(attrs={
                'class': 'form-select'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }