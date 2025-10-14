from django.urls import path
from . import views

app_name = 'escalas'

urlpatterns = [
    # Navegação hierárquica: Ano -> Mês -> Escalas
    path('', views.SelecionarAnoView.as_view(), name='selecionar_ano'),
    path('gerenciar/', views.SelecionarAnoView.as_view(), name='gerenciar_escalas'),  # Redirect para seleção de ano
    path('ano/<int:ano>/', views.SelecionarMesView.as_view(), name='selecionar_mes_ano'),
    path('gerenciar/<int:mes>/<int:ano>/', views.GerenciarEscalasView.as_view(), name='gerenciar_escalas_mes'),
    # Todas as URLs agora usam formato brasileiro DD-MM-YYYY
    path('puxar-dados/<str:data>/', views.PuxarDadosView.as_view(), name='puxar_dados'),
    path('visualizar/<str:data>/', views.VisualizarEscalaView.as_view(), name='visualizar_escala'),
    path('exportar/<str:data>/', views.ExportarEscalaView.as_view(), name='exportar_escala'),
    path('exportar-van/<str:data>/<str:van>/', views.ExportarVanEspecificaView.as_view(), name='exportar_van_especifica'),
    path('exportar-mes/<int:ano>/<int:mes>/', views.ExportarMesView.as_view(), name='exportar_mes'),
    path('excluir/<str:data>/', views.ExcluirEscalaView.as_view(), name='excluir_escala'),
    path('verificar-senha-exclusao/', views.VerificarSenhaExclusaoView.as_view(), name='verificar_senha_exclusao'),
    path('formatar-escala/', views.FormatarEscalaView.as_view(), name='formatar_escala'),
    
    path('mover-servico/', views.MoverServicoView.as_view(), name='mover_servico'),
    path('agrupar-servicos/', views.AgruparServicosView.as_view(), name='agrupar_servicos'),
    path('precificar/<str:data>/', views.PrecificarEscalaView.as_view(), name='precificar_escala'),
    path('desagrupar-servico/', views.DesagruparServicoView.as_view(), name='desagrupar_servico'),
    path('desagrupar-grupo-completo/', views.DesagruparGrupoCompletoView.as_view(), name='desagrupar_grupo_completo'),
    path('excluir-servico/', views.ExcluirServicoView.as_view(), name='excluir_servico'),
    path('detalhes-servico/', views.DetalhesServicoView.as_view(), name='detalhes_servico'),
    path('salvar-edicao-servico/', views.SalvarEdicaoServicoView.as_view(), name='salvar_edicao_servico'),
    path('detalhes-grupo/', views.DetalhesGrupoView.as_view(), name='detalhes_grupo'),
    path('salvar-edicao-grupo/', views.SalvarEdicaoGrupoView.as_view(), name='salvar_edicao_grupo'),
    path('editar-horario-servico/', views.EditarHorarioServicoView.as_view(), name='editar_horario_servico'),
    path('aprovar-escala/', views.AprovarEscalaView.as_view(), name='aprovar_escala'),
    
    # APIs para modal de tarifários
    path('api/servico/<int:alocacao_id>/', views.ApiServicoDetailView.as_view(), name='api_servico_detail'),
    path('api/tarifarios/', views.ApiTarifariosView.as_view(), name='api_tarifarios'),
    path('api/atualizar-preco/', views.ApiAtualizarPrecoView.as_view(), name='api_atualizar_preco'),
    path('api/detalhes-precificacao/<int:alocacao_id>/', views.ApiDetalhesPrecificacaoView.as_view(), name='api_detalhes_precificacao'),
    path('desfazer-agrupamentos-automaticos/', views.DesfazerAgrupamentosAutomaticosView.as_view(), name='desfazer_agrupamentos_automaticos'),
    path('toggle-status-alocacao/', views.ToggleStatusAlocacaoView.as_view(), name='toggle_status_alocacao'),
    path('adicionar-servico-manual/', views.AdicionarServicoManualView.as_view(), name='adicionar_servico_manual'),
]