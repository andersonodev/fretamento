from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('alterar-senha/', views.alterar_senha, name='alterar_senha'),
    path('ajax/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('ajax/remover-avatar/', views.remover_avatar, name='remover_avatar'),
    path('ajax/atualizar-preferencias/', views.atualizar_preferencias, name='atualizar_preferencias'),
]