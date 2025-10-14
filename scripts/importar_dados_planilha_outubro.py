#!/usr/bin/env python3
"""
Script para importar dados da planilha de controle de Van - Outubro 2025
para o sistema de fretamento.

Processa o arquivo CSV e cria:
- Serviços no modelo Servico
- Escalas no modelo Escala  
- Alocações no modelo AlocacaoVan
"""

import os
import sys
import django
import csv
import re
from datetime import datetime, date
from decimal import Decimal
from django.utils import timezone

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.models import Servico
from escalas.models import Escala, AlocacaoVan
from django.contrib.auth.models import User


class ImportadorPlanilhaOutubro:
    def __init__(self):
        self.linha_atual = 0
        self.servicos_criados = 0
        self.escalas_criadas = 0
        self.erros = []
        self.data_atual = None
        self.van_atual = None
        self.em_secao_van = False
        
    def log(self, message):
        """Log com informação da linha atual"""
        print(f"Linha {self.linha_atual}: {message}")
    
    def extrair_valor_monetario(self, valor_str):
        """Extrai valor monetário de string como 'R$ 308,00'"""
        if not valor_str or valor_str.strip() == '':
            return Decimal('0.00')
        
        # Remove R$, espaços e substitui vírgula por ponto
        valor_limpo = valor_str.replace('R$', '').replace(' ', '').replace(',', '.')
        
        # Remove sinal negativo se estiver no início
        valor_limpo = valor_limpo.replace('-', '')
        
        try:
            return Decimal(valor_limpo)
        except:
            self.log(f"Erro ao converter valor monetário: {valor_str}")
            return Decimal('0.00')
    
    def parse_data(self, data_str):
        """Converte string de data DD/MM/YY para date object"""
        if not data_str or data_str.strip() == '':
            return None
            
        try:
            # Remove espaços e tenta diferentes formatos
            data_str = data_str.strip()
            
            # Formato DD/MM/YY
            if '/' in data_str and len(data_str.split('/')) == 3:
                dia, mes, ano = data_str.split('/')
                
                # Se ano tem 2 dígitos, assumir 20XX
                if len(ano) == 2:
                    ano = '20' + ano
                
                return date(int(ano), int(mes), int(dia))
            
            return None
        except Exception as e:
            self.log(f"Erro ao fazer parse da data '{data_str}': {e}")
            return None
    
    def parse_horario(self, horario_str):
        """Converte string de horário HH:MM para time object"""
        if not horario_str or horario_str.strip() == '':
            return None
            
        try:
            horario_str = horario_str.strip()
            if ':' in horario_str:
                hora, minuto = horario_str.split(':')
                return datetime.strptime(f"{hora}:{minuto}", "%H:%M").time()
            return None
        except Exception as e:
            self.log(f"Erro ao fazer parse do horário '{horario_str}': {e}")
            return None
    
    def extrair_numeros_venda(self, nr_venda_str):
        """Extrai números de venda da string, lidando com múltiplos números"""
        if not nr_venda_str or nr_venda_str.strip() == '':
            return []
        
        # Remove espaços e divide por '/'
        numeros = []
        for parte in nr_venda_str.split('/'):
            parte = parte.strip()
            if parte:
                # Extrai apenas números
                numero = re.sub(r'[^\d]', '', parte)
                if numero:
                    numeros.append(numero)
        
        return numeros
    
    def determinar_van_da_linha(self, linha):
        """Determina qual van baseado no contexto da linha"""
        # Primeiro elemento da linha
        primeiro_campo = linha[0] if len(linha) > 0 else ''
        
        # Se a linha tem marcador explícito de Van
        if primeiro_campo and 'Van' in primeiro_campo:
            if '01' in primeiro_campo or 'Van 01' in primeiro_campo:
                self.van_atual = 'VAN1'
                self.em_secao_van = True
                self.log(f"Mudando para Van 01 (VAN1)")
                return 'VAN1'
            elif '02' in primeiro_campo or 'Van 02' in primeiro_campo:
                self.van_atual = 'VAN2'
                self.em_secao_van = True
                self.log(f"Mudando para Van 02 (VAN2)")
                return 'VAN2'
        
        # Se não tem marcador, usar a van atual (contexto anterior)
        return self.van_atual
    
    def linha_tem_dados_servico(self, linha):
        """Verifica se a linha contém dados de serviço válidos"""
        if len(linha) < 7:  # Precisa ter pelo menos 7 colunas
            return False
            
        nr_venda = linha[1] if len(linha) > 1 else ''
        servicos = linha[6] if len(linha) > 6 else ''
        
        # Deve ter número de venda E descrição do serviço
        # E não deve ser linha de totais (que geralmente não tem número de venda)
        return (nr_venda and nr_venda.strip() and 
                servicos and servicos.strip() and 
                not servicos.strip().startswith('R$') and
                not 'total' in servicos.lower())
    
    def criar_servico(self, data_servico, nr_venda, pax, horario, servicos_desc, valor_custo, observacao, van):
        """Cria um serviço no banco de dados"""
        try:
            # Se há múltiplos números de venda, criar um serviço para cada
            numeros_venda = self.extrair_numeros_venda(nr_venda)
            
            if not numeros_venda:
                numeros_venda = ['']  # Criar ao menos um serviço sem número
            
            # Extrair valor monetário corretamente
            valor_original = self.extrair_valor_monetario(valor_custo)
            
            for numero in numeros_venda:
                servico = Servico.objects.create(
                    numero_venda=numero,
                    cliente='Cliente Importado',  # Será preenchido depois
                    local_pickup='',  # Será extraído do serviço
                    pax=int(pax) if pax else 0,
                    horario=horario,
                    data_do_servico=data_servico,
                    servico=servicos_desc or '',
                    linha_original=self.linha_atual,
                    arquivo_origem='VAN FRETAMENTO CONTROLE - Outubro 25.csv'
                )
                
                self.log(f"Serviço criado ID {servico.id} ({van}): {servicos_desc[:50]}... - PAX: {pax} - Valor: R$ {valor_original}")
                
                # Criar ou buscar escala para a data
                escala, created = Escala.objects.get_or_create(
                    data=data_servico,
                    defaults={
                        'etapa': 'DADOS_PUXADOS',
                        'status': 'PENDENTE'
                    }
                )
                
                if created:
                    self.escalas_criadas += 1
                    self.log(f"Escala criada para {data_servico}")
                
                # Criar alocação na van correta
                alocacao = AlocacaoVan.objects.create(
                    escala=escala,
                    servico=servico,
                    van=van,
                    ordem=self.servicos_criados + 1,
                    automatica=False,  # Importação manual
                    preco_calculado=valor_original  # Usar valor original da planilha
                )
                
                # NÃO calcular preço automaticamente, manter o da planilha
                # alocacao.calcular_preco_e_veiculo()
                
                self.servicos_criados += 1
            
        except Exception as e:
            erro = f"Erro ao criar serviço na linha {self.linha_atual}: {e}"
            self.log(erro)
            self.erros.append(erro)
    
    def processar_linha(self, linha):
        """Processa uma linha individual do CSV"""
        self.linha_atual += 1
        
        # Pular linhas vazias ou cabeçalhos
        if not any(linha) or self.linha_atual <= 3:
            return
        
        # Extrair campos da linha
        data_str = linha[0] if len(linha) > 0 else ''
        nr_venda = linha[1] if len(linha) > 1 else ''
        pax = linha[2] if len(linha) > 2 else ''
        horario_str = linha[3] if len(linha) > 3 else ''
        inicio = linha[4] if len(linha) > 4 else ''
        termino = linha[5] if len(linha) > 5 else ''
        servicos = linha[6] if len(linha) > 6 else ''
        valor_custo = linha[7] if len(linha) > 7 else ''
        valor_van_dia = linha[8] if len(linha) > 8 else ''
        observacao = linha[9] if len(linha) > 9 else ''
        
        # Debug da linha atual
        self.log(f"Processando: Data='{data_str}' | Nr_Venda='{nr_venda}' | PAX='{pax}' | Serviços='{servicos}' | Van_Atual='{self.van_atual}'")
        
        # Se a linha tem data, atualizar data atual
        data_parseada = self.parse_data(data_str)
        if data_parseada:
            self.data_atual = data_parseada
            self.log(f"Nova data encontrada: {self.data_atual}")
            return  # Pular processamento desta linha, só atualiza data
        
        # Determinar van atual - isso pode mudar a van_atual
        van_linha = self.determinar_van_da_linha(linha)
        
        # Se ainda não temos van definida e temos dados de serviço, assumir Van 01
        if self.linha_tem_dados_servico(linha) and not self.van_atual:
            self.van_atual = 'VAN1'
            self.log(f"Primeira linha de dados encontrada, assumindo Van 01 (VAN1)")
        
        # ESPECIAL: Se temos dados de serviço mas ainda não temos data,
        # assumir que é data do dia anterior ao primeiro encontrado ou usar data padrão
        if self.linha_tem_dados_servico(linha) and not self.data_atual and self.van_atual:
            # Se é início da planilha sem data, usar primeira data padrão
            from datetime import date
            self.data_atual = date(2025, 10, 1)  # Primeira data de outubro
            self.log(f"Dados de serviço sem data encontrados, assumindo data padrão: {self.data_atual}")
        
        # Se é uma linha de dados de serviço válida e temos data e van
        if self.linha_tem_dados_servico(linha) and self.data_atual and self.van_atual:
            horario = self.parse_horario(horario_str)
            pax_int = 0
            
            try:
                pax_int = int(pax) if pax else 0
            except:
                pass
            
            self.log(f"Criando serviço para {self.van_atual}: {servicos[:50]}...")
            
            self.criar_servico(
                data_servico=self.data_atual,
                nr_venda=nr_venda,
                pax=pax_int,
                horario=horario,
                servicos_desc=servicos,
                valor_custo=valor_custo,
                observacao=observacao,
                van=self.van_atual
            )
    
    def importar_arquivo(self, caminho_arquivo):
        """Importa todo o arquivo CSV"""
        self.log(f"Iniciando importação do arquivo: {caminho_arquivo}")
        
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                leitor = csv.reader(arquivo)
                
                for linha in leitor:
                    self.processar_linha(linha)
            
            self.log("=" * 60)
            self.log("RESUMO DA IMPORTAÇÃO")
            self.log("=" * 60)
            self.log(f"Linhas processadas: {self.linha_atual}")
            self.log(f"Serviços criados: {self.servicos_criados}")
            self.log(f"Escalas criadas: {self.escalas_criadas}")
            self.log(f"Erros encontrados: {len(self.erros)}")
            
            if self.erros:
                self.log("\nERROS ENCONTRADOS:")
                for erro in self.erros:
                    self.log(f"- {erro}")
            
            self.log("\nImportação concluída!")
            
        except Exception as e:
            self.log(f"Erro crítico durante importação: {e}")
            raise


def main():
    """Função principal"""
    print("Importador de Planilha de Outubro 2025")
    print("=" * 50)
    
    caminho_arquivo = '/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/alimentar/VAN FRETAMENTO CONTROLE - Outubro 25.csv'
    
    if not os.path.exists(caminho_arquivo):
        print(f"Arquivo não encontrado: {caminho_arquivo}")
        return
    
    # Confirmar antes de importar
    resposta = input(f"Deseja importar dados do arquivo? (s/N): ")
    if resposta.lower() != 's':
        print("Importação cancelada.")
        return
    
    # Executar importação
    importador = ImportadorPlanilhaOutubro()
    importador.importar_arquivo(caminho_arquivo)


if __name__ == '__main__':
    main()