"""
Módulo de lógica de negócio para agrupamento e otimização de serviços
Baseado no código original do Google Apps Script
"""

from decimal import Decimal
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from .tarifarios import (
    calcular_preco_servico,
    calcular_veiculo_recomendado,
    buscar_preco_jw,
    buscar_preco_motoristas,
    CUSTO_DIARIO_VAN
)
from django.utils import timezone
from core.models import Servico, GrupoServico, ServicoGrupo
import logging

logger = logging.getLogger(__name__)

# Constantes
JANELA_AGRUPAMENTO_NOME = timedelta(minutes=35)
JANELA_INTERVALO_VAN = timedelta(hours=2)


class AgrupadorServicos:
    """Classe responsável pelo agrupamento de serviços"""
    
    def __init__(self):
        self.grupos_criados = []
    
    def agrupar_servicos_por_nome(self, servicos: List[Servico]) -> List[GrupoServico]:
        """
        Agrupa serviços com o mesmo nome que ocorram em até 35 minutos de diferença
        """
        logger.info(f"[AGRUPAMENTO-INÍCIO] Recebidos {len(servicos)} serviços para agrupar.")
        
        # Agrupa por nome do serviço
        mapa_servicos = {}
        for servico in servicos:
            nome_key = self._normalizar_texto(servico.servico).upper()
            if nome_key not in mapa_servicos:
                mapa_servicos[nome_key] = []
            mapa_servicos[nome_key].append(servico)
        
        grupos_finais = []
        logger.info(f"[AGRUPAMENTO-MAPA] Serviços foram separados em {len(mapa_servicos)} nomes únicos.")
        
        for nome, lista_servicos in mapa_servicos.items():
            if 'SANTOS DUMONT' in nome:  # Log detalhado para exemplo
                logger.info(f"--- Processando o serviço: {nome} (contém {len(lista_servicos)} ocorrências) ---")
            
            # Ordena por horário
            lista_servicos.sort(key=lambda s: s.horario if s.horario else datetime.min.time())
            
            grupo_atual = None
            for servico in lista_servicos:
                if not servico.horario:  # Pula serviços sem horário
                    continue
                
                if not grupo_atual:
                    # Inicia novo grupo
                    grupo_atual = self._criar_novo_grupo(servico)
                    if 'SANTOS DUMONT' in nome:
                        logger.info(f" - Iniciando novo grupo às {servico.horario} com PAX {servico.pax}")
                    continue
                
                # Verifica se pode adicionar ao grupo atual
                diff = self._calcular_diferenca_tempo(servico.horario, grupo_atual.horario_base)
                if 'SANTOS DUMONT' in nome:
                    logger.info(f" - Verificando serviço das {servico.horario}. Diferença: {diff.total_seconds()/60} minutos.")
                
                if diff <= JANELA_AGRUPAMENTO_NOME:
                    # Adiciona ao grupo atual
                    self._adicionar_servico_ao_grupo(grupo_atual, servico)
                    if 'SANTOS DUMONT' in nome:
                        logger.info(f" -> ADICIONADO. Novo PAX total: {grupo_atual.pax_total}")
                else:
                    # Finaliza grupo atual e inicia novo
                    grupos_finais.append(grupo_atual)
                    if 'SANTOS DUMONT' in nome:
                        logger.info(f" -> FORA DA JANELA. Grupo anterior finalizado.")
                    
                    grupo_atual = self._criar_novo_grupo(servico)
                    if 'SANTOS DUMONT' in nome:
                        logger.info(f" - Iniciando novo grupo às {servico.horario} com PAX {servico.pax}")
            
            if grupo_atual:
                grupos_finais.append(grupo_atual)
        
        logger.info(f"[AGRUPAMENTO-FIM] Total de {len(grupos_finais)} grupos formados.")
        return grupos_finais
    
    def _normalizar_texto(self, texto: str) -> str:
        """Normaliza texto removendo espaços e convertendo para string"""
        return (texto or "").strip()
    
    def _criar_novo_grupo(self, servico: Servico) -> GrupoServico:
        """Cria um novo grupo de serviços"""
        grupo = GrupoServico(
            nome_servico=servico.servico,
            horario_base=servico.horario,
            data_servico=servico.data_do_servico,
            pax_total=servico.pax,
            numero_venda=servico.numero_venda,
            eh_prioritario=servico.eh_prioritario
        )
        return grupo
    
    def _adicionar_servico_ao_grupo(self, grupo: GrupoServico, servico: Servico):
        """Adiciona um serviço a um grupo existente"""
        grupo.pax_total += servico.pax
        grupo.numero_venda = self._merge_numero_venda(grupo.numero_venda, servico.numero_venda)
        if servico.eh_prioritario:
            grupo.eh_prioritario = True
    
    def _merge_numero_venda(self, venda_a: str, venda_b: str) -> str:
        """Concatena números de venda"""
        va = self._normalizar_texto(venda_a)
        vb = self._normalizar_texto(venda_b)
        
        if not va and not vb:
            return ""
        if not va:
            return vb
        if not vb:
            return va
        
        # Remove duplicatas
        vendas = list(set((va + '/' + vb).split('/')))
        vendas = [v.strip() for v in vendas if v.strip()]
        return ' / '.join(vendas)
    
    def _calcular_diferenca_tempo(self, horario1, horario2) -> timedelta:
        """Calcula diferença entre dois horários"""
        if not horario1 or not horario2:
            return timedelta(hours=24)  # Diferença grande se algum horário for None
        
        # Converte time para datetime para fazer a diferença
        hoje = datetime.now().date()
        dt1 = datetime.combine(hoje, horario1)
        dt2 = datetime.combine(hoje, horario2)
        
        return abs(dt1 - dt2)


