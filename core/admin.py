from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Servico, GrupoServico, ServicoGrupo, ProcessamentoPlanilha, CalculoPreco


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ['servico_formatado', 'cliente_info', 'data_servico_formatada', 'horario_formatado', 'pax_badge', 'status_badges', 'tipo_regiao']
    list_filter = ['data_do_servico', 'tipo', 'regiao', 'eh_prioritario', 'eh_regular']
    search_fields = ['servico', 'cliente', 'numero_venda']
    readonly_fields = ['tipo', 'direcao', 'aeroporto', 'regiao', 'eh_regular', 'eh_prioritario']
    ordering = ['-data_do_servico', 'horario']
    date_hierarchy = 'data_do_servico'
    list_per_page = 25
    
    fieldsets = (
        ('📋 Informações do Serviço', {
            'fields': ('servico', 'cliente', 'numero_venda'),
            'classes': ('wide',)
        }),
        ('📅 Data e Horário', {
            'fields': ('data_do_servico', 'horario'),
            'classes': ('wide',)
        }),
        ('👥 Passageiros e Detalhes', {
            'fields': ('pax', 'obs', 'observacao'),
            'classes': ('wide',)
        }),
        ('🎯 Classificação (Automática)', {
            'fields': ('tipo', 'direcao', 'aeroporto', 'regiao', 'eh_regular', 'eh_prioritario'),
            'classes': ('collapse',)
        }),
    )
    
    def servico_formatado(self, obj):
        return format_html(
            '<strong style="color: #47d7ac;">{}</strong>',
            obj.servico[:50] + '...' if len(obj.servico) > 50 else obj.servico
        )
    servico_formatado.short_description = "🎯 Serviço"
    
    def cliente_info(self, obj):
        return format_html(
            '<span style="background: #2d3748; color: #e2e8f0; padding: 4px 8px; border-radius: 6px; font-size: 12px;">{}</span>',
            obj.cliente[:30] + '...' if len(obj.cliente) > 30 else obj.cliente
        )
    cliente_info.short_description = "👤 Cliente"
    
    def data_servico_formatada(self, obj):
        return format_html(
            '<span style="color: #4299e1; font-weight: 600;">{}</span>',
            obj.data_do_servico.strftime("%d/%m/%Y")
        )
    data_servico_formatada.short_description = "📅 Data"
    
    def horario_formatado(self, obj):
        return format_html(
            '<span style="background: #4a5568; color: white; padding: 2px 6px; border-radius: 4px; font-family: monospace;">{}</span>',
            obj.horario.strftime("%H:%M") if obj.horario else "N/A"
        )
    horario_formatado.short_description = "⏰ Horário"
    
    def pax_badge(self, obj):
        color = "#48bb78" if obj.pax <= 4 else "#ed8936" if obj.pax <= 8 else "#f56565"
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 12px; font-weight: 600; font-size: 11px;">{}</span>',
            color, obj.pax
        )
    pax_badge.short_description = "👥 PAX"
    
    def status_badges(self, obj):
        badges = []
        if obj.eh_prioritario:
            badges.append('<span style="background: #f56565; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">🔥 PRIORITÁRIO</span>')
        if obj.eh_regular:
            badges.append('<span style="background: #4299e1; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">🔄 REGULAR</span>')
        
        return format_html(' '.join(badges)) if badges else format_html('<span style="color: #8e9aaf;">-</span>')
    status_badges.short_description = "🏷️ Status"
    
    def tipo_regiao(self, obj):
        return format_html(
            '<div style="font-size: 11px;"><strong style="color: #47d7ac;">{}</strong><br><span style="color: #8e9aaf;">{}</span></div>',
            obj.tipo or "N/A", obj.regiao or "N/A"
        )
    tipo_regiao.short_description = "📍 Tipo/Região"


