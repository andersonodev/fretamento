from django.contrib import admin
from .models import Escala, AlocacaoVan


@admin.register(Escala)
class EscalaAdmin(admin.ModelAdmin):
    list_display = ['data', 'etapa', 'data_origem', 'total_van1_pax', 'total_van2_pax', 'created_at']
    list_filter = ['etapa', 'created_at']
    readonly_fields = ['total_van1_pax', 'total_van2_pax', 'total_van1_valor', 'total_van2_valor']
    ordering = ['-data']
    date_hierarchy = 'data'


@admin.register(AlocacaoVan)
class AlocacaoVanAdmin(admin.ModelAdmin):
    list_display = ['escala', 'servico', 'van', 'ordem', 'automatica', 'preco_calculado']
    list_filter = ['van', 'automatica', 'escala__data']
    ordering = ['escala__data', 'van', 'ordem']
