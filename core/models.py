from django.db import models
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import re


class Servico(models.Model):
    """Model para representar um serviço de fretamento"""
    
    TIPO_CHOICES = [
        ('TRANSFER', 'Transfer'),
        ('DISPOSICAO', 'Disposição'),
        ('TOUR', 'Tour'),
        ('OUTRO', 'Outro'),
    ]
    
    DIRECAO_CHOICES = [
        ('IN', 'IN'),
        ('OUT', 'OUT'),
        ('N/A', 'N/A'),
    ]
    
    AEROPORTO_CHOICES = [
        ('GIG', 'GIG'),
        ('SDU', 'SDU'),
        ('N/A', 'N/A'),
    ]
    
    REGIAO_CHOICES = [
        ('ZONA SUL', 'Zona Sul'),
        ('SANTOS DUMONT', 'Santos Dumont'),
        ('BARRA', 'Barra'),
        ('CENTRO', 'Centro'),
        ('BUZIOS', 'Búzios'),
        ('ANGRA', 'Angra'),
        ('PETROPOLIS', 'Petrópolis'),
        ('PARATY', 'Paraty'),
        ('MACAE', 'Macaé'),
        ('N/A', 'N/A'),
    ]
    
    # Campos básicos do serviço
    numero_venda = models.CharField(max_length=100, blank=True)
    cliente = models.CharField(max_length=200)
    local_pickup = models.CharField(max_length=300, blank=True)
    pax = models.IntegerField(default=0, help_text="Número de passageiros")
    horario = models.TimeField(null=True, blank=True)
    data_do_servico = models.DateField()
    servico = models.TextField()
    
    # Campos derivados da análise do serviço
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='OUTRO')
    direcao = models.CharField(max_length=10, choices=DIRECAO_CHOICES, default='N/A')
    aeroporto = models.CharField(max_length=10, choices=AEROPORTO_CHOICES, default='N/A')
    regiao = models.CharField(max_length=20, choices=REGIAO_CHOICES, default='N/A')
    eh_regular = models.BooleanField(default=False)
    eh_prioritario = models.BooleanField(default=False)
    
    # Metadados
    linha_original = models.IntegerField(null=True, blank=True, help_text="Linha na planilha original")
    arquivo_origem = models.CharField(max_length=255, blank=True, help_text="Nome do arquivo de origem")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['data_do_servico', 'horario']
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'
    
    def __str__(self):
        return f"{self.servico} - {self.cliente} ({self.data_do_servico})"
    
    def save(self, *args, **kwargs):
        """Sobrescreve save para extrair detalhes automaticamente"""
        self._extrair_detalhes_do_servico()
        super().save(*args, **kwargs)
    
    def _extrair_detalhes_do_servico(self):
        """Extrai detalhes do serviço baseado no texto"""
        s = self.servico.upper() if self.servico else ""
        
        # Determinar tipo
        if 'DISPOSIÇÃO' in s or 'DISPOSICAO' in s:
            self.tipo = 'DISPOSICAO'
        elif s.startswith('TOUR'):
            self.tipo = 'TOUR'
        elif 'TRANSFER' in s:
            self.tipo = 'TRANSFER'
        else:
            self.tipo = 'OUTRO'
        
        # Determinar direção
        if ' IN ' in s:
            self.direcao = 'IN'
        elif ' OUT ' in s:
            self.direcao = 'OUT'
        else:
            self.direcao = 'N/A'
        
        # Determinar aeroporto
        if 'GIG' in s or 'INTERNACIONAL' in s:
            self.aeroporto = 'GIG'
        elif 'SDU' in s:
            self.aeroporto = 'SDU'
        else:
            self.aeroporto = 'N/A'
        
        # Determinar região
        regioes = {
            'ZONA SUL': ['Z.SUL', 'ZONA SUL', 'COPACABANA', 'IPANEMA', 'LEBLON'],
            'SANTOS DUMONT': ['SANTOS DUMONT'],
            'BARRA': ['BARRA', 'RECREIO'],
            'CENTRO': ['CENTRO'],
            'BUZIOS': ['BÚZIOS', 'BUZIOS'],
            'ANGRA': ['ANGRA DOS REIS', 'ANGRA', 'FRADE', 'VILA GALE'],
            'PETROPOLIS': ['PETRÓPOLIS', 'PETROPOLIS', 'ITAIPAVA'],
            'PARATY': ['PARATY'],
            'MACAE': ['MACAÉ', 'MACAE']
        }
        
        for nome, sinonimos in regioes.items():
            if any(sin in s for sin in sinonimos):
                self.regiao = nome
                break
        else:
            self.regiao = 'N/A'
        
        # Verificar se é regular
        self.eh_regular = 'REGULAR' in s
        
        # Verificar se é prioritário
        cliente_lower = self.cliente.lower() if self.cliente else ""
        cliente_prioritario = 'hotelbeds' in cliente_lower or 'holiday' in cliente_lower
        regiao_prioritaria = self.regiao == 'BARRA'
        self.eh_prioritario = cliente_prioritario or regiao_prioritaria


