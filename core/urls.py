from django.urls import path
from . import views
from . import views_tarifarios
from .health_views import HealthCheckView, MetricsView
from escalas.views import ApiTarifariosView

app_name = 'core'

urlpatterns = [
    # Views principais
    path('', views.HomeView.as_view(), name='home'),
    path('upload/', views.UploadPlanilhaView.as_view(), name='upload_planilha'),
    path('atividades/', views.ListaAtividadesView.as_view(), name='lista_atividades'),
    
    # API endpoints
    path('api/dashboard/updates/', views.DashboardUpdatesView.as_view(), name='dashboard_updates'),
    
    # Arquivos e serviços
    path('arquivos/', views.ListaArquivosView.as_view(), name='lista_arquivos'),
    path('arquivos/<int:arquivo_id>/servicos/', views.ServicosArquivoView.as_view(), name='servicos_arquivo'),
    path('arquivos/<int:arquivo_id>/deletar/', views.DeletarArquivoView.as_view(), name='deletar_arquivo'),
    path('servicos/', views.ListaServicosView.as_view(), name='lista_servicos'),
    
    path('processamento/<int:processamento_id>/status/', 
         views.StatusProcessamentoView.as_view(), name='status_processamento'),
    
    # Views de tarifários e preços
    path('tarifarios/', views_tarifarios.visualizar_tarifarios, name='visualizar_tarifarios'),
    path('simulador-precos/', views_tarifarios.simulador_precos, name='simulador_precos'),
    path('buscar-preco/', views_tarifarios.buscar_preco_tarifario, name='buscar_preco'),
    path('historico-calculos/', views_tarifarios.historico_calculos, name='historico_calculos'),
    path('api/calcular-preco/', views_tarifarios.api_calcular_preco, name='api_calcular_preco'),
    path('api/tarifarios/', ApiTarifariosView.as_view(), name='api_tarifarios'),
    
    # Health Check e Métricas
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('metrics/', MetricsView.as_view(), name='metrics'),
]