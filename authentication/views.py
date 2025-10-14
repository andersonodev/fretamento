from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import UserProfile
from .forms import UserProfileForm, UserForm
import json
import os


class CustomLoginView(LoginView):
    template_name = 'authentication/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('core:home')
    
    def form_valid(self, form):
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('authentication:login')
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'Logout realizado com sucesso!')
        return super().dispatch(request, *args, **kwargs)


@login_required
def perfil(request):
    """View para exibir e editar o perfil do usuário"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Criar perfil se não existir
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('authentication:perfil')
        else:
            messages.error(request, 'Erro ao atualizar perfil. Verifique os dados informados.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile
    }
    return render(request, 'authentication/perfil.html', context)


@login_required
def alterar_senha(request):
    """View para alterar senha do usuário"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Manter usuário logado
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('authentication:perfil')
        else:
            messages.error(request, 'Erro ao alterar senha. Verifique os dados informados.')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {'form': form}
    return render(request, 'authentication/alterar_senha.html', context)


@login_required
@require_http_methods(["POST"])
def upload_avatar(request):
    """View AJAX para upload de avatar"""
    try:
        if 'avatar' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'Nenhum arquivo enviado'})
        
        avatar_file = request.FILES['avatar']
        
        # Validar tipo de arquivo
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if avatar_file.content_type not in allowed_types:
            return JsonResponse({
                'success': False, 
                'error': 'Tipo de arquivo não permitido. Use JPEG, PNG, GIF ou WEBP.'
            })
        
        # Validar tamanho (máximo 5MB)
        if avatar_file.size > 5 * 1024 * 1024:
            return JsonResponse({
                'success': False, 
                'error': 'Arquivo muito grande. Máximo 5MB.'
            })
        
        # Obter ou criar perfil
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Remover avatar anterior se existir
        if profile.avatar:
            try:
                if os.path.isfile(profile.avatar.path):
                    os.remove(profile.avatar.path)
            except:
                pass
        
        # Salvar novo avatar
        profile.avatar = avatar_file
        profile.save()
        
        return JsonResponse({
            'success': True, 
            'avatar_url': profile.get_avatar_url,
            'message': 'Avatar atualizado com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Erro interno: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def remover_avatar(request):
    """View AJAX para remover avatar"""
    try:
        profile = request.user.profile
        
        if profile.avatar:
            # Remover arquivo físico
            try:
                if os.path.isfile(profile.avatar.path):
                    os.remove(profile.avatar.path)
            except:
                pass
            
            # Limpar campo no banco
            profile.avatar = None
            profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Avatar removido com sucesso!'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Nenhum avatar para remover'
            })
            
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Perfil não encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def atualizar_preferencias(request):
    """View AJAX para atualizar preferências do usuário"""
    try:
        data = json.loads(request.body)
        profile = request.user.profile
        
        # Atualizar preferências
        if 'theme_preference' in data:
            profile.theme_preference = data['theme_preference']
        
        if 'language_preference' in data:
            profile.language_preference = data['language_preference']
        
        if 'email_notifications' in data:
            profile.email_notifications = data['email_notifications']
        
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Preferências atualizadas com sucesso!'
        })
        
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Perfil não encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        })