from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages

class CustomLoginView(LoginView):
    template_name = 'authentication/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('escalas:gerenciar_escalas')
    
    def form_valid(self, form):
        messages.success(self.request, f'Bem-vindo(a), {form.get_user().get_full_name() or form.get_user().username}!')
        return super().form_valid(form)

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('authentication:login')
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'Logout realizado com sucesso!')
        return super().dispatch(request, *args, **kwargs)