"""
Módulo para processamento da planilha OS
Baseado na função limparOS() do Google Apps Script
"""

import pandas as pd
import re
from datetime import datetime, time
from typing import List, Dict, Tuple, Optional
from django.core.files.uploadedfile import UploadedFile
from core.models import Servico, ProcessamentoPlanilha
import logging

logger = logging.getLogger(__name__)


class ProcessadorPlanilhaOS:
    """Classe para processar e limpar a planilha OS"""
    
    def __init__(self):
        self.colunas_excluir = [
            "File Operadora", "Fone Contato", "Situação", "Agente", 
            "Obs", "Titular", "HORA", "Hora", "Cidade", 
            "Local Drop-Off", "Tipo"
        ]
        
        self.renames_colunas = {
            "Venda": "NÚMERO DA VENDA",
            "Data Reserva": "DATA",
            "Hora Voo": "HORÁRIO",
            "Serviço": "SERVIÇOS"
        }
    
    def processar_planilha(self, arquivo: UploadedFile) -> Tuple[List[Servico], ProcessamentoPlanilha]:
        """
        Processa a planilha OS completa
        """
        # Cria registro de processamento
        processamento = ProcessamentoPlanilha.objects.create(
            arquivo=arquivo,
            nome_arquivo=arquivo.name,
            status='PROCESSANDO'
        )
        
        try:
            # Lê a planilha
            df = self._ler_planilha(arquivo)
            
            # Aplica todas as limpezas
            df = self._limpar_planilha(df)
            
            # Converte para objetos Servico
            servicos = self._converter_para_servicos(df)
            
            # Atualiza status
            processamento.status = 'CONCLUIDO'
            processamento.linhas_processadas = len(servicos)
            processamento.log_processamento = f"Processamento concluído com sucesso. {len(servicos)} serviços criados."
            processamento.save()
            
            return servicos, processamento
            
        except Exception as e:
            processamento.status = 'ERRO'
            processamento.log_processamento = f"Erro durante processamento: {str(e)}"
            processamento.save()
            logger.error(f"Erro no processamento: {e}")
            raise
    
    def _ler_planilha(self, arquivo: UploadedFile) -> pd.DataFrame:
        """Lê a planilha Excel ou CSV"""
        try:
            if arquivo.name.endswith('.xlsx') or arquivo.name.endswith('.xls'):
                df = pd.read_excel(arquivo, engine='openpyxl')
            elif arquivo.name.endswith('.csv'):
                df = pd.read_csv(arquivo)
            else:
                raise ValueError("Formato de arquivo não suportado. Use .xlsx, .xls ou .csv")
            
            logger.info(f"Planilha lida com {len(df)} linhas e {len(df.columns)} colunas")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao ler planilha: {e}")
            raise
    
    def _limpar_planilha(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica todas as limpezas na planilha"""
        
        # 1. Remover colunas a partir de "ADT"
        df = self._remover_colunas_apos_adt(df)
        
        # 2. Remover colunas indesejadas
        df = self._remover_colunas_indesejadas(df)
        
        # 3. Limpar linhas indesejadas
        df = self._limpar_linhas_indesejadas(df)
        
        # 4. Separar Cliente/Titular
        df = self._separar_cliente_titular(df)
        
        # 5. Separar Voo em Nº Voo e Hora Voo
        df = self._separar_voo(df)
        
        # 6. Padronizar serviços
        df = self._padronizar_servicos(df)
        
        # 7. Normalizar nomes dos cabeçalhos
        df = self._normalizar_cabecalhos(df)
        
        return df
    
    def _remover_colunas_apos_adt(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove colunas a partir de 'ADT'"""
        colunas_manter = []
        for col in df.columns:
            if 'ADT' in str(col).upper():
                break
            colunas_manter.append(col)
        
        return df[colunas_manter] if colunas_manter else df
    
    def _remover_colunas_indesejadas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove colunas da lista de exclusão"""
        colunas_para_manter = [col for col in df.columns if col not in self.colunas_excluir]
        return df[colunas_para_manter]
    
    def _limpar_linhas_indesejadas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove linhas com folga, búzios, etc."""
        mascara_manter = True
        
        for col in df.columns:
            if df[col].dtype == 'object':  # Apenas colunas de texto
                # Remove linhas que contêm "folga" (case insensitive)
                mascara_folga = ~df[col].astype(str).str.lower().str.contains('folga', na=False)
                mascara_manter = mascara_manter & mascara_folga
        
        # Remove linhas completamente vazias
        mascara_nao_vazia = ~(df.astype(str) == '').all(axis=1)
        mascara_manter = mascara_manter & mascara_nao_vazia
        
        # Remove linhas que são apenas "-"
        mascara_hifen = ~(df.astype(str) == '-').all(axis=1)
        mascara_manter = mascara_manter & mascara_hifen
        
        df_limpo = df[mascara_manter].copy()
        linhas_removidas = len(df) - len(df_limpo)
        logger.info(f"Linhas removidas durante a limpeza: {linhas_removidas}")
        
        return df_limpo
    
    def _separar_cliente_titular(self, df: pd.DataFrame) -> pd.DataFrame:
        """Separa Cliente/Titular, mantém apenas Cliente"""
        cliente_cols = [col for col in df.columns if 'cliente' in str(col).lower()]
        
        for col in cliente_cols:
            df[col] = df[col].astype(str).apply(
                lambda x: x.split('/')[0].strip() if '/' in x else x
            )
            # Renomeia para "CLIENTE"
            if col != "CLIENTE":
                df = df.rename(columns={col: "CLIENTE"})
        
        return df
    
    def _separar_voo(self, df: pd.DataFrame) -> pd.DataFrame:
        """Separa coluna Voo em Nº Voo e Hora Voo"""
        voo_cols = [col for col in df.columns if str(col).lower() == 'voo']
        
        for col in voo_cols:
            # Verifica se já existem as colunas separadas
            if 'Nº Voo' not in df.columns and 'Hora Voo' not in df.columns:
                # Separa os dados
                voo_data = df[col].astype(str).str.split('-', n=1, expand=True)
                df['Nº Voo'] = voo_data[0].str.strip() if len(voo_data.columns) > 0 else ''
                df['Hora Voo'] = voo_data[1].str.strip() if len(voo_data.columns) > 1 else ''
                
                # Remove a coluna original
                df = df.drop(columns=[col])
        
        return df
    
    def _padronizar_servicos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Padroniza nomes de serviços"""
        servico_cols = [col for col in df.columns if 'serviço' in str(col).lower()]
        
        for col in servico_cols:
            df[col] = df[col].astype(str).apply(self._limpar_servico)
        
        return df
    
    def _limpar_servico(self, servico_original: str) -> str:
        """Limpa e padroniza um serviço individual"""
        if pd.isna(servico_original) or servico_original == 'nan':
            return ""
        
        servico = str(servico_original).strip()
        
        # 1. Limpeza e substituições gerais
        servico = re.sub(r'^\d+\s*[-–]?\s*', '', servico)  # Remove prefixo numérico
        servico = re.sub(r'S\s*\/\s*GUIA', '', servico, flags=re.IGNORECASE)  # Remove "S / GUIA"
        servico = re.sub(r'C\s*\/\s*GUIA', '', servico, flags=re.IGNORECASE)  # Remove "C / GUIA"
        servico = re.sub(r'P\/\s*', 'PARA ', servico, flags=re.IGNORECASE)  # Substitui "P/" por "PARA "
        servico = re.sub(r'\bZ\.SUL\b', 'ZONA SUL', servico, flags=re.IGNORECASE)  # Substitui "Z.SUL"
        
        # 2. Limpeza final
        servico = re.sub(r'\s*-\s*$', '', servico).strip()  # Remove hífen final
        servico = re.sub(r'\s{2,}', ' ', servico).strip()  # Remove espaços duplos
        
        # 3. Padronização específica para "Disposição"
        disposicao_match = re.search(r'disposição (\d+)\s*horas', servico, re.IGNORECASE)
        if disposicao_match:
            horas = disposicao_match.group(1)
            return f"Disposição {horas}h"
        
        return servico
    
    def _normalizar_cabecalhos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza nomes dos cabeçalhos"""
        return df.rename(columns=self.renames_colunas)
    
    def _converter_para_servicos(self, df: pd.DataFrame) -> List[Servico]:
        """Converte DataFrame para lista de objetos Servico"""
        servicos = []
        
        # Mapear colunas
        col_mapping = {
            'numero_venda': self._encontrar_coluna(df, ['NÚMERO DA VENDA', 'Venda']),
            'cliente': self._encontrar_coluna(df, ['CLIENTE', 'Cliente']),
            'local_pickup': self._encontrar_coluna(df, ['Local Pick-UP', 'LOCAL PICK-UP']),
            'pax': self._encontrar_coluna(df, ['PAX', 'Pax']),
            'horario': self._encontrar_coluna(df, ['HORÁRIO', 'Hora Voo']),
            'data_servico': self._encontrar_coluna(df, ['DATA', 'Data Reserva']),
            'servico': self._encontrar_coluna(df, ['SERVIÇOS', 'Serviço'])
        }
        
        data_atual = None
        
        for idx, row in df.iterrows():
            # Atualiza data atual se presente
            if col_mapping['data_servico'] and pd.notna(row[col_mapping['data_servico']]):
                try:
                    data_atual = pd.to_datetime(row[col_mapping['data_servico']]).date()
                except:
                    pass
            
            # Pula se não há serviço ou cliente
            if not self._tem_dados_minimos(row, col_mapping):
                continue
            
            # Cria objeto Servico
            servico_obj = Servico(
                numero_venda=self._obter_valor_string(row, col_mapping['numero_venda']),
                cliente=self._obter_valor_string(row, col_mapping['cliente']),
                local_pickup=self._obter_valor_string(row, col_mapping['local_pickup']),
                pax=self._obter_valor_int(row, col_mapping['pax']),
                horario=self._obter_valor_time(row, col_mapping['horario']),
                data_do_servico=data_atual or datetime.now().date(),
                servico=self._obter_valor_string(row, col_mapping['servico']),
                linha_original=idx + 2  # +2 porque pandas é 0-based e Excel começa na linha 1
            )
            
            servicos.append(servico_obj)
        
        return servicos
    
    def _encontrar_coluna(self, df: pd.DataFrame, nomes_possiveis: List[str]) -> Optional[str]:
        """Encontra uma coluna pelos nomes possíveis"""
        for nome in nomes_possiveis:
            if nome in df.columns:
                return nome
        return None
    
    def _tem_dados_minimos(self, row: pd.Series, col_mapping: Dict) -> bool:
        """Verifica se a linha tem dados mínimos necessários"""
        cliente = self._obter_valor_string(row, col_mapping['cliente'])
        servico = self._obter_valor_string(row, col_mapping['servico'])
        return bool(cliente or servico)
    
    def _obter_valor_string(self, row: pd.Series, coluna: Optional[str]) -> str:
        """Obtém valor string de uma célula"""
        if not coluna or coluna not in row:
            return ""
        valor = row[coluna]
        if pd.isna(valor):
            return ""
        return str(valor).strip()
    
    def _obter_valor_int(self, row: pd.Series, coluna: Optional[str]) -> int:
        """Obtém valor inteiro de uma célula"""
        if not coluna or coluna not in row:
            return 0
        try:
            valor = row[coluna]
            if pd.isna(valor):
                return 0
            return int(float(valor))
        except (ValueError, TypeError):
            return 0
    
    def _obter_valor_time(self, row: pd.Series, coluna: Optional[str]) -> Optional[time]:
        """Obtém valor time de uma célula"""
        if not coluna or coluna not in row:
            return None
        
        try:
            valor = row[coluna]
            if pd.isna(valor):
                return None
            
            # Se já é um time
            if isinstance(valor, time):
                return valor
            
            # Se é datetime
            if isinstance(valor, (pd.Timestamp, datetime)):
                return valor.time()
            
            # Se é string, tenta fazer parse
            if isinstance(valor, str):
                # Tenta formatos comuns
                for fmt in ['%H:%M', '%H:%M:%S', '%I:%M %p']:
                    try:
                        return datetime.strptime(valor.strip(), fmt).time()
                    except ValueError:
                        continue
            
            return None
            
        except Exception:
            return None