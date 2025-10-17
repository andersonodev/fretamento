#!/usr/bin/env python
"""
Script completo para importar dados da planilha de outubro 2025
Captura TODOS os campos: horários, observações, valores acumulados, rentabilidade
"""

import os
import sys
import django
from pathlib import Path
import csv
import re
from datetime import datetime, time
from decimal import Decimal

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from django.db import transaction
from core.models import Servico
from escalas.models import Escala, AlocacaoVan


class ImportadorCompletoOutubro:
    def __init__(self):
        self.arquivo_csv = BASE_DIR / 'alimentar' / 'VAN FRETAMENTO CONTROLE - Outubro 25.csv'
        self.van_atual = 'VAN1'  # Começa com Van 01
        self.data_atual = None
        self.servicos_criados = 0
        self.escalas_criadas = 0
        self.erros = 0
        
        # Campos da planilha completa
        self.COLUNAS = {
            'data': 0,           # Data
            'nr_venda': 1,       # Nr Venda  
            'pax': 2,            # Qtdade Pax
            'horario': 3,        # Horário
            'inicio': 4,         # Início
            'termino': 5,        # Término
            'servicos': 6,       # Serviços
            'valor_custo': 7,    # Valor Custo Tarifário
            'valor_van_dia': 8,  # Valor Van/Dia
            'observacao': 9,     # Observação
            'acum_van01': 10,    # Acumulado Van 01
            'rent_van01': 11,    # Rent Van 01
            'acum_van02': 12,    # Acumulado Van 02
            'rent_van02': 13,    # Rent Van 02
        }
        
    def executar_importacao(self):
        """Executa a importação completa"""
        print("Importador COMPLETO de Planilha de Outubro 2025")
        print("=" * 60)
        
        confirmacao = input("Deseja importar dados COMPLETOS do arquivo? (s/N): ")
        if confirmacao.lower() != 's':
            print("Importação cancelada.")
            return
            
        try:
            with transaction.atomic():
                self._processar_arquivo()
                
            print(f"\n{'='*60}")
            print(f"RESUMO DA IMPORTAÇÃO COMPLETA")
            print(f"{'='*60}")
            print(f"Serviços criados: {self.servicos_criados}")
            print(f"Escalas criadas: {self.escalas_criadas}")
            print(f"Erros encontrados: {self.erros}")
            print(f"\nImportação completa concluída!")
            
        except Exception as e:
            print(f"Erro durante importação: {e}")
            raise
    
    def _processar_arquivo(self):
        """Processa o arquivo CSV linha por linha"""
        print(f"Iniciando importação do arquivo: {self.arquivo_csv}")
        
        with open(self.arquivo_csv, 'r', encoding='utf-8') as arquivo:
            reader = csv.reader(arquivo)
            
            for linha_num, linha in enumerate(reader):
                if linha_num == 0:  # Skip header
                    continue
                    
                # Preencher colunas faltantes
                while len(linha) < 14:
                    linha.append('')
                
                self._processar_linha_completa(linha_num, linha)
                
    def _processar_linha_completa(self, linha_num, linha):
        """Processa uma linha completa da planilha"""
        try:
            # Extrair dados de todas as colunas
            data_str = linha[self.COLUNAS['data']].strip()
            nr_venda = linha[self.COLUNAS['nr_venda']].strip()
            pax_str = linha[self.COLUNAS['pax']].strip()
            horario_str = linha[self.COLUNAS['horario']].strip()
            inicio_str = linha[self.COLUNAS['inicio']].strip()
            termino_str = linha[self.COLUNAS['termino']].strip()
            servicos_str = linha[self.COLUNAS['servicos']].strip()
            valor_custo_str = linha[self.COLUNAS['valor_custo']].strip()
            valor_van_dia_str = linha[self.COLUNAS['valor_van_dia']].strip()
            observacao_str = linha[self.COLUNAS['observacao']].strip()
            acum_van01_str = linha[self.COLUNAS['acum_van01']].strip()
            rent_van01_str = linha[self.COLUNAS['rent_van01']].strip()
            acum_van02_str = linha[self.COLUNAS['acum_van02']].strip()
            rent_van02_str = linha[self.COLUNAS['rent_van02']].strip()
            
            print(f"Linha {linha_num}: Processando: Data='{data_str}' | Nr_Venda='{nr_venda}' | PAX='{pax_str}' | Horário='{horario_str}' | Serviços='{servicos_str}' | Van_Atual='{self.van_atual}'")
            
            # Verificar mudança de VAN
            if self._determinar_van_da_linha(data_str, nr_venda, servicos_str):
                print(f"Linha {linha_num}: Mudando para {self.van_atual}")
            
            # Verificar mudança de data
            if self._processar_data(data_str):
                print(f"Linha {linha_num}: Nova data encontrada: {self.data_atual}")
            
            # Processar serviço se há dados
            if self._linha_tem_dados_servico(nr_venda, pax_str, servicos_str):
                self._criar_servico_completo(
                    linha_num, nr_venda, pax_str, horario_str, 
                    inicio_str, termino_str, servicos_str, 
                    valor_custo_str, valor_van_dia_str, observacao_str,
                    acum_van01_str, rent_van01_str, acum_van02_str, rent_van02_str
                )
                
        except Exception as e:
            print(f"Erro ao processar linha {linha_num}: {e}")
            self.erros += 1
    
    def _determinar_van_da_linha(self, data_str, nr_venda, servicos_str):
        """Determina qual VAN deve ser usada baseado no conteúdo da linha"""
        if data_str == 'Van 01' or (data_str.strip() and 'Van 01' in data_str):
            if self.van_atual != 'VAN1':
                self.van_atual = 'VAN1'
                return True
        elif data_str == 'Van 02' or (data_str.strip() and 'Van 02' in data_str):
            if self.van_atual != 'VAN2':
                self.van_atual = 'VAN2'
                return True
        elif self.servicos_criados == 0 and self._linha_tem_dados_servico(nr_venda, '', servicos_str):
            # Primeira linha com dados assume Van 01
            print(f"Primeira linha de dados encontrada, assumindo Van 01 (VAN1)")
            self.van_atual = 'VAN1'
            return True
        return False
    
    def _processar_data(self, data_str):
        """Processa e atualiza a data atual"""
        if not data_str or data_str in ['Van 01', 'Van 02']:
            return False
            
        # Tentar vários formatos de data
        formatos_data = ['%d/%m/%y', '%d/%m/%Y', '%d/%m/%Y']
        
        for formato in formatos_data:
            try:
                data_obj = datetime.strptime(data_str, formato)
                # Garantir que está em 2025
                if data_obj.year < 2000:
                    data_obj = data_obj.replace(year=2025)
                elif data_obj.year < 2025:
                    data_obj = data_obj.replace(year=2025)
                    
                nova_data = data_obj.date()
                if nova_data != self.data_atual:
                    self.data_atual = nova_data
                    return True
                break
            except ValueError:
                continue
        return False
    
    def _linha_tem_dados_servico(self, nr_venda, pax_str, servicos_str):
        """Verifica se a linha tem dados de serviço"""
        return (nr_venda and nr_venda.strip()) or (pax_str and pax_str.strip()) or (servicos_str and servicos_str.strip())
    
    def _criar_servico_completo(self, linha_num, nr_venda, pax_str, horario_str, 
                               inicio_str, termino_str, servicos_str, 
                               valor_custo_str, valor_van_dia_str, observacao_str,
                               acum_van01_str, rent_van01_str, acum_van02_str, rent_van02_str):
        """Cria serviço com TODOS os campos da planilha"""
        
        # Se não há data definida, usar padrão
        if not self.data_atual:
            self.data_atual = datetime(2025, 10, 1).date()
            print(f"Linha {linha_num}: Dados de serviço sem data encontrados, assumindo data padrão: {self.data_atual}")
        
        # Garantir que existe escala para esta data
        escala, criada = Escala.objects.get_or_create(
            data=self.data_atual,
            defaults={'etapa': 'DADOS_PUXADOS'}
        )
        if criada:
            self.escalas_criadas += 1
            print(f"Linha {linha_num}: Escala criada para {self.data_atual}")
        
        # Processar PAX
        try:
            pax = int(pax_str) if pax_str and pax_str.strip() else 0
        except ValueError:
            pax = 0
        
        # Processar horário
        horario_obj = self._processar_horario(horario_str)
        
        # Processar valores monetários
        valor_custo = self._processar_valor_monetario(valor_custo_str)
        valor_van_dia = self._processar_valor_monetario(valor_van_dia_str)
        acum_van01 = self._processar_valor_monetario(acum_van01_str)
        rent_van01 = self._processar_valor_monetario(rent_van01_str)
        acum_van02 = self._processar_valor_monetario(acum_van02_str)
        rent_van02 = self._processar_valor_monetario(rent_van02_str)
        
        # Separar números de venda múltiplos
        numeros_venda = self._separar_numeros_venda(nr_venda)
        
        for i, numero_venda in enumerate(numeros_venda):
            print(f"Linha {linha_num}: Criando serviço para {self.van_atual}: {servicos_str}...")
            
            # Criar serviço
            servico = Servico.objects.create(
                numero_venda=numero_venda,
                cliente='Cliente Importado',  # Pode ser melhorado depois
                local_pickup='',  # Pode ser extraído do serviço
                pax=pax,
                horario=horario_obj,
                data_do_servico=self.data_atual,
                servico=servicos_str,
                linha_original=linha_num,
                arquivo_origem='VAN FRETAMENTO CONTROLE - Outubro 25.csv'
            )
            
            # Calcular lucratividade baseada na van
            lucratividade = None
            if self.van_atual == 'VAN1' and rent_van01:
                lucratividade = rent_van01
            elif self.van_atual == 'VAN2' and rent_van02:
                lucratividade = rent_van02
            
            # Criar alocação COMPLETA
            alocacao = AlocacaoVan.objects.create(
                escala=escala,
                servico=servico,
                van=self.van_atual,
                ordem=self.servicos_criados + 1,
                automatica=True,
                status_alocacao='NAO_ALOCADO',  # STATUS PADRÃO: NÃO ALOCADO
                preco_calculado=valor_custo,
                lucratividade=lucratividade,
                detalhes_precificacao={
                    'metodo': 'importacao_completa',
                    'dados_originais': {
                        'nr_venda': nr_venda,
                        'pax': pax,
                        'horario': horario_str,
                        'inicio': inicio_str,
                        'termino': termino_str,
                        'servico': servicos_str,
                        'valor_custo_tarifario': valor_custo_str,
                        'valor_van_dia': valor_van_dia_str,
                        'observacao': observacao_str,
                        'acumulado_van01': acum_van01_str,
                        'rent_van01': rent_van01_str,
                        'acumulado_van02': acum_van02_str,
                        'rent_van02': rent_van02_str,
                    },
                    'valores_processados': {
                        'valor_custo': float(valor_custo) if valor_custo else 0,
                        'valor_van_dia': float(valor_van_dia) if valor_van_dia else 0,
                        'acum_van01': float(acum_van01) if acum_van01 else 0,
                        'rent_van01': float(rent_van01) if rent_van01 else 0,
                        'acum_van02': float(acum_van02) if acum_van02 else 0,
                        'rent_van02': float(rent_van02) if rent_van02 else 0,
                    },
                    'observacoes': observacao_str,
                    'linha_planilha': linha_num,
                    'van_atribuida': self.van_atual,
                    'data_importacao': datetime.now().isoformat()
                }
            )
            
            self.servicos_criados += 1
            valor_display = f"R$ {valor_custo:.2f}" if valor_custo else "R$ 0.00"
            print(f"Linha {linha_num}: Serviço criado ID {servico.id} ({self.van_atual}): {servicos_str}... - PAX: {pax} - Valor: {valor_display}")
    
    def _processar_horario(self, horario_str):
        """Converte string de horário para objeto time"""
        if not horario_str or not horario_str.strip():
            return None
            
        # Tentar formatos comuns
        formatos = ['%H:%M', '%H:%M:%S', '%H.%M']
        
        for formato in formatos:
            try:
                horario_obj = datetime.strptime(horario_str.strip(), formato).time()
                return horario_obj
            except ValueError:
                continue
        
        # Se não conseguiu converter, retornar None
        return None
    
    def _processar_valor_monetario(self, valor_str):
        """Converte string de valor monetário para Decimal"""
        if not valor_str or not valor_str.strip():
            return None
            
        # Limpar string (remover R$, espaços, etc.)
        valor_limpo = re.sub(r'[R$\s]', '', valor_str.replace(',', '.'))
        
        # Remover sinais de negativo ou positivo para manter apenas números
        valor_limpo = re.sub(r'^[-+]', '', valor_limpo)
        
        try:
            return Decimal(valor_limpo)
        except:
            return None
    
    def _separar_numeros_venda(self, nr_venda_str):
        """Separa números de venda múltiplos"""
        if not nr_venda_str or not nr_venda_str.strip():
            return ['']
        
        # Separar por / ou espaços múltiplos
        numeros = re.split(r'\s*/\s*|\s+', nr_venda_str.strip())
        return [n.strip() for n in numeros if n.strip()]


def main():
    importador = ImportadorCompletoOutubro()
    importador.executar_importacao()


if __name__ == "__main__":
    main()