class OtimizadorEscalas:
    """Classe responsável pela otimização de escalas"""
    
    def criar_grupos_otimizados(self, servicos: List[Servico]) -> List[GrupoServico]:
        """
        Função principal que orquestra a otimização
        Versão simplificada que apenas agrupa os serviços
        """
        logger.info('===== INÍCIO DA OTIMIZAÇÃO (SIMPLIFICADA) =====')
        
        # Filtra serviços com horário válido
        servicos_com_horario = [s for s in servicos if s.horario is not None]
        logger.info(f"[FILTRO INICIAL] {len(servicos_com_horario)} de {len(servicos)} serviços têm horário válido.")
        
        # Etapa de Agrupamento
        agrupador = AgrupadorServicos()
        todos_os_grupos = agrupador.agrupar_servicos_por_nome(servicos_com_horario)
        logger.info(f"[AGRUPAMENTO] Total de {len(todos_os_grupos)} grupos formados.")
        
        return todos_os_grupos
    
    def alocar_grupos_nas_vans(self, grupos: List[GrupoServico]) -> Dict[str, List[GrupoServico]]:
        """
        Distribui os grupos alternadamente entre as vans para melhor visualização
        """
        # Ordena todos os grupos por horário
        grupos.sort(key=lambda g: g.horario_base if g.horario_base else datetime.min.time())
        
        alocacao_van1 = []
        alocacao_van2 = []
        
        # Distribui os grupos alternadamente
        for index, grupo in enumerate(grupos):
            if index % 2 == 0:  # Índice par -> Van 1
                alocacao_van1.append(grupo)
            else:  # Índice ímpar -> Van 2
                alocacao_van2.append(grupo)
        
        return {
            'alocacao_van1': alocacao_van1,
            'alocacao_van2': alocacao_van2
        }