class GrupoServico(models.Model):
    """Model para representar um grupo de serviços agrupados"""
    
    nome_servico = models.TextField()
    horario_base = models.TimeField()
    data_servico = models.DateField()
    pax_total = models.IntegerField(default=0)
    numero_venda = models.TextField(blank=True, help_text="Números de venda concatenados")
    eh_prioritario = models.BooleanField(default=False)
    
    # Campos para veículo e preço
    veiculo_recomendado = models.CharField(max_length=50, blank=True)
    preco_estimado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['data_servico', 'horario_base']
        verbose_name = 'Grupo de Serviços'
        verbose_name_plural = 'Grupos de Serviços'
    
    def __str__(self):
        return f"{self.nome_servico} - {self.pax_total} PAX ({self.data_servico})"
    
    @property
    def servicos_relacionados(self):
        """Retorna os serviços que fazem parte deste grupo"""
        return self.servicogrupo_set.all()
    
    def calcular_veiculo_e_preco(self):
        """Calcula o veículo recomendado e preço baseado no PAX"""
        pax = self.pax_total
        
        if pax <= 3:
            self.veiculo_recomendado = "Executivo"
        elif pax <= 11:
            self.veiculo_recomendado = "Van 15 lugares"
        elif pax <= 14:
            self.veiculo_recomendado = "Van 18 lugares"
        elif pax <= 26:
            self.veiculo_recomendado = "Micro"
        else:
            self.veiculo_recomendado = "Ônibus"
        
        # Aqui você pode implementar a lógica de preços do tarifário
        # Por enquanto, valor básico
        self.preco_estimado = pax * 50  # Exemplo simples
        
        self.save()


class ServicoGrupo(models.Model):
    """Model para relacionar serviços aos grupos (Many-to-Many)"""
    
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE)
    grupo = models.ForeignKey(GrupoServico, on_delete=models.CASCADE)
    ordem = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['ordem']
        verbose_name = 'Serviço do Grupo'
        verbose_name_plural = 'Serviços dos Grupos'


