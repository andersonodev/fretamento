from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Escala, AlocacaoVan


@admin.register(Escala)
class EscalaAdmin(admin.ModelAdmin):
    list_display = ['escala_info', 'etapa_badge', 'origem_data', 'vans_resumo', 'totais_financeiros', 'acoes_escala']
    list_filter = ['etapa', 'created_at']
    readonly_fields = ['total_van1_pax', 'total_van2_pax', 'total_van1_valor', 'total_van2_valor']
    ordering = ['-data']
    date_hierarchy = 'data'
    list_per_page = 20
    
    fieldsets = (
        ('📅 Informações da Escala', {
            'fields': ('data', 'etapa', 'data_origem'),
            'classes': ('wide',)
        }),
        ('🚐 Van 1 - Totais', {
            'fields': ('total_van1_pax', 'total_van1_valor'),
            'classes': ('wide',)
        }),
        ('🚗 Van 2 - Totais', {
            'fields': ('total_van2_pax', 'total_van2_valor'),
            'classes': ('wide',)
        }),
    )
    
    def escala_info(self, obj):
        return format_html(
            '<strong style="color: #47d7ac;">📅 {}</strong>',
            obj.data.strftime("%d/%m/%Y")
        )
    escala_info.short_description = "📅 Data da Escala"
    
    def etapa_badge(self, obj):
        etapa_colors = {
            'Estrutura Criada': '#4299e1',
            'Dados Puxados': '#ed8936',
            'Otimizada': '#48bb78'
        }
        color = etapa_colors.get(obj.etapa, '#8e9aaf')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 10px; border-radius: 8px; font-weight: 600; font-size: 11px;">{}</span>',
            color, obj.etapa
        )
    etapa_badge.short_description = "⚡ Etapa"
    
    def origem_data(self, obj):
        if obj.data_origem:
            return format_html(
                '<span style="color: #4299e1; font-weight: 500;">📊 {}</span>',
                obj.data_origem.strftime("%d/%m/%Y")
            )
        return format_html('<span style="color: #8e9aaf;">N/A</span>')
    origem_data.short_description = "📊 Data Origem"
    
    def vans_resumo(self, obj):
        return format_html(
            '<div style="display: flex; gap: 8px;"><span style="background: #4299e1; color: white; padding: 2px 8px; border-radius: 6px; font-size: 10px; font-weight: 600;">🚐 VAN1: {} PAX</span><span style="background: #ed8936; color: white; padding: 2px 8px; border-radius: 6px; font-size: 10px; font-weight: 600;">🚗 VAN2: {} PAX</span></div>',
            obj.total_van1_pax or 0,
            obj.total_van2_pax or 0
        )
    vans_resumo.short_description = "🚐 Passageiros"
    
    def totais_financeiros(self, obj):
        total_geral = (obj.total_van1_valor or 0) + (obj.total_van2_valor or 0)
        return format_html(
            '<div style="text-align: center;"><div style="color: #47d7ac; font-weight: 700; font-size: 14px;">R$ {}</div><small style="color: #8e9aaf;">V1: R$ {} | V2: R$ {}</small></div>',
            f'{total_geral:.2f}',
            f'{obj.total_van1_valor or 0:.2f}',
            f'{obj.total_van2_valor or 0:.2f}'
        )
    totais_financeiros.short_description = "💰 Valores"
    
    def acoes_escala(self, obj):
        change_url = reverse('admin:escalas_escala_change', args=[obj.pk])
        alocacoes_count = obj.alocacoes.count()
        
        return format_html(
            '<div style="text-align: center;"><a href="{}" style="background: #4299e1; color: white; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; display: block; margin-bottom: 2px;">✏️ EDITAR</a><small style="color: #8e9aaf;">{} alocações</small></div>',
            change_url, alocacoes_count
        )
    acoes_escala.short_description = "⚡ Ações"


@admin.register(AlocacaoVan)
class AlocacaoVanAdmin(admin.ModelAdmin):
    list_display = ['alocacao_info', 'servico_detalhes', 'van_ordem', 'tipo_alocacao', 'preco_badge', 'data_escala']
    list_filter = ['van', 'automatica', 'escala__data']
    ordering = ['escala__data', 'van', 'ordem']
    list_per_page = 30
    
    def alocacao_info(self, obj):
        return format_html(
            '<strong style="color: #47d7ac;">🎯 Alocação #{}</strong>',
            obj.pk
        )
    alocacao_info.short_description = "🎯 ID"
    
    def servico_detalhes(self, obj):
        if obj.servico:
            return format_html(
                '<div style="font-size: 11px;"><strong style="color: #4299e1;">{}</strong><br><span style="color: #8e9aaf;">{} | {} PAX</span></div>',
                obj.servico.servico[:40] + '...' if len(obj.servico.servico) > 40 else obj.servico.servico,
                obj.servico.cliente[:20] + '...' if len(obj.servico.cliente) > 20 else obj.servico.cliente,
                obj.servico.pax
            )
        return format_html('<span style="color: #f56565;">❌ Serviço não encontrado</span>')
    servico_detalhes.short_description = "📋 Serviço"
    
    def van_ordem(self, obj):
        van_colors = {
            'VAN1': '#4299e1',
            'VAN2': '#ed8936'
        }
        color = van_colors.get(obj.van, '#8e9aaf')
        
        return format_html(
            '<div style="text-align: center;"><span style="background: {}; color: white; padding: 4px 8px; border-radius: 8px; font-weight: 600; font-size: 11px; display: block; margin-bottom: 2px;">{}</span><small style="color: #8e9aaf;">Ordem: {}</small></div>',
            color, obj.van, obj.ordem or 'N/A'
        )
    van_ordem.short_description = "🚐 Van & Ordem"
    
    def tipo_alocacao(self, obj):
        if obj.automatica:
            return format_html('<span style="background: #48bb78; color: white; padding: 2px 6px; border-radius: 6px; font-size: 10px; font-weight: 600;">🤖 AUTO</span>')
        else:
            return format_html('<span style="background: #f56565; color: white; padding: 2px 6px; border-radius: 6px; font-size: 10px; font-weight: 600;">👤 MANUAL</span>')
    tipo_alocacao.short_description = "🎛️ Tipo"
    
    def preco_badge(self, obj):
        if obj.preco_calculado:
            return format_html(
                '<span style="background: #47d7ac; color: white; padding: 4px 8px; border-radius: 8px; font-weight: 600; font-size: 11px;">R$ {:.2f}</span>',
                obj.preco_calculado
            )
        return format_html('<span style="color: #8e9aaf;">Sem preço</span>')
    preco_badge.short_description = "💰 Preço"
    
    def data_escala(self, obj):
        return format_html(
            '<span style="color: #4299e1; font-weight: 500;">{}</span>',
            obj.escala.data.strftime("%d/%m/%Y")
        )
    data_escala.short_description = "📅 Data"