class CalculadorVeiculoPreco:
    """Classe para calcular veículo e preço dos grupos"""
    
    # Tarifário básico (pode ser expandido)
    TARIFARIO_BASICO = {
        'Executivo': 200,
        'Van 15 lugares': 300,
        'Van 18 lugares': 350,
        'Micro': 500,
        'Ônibus': 800
    }
    
    def alocar_veiculo_e_preco(self, grupo) -> Tuple[str, float]:
        """
        Aloca veículo e calcula preço para um grupo usando busca inteligente
        
        Args:
            grupo: Objeto grupo com serviços
            
        Returns:
            Tuple (veiculo, preco)
        """
        from core.busca_inteligente_precos import buscador_inteligente
        
        # Pega o primeiro serviço do grupo como referência
        servicos_do_grupo = grupo.servicogrupo_set.all()
        if not servicos_do_grupo:
            return ("Executivo", 200.0)
        
        servico_principal = servicos_do_grupo.first().servico
        total_pax = grupo.pax_total
        
        # Usa busca inteligente de preços
        veiculo, preco, fonte = buscador_inteligente.buscar_preco_inteligente(
            servico_principal.servico,
            total_pax,
            servico_principal.numero_venda
        )
        
        return (veiculo, float(preco))
    
    def alocar_veiculo_e_preco_servico(self, servico) -> Tuple[str, float]:
        """
        Aloca veículo e calcula preço para um serviço individual usando busca inteligente
        
        Args:
            servico: Objeto serviço individual
            
        Returns:
            Tuple (veiculo, preco)
        """
        from core.tarifarios import calcular_preco_servico
        
        # Usa a função melhorada de cálculo de preço
        return calcular_preco_servico(servico)
    
    def _alocarVeiculoEPreco(self, grupo: Dict[str, Any], servicos: List) -> Dict[str, Any]:
        """
        Aloca veículo e calcula preço para um grupo de serviços
        Integrado com os tarifários TARIFARIO_MOTORISTAS e TARIFARIO_JW
        """
        total_pax = grupo['total_pax']
        motorista_priority = grupo.get('motorista_priority', 0)
        
        # Escolhe o primeiro serviço como representativo para cálculo de preço
        servico_principal = servicos[0] if servicos else None
        
        if servico_principal:
            # Usa o novo sistema de tarifários
            veiculo_recomendado, preco_base = calcular_preco_servico(servico_principal)
            
            # Ajusta baseado no número total de PAX do grupo
            if total_pax > 3:
                # Para grupos maiores, recalcula o veículo
                veiculo_recomendado = calcular_veiculo_recomendado(total_pax)
                
                # Recalcula preço se necessário
                if total_pax > 4:
                    # Para múltiplos veículos (motoristas)
                    carros_necessarios = (total_pax + 3) // 4
                    preco_base = preco_base * carros_necessarios
        else:
            # Fallback para grupos sem serviços válidos
            veiculo_recomendado = calcular_veiculo_recomendado(total_pax)
            preco_base = 200.00  # Preço padrão
        
        # Aplicar multiplicador de prioridade
        if motorista_priority > 0:
            preco_final = preco_base * (1 + (motorista_priority * 0.1))
        else:
            preco_final = preco_base
        
        # Cálculo do custo operacional baseado no CUSTO_DIARIO_VAN
        custo_operacional = CUSTO_DIARIO_VAN * 0.15  # 15% do custo diário como base
        
        return {
            'veiculo': veiculo_recomendado,
            'preco_venda': round(preco_final, 2),
            'preco_custo': round(custo_operacional, 2),
            'margem': round(preco_final - custo_operacional, 2),
            'rentabilidade': round(((preco_final - custo_operacional) / preco_final) * 100, 2) if preco_final > 0 else 0,
            'detalhes_calculo': {
                'preco_base_tarifario': preco_base,
                'multiplicador_prioridade': (1 + (motorista_priority * 0.1)) if motorista_priority > 0 else 1,
                'veiculo_recomendado_pax': total_pax,
                'fonte_preco': 'tarifarios_integrados'
            }
        }