class ProcessamentoPlanilha(models.Model):
    """Model para controlar o processamento de planilhas"""
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PROCESSANDO', 'Processando'),
        ('CONCLUIDO', 'Concluído'),
        ('ERRO', 'Erro'),
    ]
    
    arquivo = models.FileField(upload_to='planilhas/')
    nome_arquivo = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    linhas_processadas = models.IntegerField(default=0)
    linhas_erro = models.IntegerField(default=0)
    log_processamento = models.TextField(blank=True)
    
    # Campos adicionais para melhor controle
    tamanho_arquivo = models.BigIntegerField(default=0, help_text="Tamanho do arquivo em bytes")
    usuario_upload = models.CharField(max_length=150, blank=True, help_text="Usuário que fez o upload")
    total_servicos_criados = models.IntegerField(default=0, help_text="Total de serviços criados a partir desta planilha")
    data_primeira_linha = models.DateField(null=True, blank=True, help_text="Data do primeiro serviço na planilha")
    data_ultima_linha = models.DateField(null=True, blank=True, help_text="Data do último serviço na planilha")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Processamento de Planilha'
        verbose_name_plural = 'Processamentos de Planilhas'
    
    def __str__(self):
        return f"{self.nome_arquivo} - {self.status}"
    
    @property
    def tamanho_formatado(self):
        """Retorna o tamanho do arquivo formatado"""
        if self.tamanho_arquivo < 1024:
            return f"{self.tamanho_arquivo} bytes"
        elif self.tamanho_arquivo < 1024 * 1024:
            return f"{self.tamanho_arquivo / 1024:.1f} KB"
        else:
            return f"{self.tamanho_arquivo / (1024 * 1024):.1f} MB"
    
    @property
    def periodo_servicos(self):
        """Retorna o período dos serviços desta planilha"""
        if self.data_primeira_linha and self.data_ultima_linha:
            if self.data_primeira_linha == self.data_ultima_linha:
                return self.data_primeira_linha.strftime("%d/%m/%Y")
            else:
                return f"{self.data_primeira_linha.strftime('%d/%m/%Y')} a {self.data_ultima_linha.strftime('%d/%m/%Y')}"
        return "N/A"


class CalculoPreco(models.Model):
    """Modelo para armazenar cálculos de preços realizados"""
    TIPOS_TARIFARIO = [
        ('JW', 'Tarifário JW'),
        ('MOTORISTAS', 'Tarifário Motoristas'),
        ('PERSONALIZADO', 'Preço Personalizado'),
        ('AUTOMATICO', 'Cálculo Automático'),
    ]
    
    TIPOS_VEICULO = [
        ('Executivo', 'Executivo'),
        ('Van 15 lugares', 'Van 15 lugares'),
        ('Van 18 lugares', 'Van 18 lugares'),
        ('Micro', 'Micro'),
        ('Ônibus', 'Ônibus'),
    ]
    
    # Identificação do serviço
    chave_servico = models.CharField(max_length=255, help_text="Chave do serviço no tarifário")
    tipo_servico = models.CharField(max_length=100)
    aeroporto = models.CharField(max_length=10, blank=True)
    regiao = models.CharField(max_length=100, blank=True)
    pax = models.IntegerField(default=1)
    
    # Dados do cálculo
    tipo_tarifario = models.CharField(max_length=20, choices=TIPOS_TARIFARIO, default='AUTOMATICO')
    veiculo_recomendado = models.CharField(max_length=20, choices=TIPOS_VEICULO)
    preco_base = models.DecimalField(max_digits=10, decimal_places=2)
    preco_final = models.DecimalField(max_digits=10, decimal_places=2)
    custo_operacional = models.DecimalField(max_digits=10, decimal_places=2)
    margem = models.DecimalField(max_digits=10, decimal_places=2)
    rentabilidade = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Metadados
    data_calculo = models.DateTimeField(default=timezone.now)
    detalhes_json = models.JSONField(blank=True, null=True, help_text="Detalhes adicionais do cálculo")
    
    class Meta:
        verbose_name = "Cálculo de Preço"
        verbose_name_plural = "Cálculos de Preços"
        ordering = ['-data_calculo']
        indexes = [
            models.Index(fields=['chave_servico']),
            models.Index(fields=['tipo_servico']),
            models.Index(fields=['data_calculo']),
        ]
    
    def __str__(self):
        return f"{self.chave_servico} - {self.veiculo_recomendado} - R$ {self.preco_final}"
    
    @property
    def margem_percentual(self):
        """Calcula margem em percentual"""
        if self.preco_final > 0:
            return (self.margem / self.preco_final) * 100
        return 0
