from django.contrib import admin
from .models import Servico, GrupoServico, ServicoGrupo, ProcessamentoPlanilha, CalculoPreco


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ['servico', 'cliente', 'data_do_servico', 'horario', 'pax', 'eh_prioritario', 'tipo', 'regiao']
    list_filter = ['data_do_servico', 'tipo', 'regiao', 'eh_prioritario', 'eh_regular']
    search_fields = ['servico', 'cliente', 'numero_venda']
    readonly_fields = ['tipo', 'direcao', 'aeroporto', 'regiao', 'eh_regular', 'eh_prioritario']
    ordering = ['-data_do_servico', 'horario']
    date_hierarchy = 'data_do_servico'


@admin.register(GrupoServico)
class GrupoServicoAdmin(admin.ModelAdmin):
    list_display = ['nome_servico', 'data_servico', 'horario_base', 'pax_total', 'eh_prioritario', 'veiculo_recomendado', 'preco_estimado']
    list_filter = ['data_servico', 'eh_prioritario', 'veiculo_recomendado']
    search_fields = ['nome_servico', 'numero_venda']
    ordering = ['-data_servico', 'horario_base']
    date_hierarchy = 'data_servico'


@admin.register(ServicoGrupo)
class ServicoGrupoAdmin(admin.ModelAdmin):
    list_display = ['servico', 'grupo', 'ordem']
    list_filter = ['grupo__data_servico']
    ordering = ['grupo__data_servico', 'grupo__horario_base', 'ordem']


@admin.register(ProcessamentoPlanilha)
class ProcessamentoPlanilhaAdmin(admin.ModelAdmin):
    list_display = ['nome_arquivo', 'status', 'linhas_processadas', 'linhas_erro', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['nome_arquivo']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CalculoPreco)
class CalculoPrecoAdmin(admin.ModelAdmin):
    list_display = [
        'chave_servico', 'tipo_tarifario', 'veiculo_recomendado', 
        'pax', 'preco_final', 'margem_percentual', 'data_calculo'
    ]
    list_filter = ['tipo_tarifario', 'veiculo_recomendado', 'data_calculo']
    search_fields = ['chave_servico', 'tipo_servico']
    readonly_fields = ['data_calculo', 'margem_percentual']
    
    fieldsets = (
        ('Identificação do Serviço', {
            'fields': ('chave_servico', 'tipo_servico', 'aeroporto', 'regiao', 'pax')
        }),
        ('Cálculo de Preços', {
            'fields': ('tipo_tarifario', 'veiculo_recomendado', 'preco_base', 
                      'preco_final', 'custo_operacional', 'margem', 'rentabilidade')
        }),
        ('Metadados', {
            'fields': ('data_calculo', 'detalhes_json'),
            'classes': ('collapse',)
        }),
    )
    
    def margem_percentual(self, obj):
        return f"{obj.margem_percentual:.2f}%"
    margem_percentual.short_description = "Margem %"
