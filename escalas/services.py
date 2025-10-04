"""
Serviços para gerenciamento de escalas
"""

from datetime import datetime, date
from typing import List, Dict
from django.db import transaction
from core.models import Servico, GrupoServico
from escalas.models import Escala, AlocacaoVan, ServicoGrupo
from core.logic import OtimizadorEscalas, CalculadorVeiculoPreco
import logging

logger = logging.getLogger(__name__)


class GerenciadorEscalas:
    """Classe principal para gerenciar escalas - DEPRECATED"""
    
    def __init__(self):
        # Mantido para compatibilidade, mas não usado mais
        pass
    
    def criar_escala_basica(self, data_alvo: date) -> 'Escala':
        """
        Cria apenas a estrutura básica da escala (sem dados)
        """
        from escalas.models import Escala
        
        # Busca ou cria a escala
        escala, created = Escala.objects.get_or_create(
            data=data_alvo,
            defaults={'etapa': 'ESTRUTURA'}
        )
        
        if created:
            logger.info(f"Estrutura de escala criada para {data_alvo}")
        else:
            logger.info(f"Escala para {data_alvo} já existe.")
        
        return escala


class ExportadorEscalas:
    """Classe para exportar escalas em diversos formatos"""
    
    def exportar_para_excel(self, escala: Escala) -> bytes:
        """Exporta escala para formato Excel conforme especificação Google Sheets"""
        import io
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
        from django.db.models import Q
        
        wb = Workbook()
        ws = wb.active
        nomeMes = escala.data.strftime('%B')
        ws.title = f"Escala para {nomeMes}"
        
        # Cabeçalhos conforme especificação
        headers = [
            "DATA", "CLIENTE", "Local Pick-UP", "NÚMERO DA VENDA", "PAX",
            "HORÁRIO", "DATA DO SERVIÇO", "INÍCIO", "TÉRMINO", "SERVIÇOS", 
            "VALOR CUSTO TARIFÁRIO", "VAN", "OBS", "Acumulado Van 01", "Rent Van 01"
        ]
        
        # Configuração de estilo
        header_font = Font(bold=True, size=10)
        header_fill = PatternFill(start_color="d9ead3", end_color="d9ead3", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Escreve cabeçalhos
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # Configurar larguras de coluna conforme especificação
        column_widths = [80, 110, 120, 110, 65, 65, 80, 65, 65, 300, 120, 70, 150, 120, 120]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width / 7  # Ajuste de escala
        
        # Congelar primeira linha
        ws.freeze_panes = "A2"
        
        # Função para processar grupos e serviços individuais
        def processar_van(alocacoes, van_name):
            """Processa alocações de uma van, agrupando quando necessário"""
            grupos_processados = set()
            resultados = []
            
            for alocacao in alocacoes:
                # Verificar se esta alocação está em um grupo
                try:
                    grupo_info = alocacao.grupo_info
                    grupo = grupo_info.grupo
                    
                    if grupo.id not in grupos_processados:
                        # Processar grupo completo
                        grupos_processados.add(grupo.id)
                        
                        # Buscar todos os serviços do grupo na mesma van
                        servicos_do_grupo = []
                        alocacoes_do_grupo = alocacao.escala.alocacoes.filter(
                            van=alocacao.van,
                            grupo_info__grupo=grupo
                        ).order_by('ordem')
                        
                        for aloc in alocacoes_do_grupo:
                            servicos_do_grupo.append(aloc)
                        
                        if len(servicos_do_grupo) > 1:
                            # Grupo com múltiplos serviços - concatenar números de venda
                            numeros_venda = []
                            total_pax = 0
                            primeiro_servico = servicos_do_grupo[0].servico
                            
                            for aloc_grupo in servicos_do_grupo:
                                if aloc_grupo.servico.numero_venda:
                                    numeros_venda.append(str(aloc_grupo.servico.numero_venda))
                                total_pax += aloc_grupo.servico.pax or 0
                            
                            # Criar linha agrupada
                            linha_grupo = {
                                'data': escala.data,
                                'cliente': primeiro_servico.cliente,
                                'local_pickup': primeiro_servico.local_pickup or "",
                                'numero_venda': " / ".join(numeros_venda),  # CONCATENADO
                                'pax': total_pax,
                                'horario': primeiro_servico.horario,
                                'data_servico': primeiro_servico.data_do_servico,
                                'servico': f"{primeiro_servico.servico} (+{len(servicos_do_grupo)-1} / Grupo)",
                                'preco': sum(float(aloc.preco_calculado or 0) for aloc in servicos_do_grupo),
                                'van': van_name,
                                'obs': f"Grupo {grupo.id}"
                            }
                            resultados.append(linha_grupo)
                        else:
                            # Grupo com apenas um serviço - tratar como individual
                            resultados.append({
                                'data': escala.data,
                                'cliente': alocacao.servico.cliente,
                                'local_pickup': alocacao.servico.local_pickup or "",
                                'numero_venda': alocacao.servico.numero_venda or "",
                                'pax': alocacao.servico.pax,
                                'horario': alocacao.servico.horario,
                                'data_servico': alocacao.servico.data_do_servico,
                                'servico': alocacao.servico.servico,
                                'preco': float(alocacao.preco_calculado or 0),
                                'van': van_name,
                                'obs': ""
                            })
                
                except ServicoGrupo.DoesNotExist:
                    # Serviço individual (não está em grupo)
                    resultados.append({
                        'data': escala.data,
                        'cliente': alocacao.servico.cliente,
                        'local_pickup': alocacao.servico.local_pickup or "",
                        'numero_venda': alocacao.servico.numero_venda or "",
                        'pax': alocacao.servico.pax,
                        'horario': alocacao.servico.horario,
                        'data_servico': alocacao.servico.data_do_servico,
                        'servico': alocacao.servico.servico,
                        'preco': float(alocacao.preco_calculado or 0),
                        'van': van_name,
                        'obs': ""
                    })
            
            return resultados
        
        # Obtém alocações da escala ordenadas por van e ordem
        alocacoes_van1 = escala.alocacoes.filter(van='VAN1').order_by('ordem')
        alocacoes_van2 = escala.alocacoes.filter(van='VAN2').order_by('ordem')
        
        # Processar cada van
        dados_van1 = processar_van(alocacoes_van1, "VAN 1")
        dados_van2 = processar_van(alocacoes_van2, "VAN 2")
        
        row = 2
        
        # ===== VAN 1 =====
        van1_start_row = row
        van1_rows = 0
        
        for dados in dados_van1:
            ws.cell(row=row, column=1, value=dados['data'])  # DATA
            ws.cell(row=row, column=2, value=dados['cliente'])  # CLIENTE
            ws.cell(row=row, column=3, value=dados['local_pickup'])  # Local Pick-UP
            ws.cell(row=row, column=4, value=dados['numero_venda'])  # NÚMERO DA VENDA (CONCATENADO)
            ws.cell(row=row, column=5, value=dados['pax'])  # PAX
            ws.cell(row=row, column=6, value=dados['horario'])  # HORÁRIO
            ws.cell(row=row, column=7, value=dados['data_servico'])  # DATA DO SERVIÇO
            ws.cell(row=row, column=8, value="")  # INÍCIO (vazio)
            ws.cell(row=row, column=9, value="")  # TÉRMINO (vazio)
            ws.cell(row=row, column=10, value=dados['servico'])  # SERVIÇOS
            ws.cell(row=row, column=11, value=dados['preco'])  # VALOR CUSTO TARIFÁRIO
            ws.cell(row=row, column=12, value=dados['van'])  # VAN
            ws.cell(row=row, column=13, value=dados['obs'])  # OBS
            
            row += 1
            van1_rows += 1
        
        # Preencher linhas vazias para Van 1 (mínimo 20 linhas)
        MIN_ROWS_VAN = 20
        while van1_rows < MIN_ROWS_VAN:
            ws.cell(row=row, column=1, value=escala.data)
            ws.cell(row=row, column=12, value="VAN 1")
            row += 1
            van1_rows += 1
        
        van1_end_row = row - 1
        
        # ===== LINHA DIVISÓRIA =====
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=row, column=col)
            cell.fill = PatternFill(start_color="34a853", end_color="34a853", fill_type="solid")
        row += 1
        
        # ===== VAN 2 =====
        van2_start_row = row
        van2_rows = 0
        
        for dados in dados_van2:
            ws.cell(row=row, column=1, value=dados['data'])  # DATA
            ws.cell(row=row, column=2, value=dados['cliente'])  # CLIENTE
            ws.cell(row=row, column=3, value=dados['local_pickup'])  # Local Pick-UP
            ws.cell(row=row, column=4, value=dados['numero_venda'])  # NÚMERO DA VENDA (CONCATENADO)
            ws.cell(row=row, column=5, value=dados['pax'])  # PAX
            ws.cell(row=row, column=6, value=dados['horario'])  # HORÁRIO
            ws.cell(row=row, column=7, value=dados['data_servico'])  # DATA DO SERVIÇO
            ws.cell(row=row, column=8, value="")  # INÍCIO (vazio)
            ws.cell(row=row, column=9, value="")  # TÉRMINO (vazio)
            ws.cell(row=row, column=10, value=dados['servico'])  # SERVIÇOS
            ws.cell(row=row, column=11, value=dados['preco'])  # VALOR CUSTO TARIFÁRIO
            ws.cell(row=row, column=12, value=dados['van'])  # VAN
            ws.cell(row=row, column=13, value=dados['obs'])  # OBS
            
            row += 1
            van2_rows += 1
        
        # Preencher linhas vazias para Van 2 (mínimo 20 linhas)
        while van2_rows < MIN_ROWS_VAN:
            ws.cell(row=row, column=1, value=escala.data)
            ws.cell(row=row, column=12, value="VAN 2")
            row += 1
            van2_rows += 1
        
        van2_end_row = row - 1
        
        # ===== FÓRMULAS DE ACUMULADO E RENT =====
        CUSTO_DIARIO = 635.17
        
        # Van 1 - Acumulado e Rent
        if van1_rows > 0:
            # Mesclar células para Acumulado Van 1
            if van1_end_row > van1_start_row:
                ws.merge_cells(f"N{van1_start_row}:N{van1_end_row}")
                ws.merge_cells(f"O{van1_start_row}:O{van1_end_row}")
            
            # Fórmulas
            acumulado_cell = ws.cell(row=van1_start_row, column=14)  # Coluna N
            rent_cell = ws.cell(row=van1_start_row, column=15)  # Coluna O
            
            acumulado_cell.value = f"=SUM(K{van1_start_row}:K{van1_end_row})"
            rent_cell.value = f"=SUM(K{van1_start_row}:K{van1_end_row})-{CUSTO_DIARIO}"
            
            # Estilo para células de resumo
            gray_fill = PatternFill(start_color="efefef", end_color="efefef", fill_type="solid")
            center_alignment = Alignment(horizontal="center", vertical="center")
            bold_font = Font(bold=True)
            
            acumulado_cell.fill = gray_fill
            acumulado_cell.alignment = center_alignment
            acumulado_cell.font = bold_font
            
            rent_cell.fill = gray_fill
            rent_cell.alignment = center_alignment
            rent_cell.font = bold_font
        
        # Van 2 - Acumulado e Rent
        if van2_rows > 0:
            # Mesclar células para Acumulado Van 2
            if van2_end_row > van2_start_row:
                ws.merge_cells(f"N{van2_start_row}:N{van2_end_row}")
                ws.merge_cells(f"O{van2_start_row}:O{van2_end_row}")
            
            # Fórmulas
            acumulado_cell = ws.cell(row=van2_start_row, column=14)  # Coluna N
            rent_cell = ws.cell(row=van2_start_row, column=15)  # Coluna O
            
            acumulado_cell.value = f"=SUM(K{van2_start_row}:K{van2_end_row})"
            rent_cell.value = f"=SUM(K{van2_start_row}:K{van2_end_row})-{CUSTO_DIARIO}"
            
            # Estilo para células de resumo
            gray_fill = PatternFill(start_color="efefef", end_color="efefef", fill_type="solid")
            center_alignment = Alignment(horizontal="center", vertical="center")
            bold_font = Font(bold=True)
            
            acumulado_cell.fill = gray_fill
            acumulado_cell.alignment = center_alignment
            acumulado_cell.font = bold_font
            
            rent_cell.fill = gray_fill
            rent_cell.alignment = center_alignment
            rent_cell.font = bold_font
        
        # ===== FORMATAÇÃO =====
        # Formato de moeda para colunas de valor
        for row_num in range(2, row):
            ws.cell(row=row_num, column=11).number_format = 'R$ #,##0.00'  # VALOR CUSTO
        
        # Formato de moeda para acumulados
        ws.cell(row=van1_start_row, column=14).number_format = 'R$ #,##0.00'
        ws.cell(row=van1_start_row, column=15).number_format = 'R$ #,##0.00'
        if van2_rows > 0:
            ws.cell(row=van2_start_row, column=14).number_format = 'R$ #,##0.00'
            ws.cell(row=van2_start_row, column=15).number_format = 'R$ #,##0.00'
        
        # Formato de horário
        for row_num in range(2, row):
            ws.cell(row=row_num, column=6).number_format = 'hh:mm'  # HORÁRIO
            ws.cell(row=row_num, column=8).number_format = 'hh:mm'  # INÍCIO
            ws.cell(row=row_num, column=9).number_format = 'hh:mm'  # TÉRMINO
        
        # Formato de data
        for row_num in range(2, row):
            ws.cell(row=row_num, column=1).number_format = 'dd/mm/yy'  # DATA
            ws.cell(row=row_num, column=7).number_format = 'dd/mm/yyyy'  # DATA DO SERVIÇO
        
        # Salva em buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return buffer.getvalue()