from django.urls import path
from . import views

app_name = 'escalas'

urlpatterns = [
    path('gerenciar/', views.GerenciarEscalasView.as_view(), name='gerenciar_escalas'),
    # Todas as URLs agora usam formato brasileiro DD-MM-YYYY
    path('puxar-dados/<str:data>/', views.PuxarDadosView.as_view(), name='puxar_dados'),
    path('visualizar/<str:data>/', views.VisualizarEscalaView.as_view(), name='visualizar_escala'),
    path('exportar/<str:data>/', views.ExportarEscalaView.as_view(), name='exportar_escala'),
    path('excluir/<str:data>/', views.ExcluirEscalaView.as_view(), name='excluir_escala'),
    
    path('mover-servico/', views.MoverServicoView.as_view(), name='mover_servico'),
    path('agrupar-servicos/', views.AgruparServicosView.as_view(), name='agrupar_servicos'),
    path('desagrupar-servico/', views.DesagruparServicoView.as_view(), name='desagrupar_servico'),
    path('desagrupar-grupo-completo/', views.DesagruparGrupoCompletoView.as_view(), name='desagrupar_grupo_completo'),
    path('excluir-servico/', views.ExcluirServicoView.as_view(), name='excluir_servico'),
    path('detalhes-servico/', views.DetalhesServicoView.as_view(), name='detalhes_servico'),
    path('salvar-edicao-servico/', views.SalvarEdicaoServicoView.as_view(), name='salvar_edicao_servico'),
    path('detalhes-grupo/', views.DetalhesGrupoView.as_view(), name='detalhes_grupo'),
    path('salvar-edicao-grupo/', views.SalvarEdicaoGrupoView.as_view(), name='salvar_edicao_grupo'),
    path('aprovar-escala/', views.AprovarEscalaView.as_view(), name='aprovar_escala'),
    
    # APIs para modal de tarifários
    path('api/servico/<int:alocacao_id>/', views.ApiServicoDetailView.as_view(), name='api_servico_detail'),
    path('api/atualizar-preco/', views.ApiAtualizarPrecoView.as_view(), name='api_atualizar_preco'),
    path('desfazer-agrupamentos-automaticos/', views.DesfazerAgrupamentosAutomaticosView.as_view(), name='desfazer_agrupamentos_automaticos'),
]