@admin.register(GrupoServico)
class GrupoServicoAdmin(admin.ModelAdmin):
    list_display = ['nome_servico_formatado', 'data_servico_badge', 'horario_veiculo', 'pax_preco', 'status_grupo', 'acoes_rapidas']
    list_filter = ['data_servico', 'eh_prioritario', 'veiculo_recomendado']
    search_fields = ['nome_servico', 'numero_venda']
    ordering = ['-data_servico', 'horario_base']
    date_hierarchy = 'data_servico'
    list_per_page = 20
    
    def nome_servico_formatado(self, obj):
        return format_html(
            '<strong style="color: #47d7ac;">{}</strong><br><small style="color: #8e9aaf;">Venda: {}</small>',
            obj.nome_servico[:40] + '...' if len(obj.nome_servico) > 40 else obj.nome_servico,
            obj.numero_venda or "N/A"
        )
    nome_servico_formatado.short_description = "🎯 Grupo de Serviço"
    
    def data_servico_badge(self, obj):
        return format_html(
            '<span style="background: linear-gradient(135deg, #2c5282, #47d7ac); color: white; padding: 6px 10px; border-radius: 8px; font-weight: 600; font-size: 12px;">{}</span>',
            obj.data_servico.strftime("%d/%m/%Y")
        )
    data_servico_badge.short_description = "📅 Data"
    
    def horario_veiculo(self, obj):
        veiculo_color = {
            'VAN': '#4299e1',
            'MICRO': '#ed8936', 
            'BUS': '#f56565'
        }.get(obj.veiculo_recomendado, '#8e9aaf')
        
        return format_html(
            '<div style="text-align: center;"><span style="background: #4a5568; color: white; padding: 2px 6px; border-radius: 4px; font-family: monospace; display: block; margin-bottom: 4px;">{}</span><span style="background: {}; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; font-weight: 600;">{}</span></div>',
            obj.horario_base.strftime("%H:%M") if obj.horario_base else "N/A",
            veiculo_color,
            obj.veiculo_recomendado or "N/A"
        )
    horario_veiculo.short_description = "⏰ Horário & 🚐 Veículo"
    
    def pax_preco(self, obj):
        return format_html(
            '<div style="text-align: center;"><span style="background: #48bb78; color: white; padding: 2px 8px; border-radius: 12px; font-weight: 600; font-size: 11px; display: block; margin-bottom: 4px;">{} PAX</span><span style="color: #47d7ac; font-weight: 600;">R$ {:.2f}</span></div>',
            obj.pax_total,
            obj.preco_estimado or 0
        )
    pax_preco.short_description = "👥 PAX & 💰 Preço"
    
    def status_grupo(self, obj):
        if obj.eh_prioritario:
            return format_html('<span style="background: #f56565; color: white; padding: 4px 8px; border-radius: 8px; font-weight: 600; font-size: 10px;">🔥 PRIORITÁRIO</span>')
        return format_html('<span style="background: #48bb78; color: white; padding: 4px 8px; border-radius: 8px; font-weight: 600; font-size: 10px;">✅ NORMAL</span>')
    status_grupo.short_description = "🏷️ Status"
    
    def acoes_rapidas(self, obj):
        change_url = reverse('admin:core_gruposervico_change', args=[obj.pk])
        return format_html(
            '<a href="{}" style="background: #4299e1; color: white; padding: 4px 8px; border-radius: 6px; text-decoration: none; font-size: 10px;">✏️ EDITAR</a>',
            change_url
        )
    acoes_rapidas.short_description = "⚡ Ações"


@admin.register(ServicoGrupo)
class ServicoGrupoAdmin(admin.ModelAdmin):
    list_display = ['servico', 'grupo', 'ordem']
    list_filter = ['grupo__data_servico']
    ordering = ['grupo__data_servico', 'grupo__horario_base', 'ordem']


@admin.register(ProcessamentoPlanilha)
class ProcessamentoPlanilhaAdmin(admin.ModelAdmin):
    list_display = ['arquivo_info', 'status_badge', 'estatisticas_processamento', 'data_formatada']
    list_filter = ['status', 'created_at']
    search_fields = ['nome_arquivo']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 15
    
    def arquivo_info(self, obj):
        return format_html(
            '<strong style="color: #47d7ac;">📄 {}</strong>',
            obj.nome_arquivo[:50] + '...' if len(obj.nome_arquivo) > 50 else obj.nome_arquivo
        )
    arquivo_info.short_description = "📁 Arquivo"
    
    def status_badge(self, obj):
        status_colors = {
            'SUCESSO': '#48bb78',
            'ERRO': '#f56565', 
            'PROCESSANDO': '#ed8936',
            'PENDENTE': '#4299e1'
        }
        color = status_colors.get(obj.status, '#8e9aaf')
        
        status_icons = {
            'SUCESSO': '✅',
            'ERRO': '❌',
            'PROCESSANDO': '⏳',
            'PENDENTE': '⏸️'
        }
        icon = status_icons.get(obj.status, '❓')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 8px; font-weight: 600; font-size: 10px;">{} {}</span>',
            color, icon, obj.status
        )
    status_badge.short_description = "📊 Status"
    
    def estatisticas_processamento(self, obj):
        total = (obj.linhas_processadas or 0) + (obj.linhas_erro or 0)
        sucesso_pct = (obj.linhas_processadas / total * 100) if total > 0 else 0
        
        return format_html(
            '<div style="font-size: 11px;"><span style="background: #48bb78; color: white; padding: 2px 6px; border-radius: 4px; margin-right: 4px;">✅ {}</span><span style="background: #f56565; color: white; padding: 2px 6px; border-radius: 4px;">❌ {}</span><br><small style="color: #8e9aaf;">Taxa: {:.1f}%</small></div>',
            obj.linhas_processadas or 0,
            obj.linhas_erro or 0,
            sucesso_pct
        )
    estatisticas_processamento.short_description = "📈 Estatísticas"
    
    def data_formatada(self, obj):
        return format_html(
            '<span style="color: #4299e1; font-weight: 500;">{}</span>',
            obj.created_at.strftime("%d/%m/%Y %H:%M")
        )
    data_formatada.short_description = "📅 Processado em"


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
