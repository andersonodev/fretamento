from django.db import models
from django.contrib.auth.models import User
from core.models import GrupoServico, Servico


class Escala(models.Model):
    """Model para representar uma escala diária"""
    
    ETAPA_CHOICES = [
        ('ESTRUTURA', 'Estrutura Criada'),
        ('DADOS_PUXADOS', 'Dados Puxados'),
        ('OTIMIZADA', 'Otimizada'),
    ]
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADA', 'Aprovada'),
        ('REJEITADA', 'Rejeitada'),
    ]
    
    data = models.DateField(unique=True)
    etapa = models.CharField(max_length=20, choices=ETAPA_CHOICES, default='ESTRUTURA')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    data_origem = models.DateField(null=True, blank=True, help_text="Data de onde os dados foram puxados")
    
    # Campos de aprovação
    aprovada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='escalas_aprovadas')
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    observacoes_aprovacao = models.TextField(blank=True, help_text="Observações sobre a aprovação/rejeição")
    
    # Campos de controle
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['data']
        verbose_name = 'Escala'
        verbose_name_plural = 'Escalas'
    
    def __str__(self):
        return f"Escala {self.data.strftime('%d/%m/%Y')} - {self.get_etapa_display()}"
    
    @property
    def total_van1_pax(self):
        """Retorna o total de PAX da Van 1"""
        return sum(alocacao.servico.pax for alocacao in self.alocacoes.filter(van='VAN1'))
    
    @property
    def total_van2_pax(self):
        """Retorna o total de PAX da Van 2"""
        return sum(alocacao.servico.pax for alocacao in self.alocacoes.filter(van='VAN2'))
    
    @property
    def total_van1_valor(self):
        """Retorna o valor total da Van 1"""
        from core.tarifarios import calcular_preco_servico
        total = 0
        for alocacao in self.alocacoes.filter(van='VAN1'):
            _, preco = calcular_preco_servico(alocacao.servico)
            total += preco
        return total
    
    @property
    def total_van2_valor(self):
        """Retorna o valor total da Van 2"""
        from core.tarifarios import calcular_preco_servico
        total = 0
        for alocacao in self.alocacoes.filter(van='VAN2'):
            _, preco = calcular_preco_servico(alocacao.servico)
            total += preco
        return total
    
    @property
    def tem_dados(self):
        """Verifica se a escala tem dados puxados"""
        return self.etapa in ['DADOS_PUXADOS', 'OTIMIZADA']
    
    @property
    def esta_otimizada(self):
        """Verifica se a escala está otimizada"""
        return self.etapa == 'OTIMIZADA'
    
    @property
    def pode_aprovar(self):
        """Verifica se a escala pode ser aprovada"""
        return self.tem_dados and self.status == 'PENDENTE'
    
    @property
    def esta_aprovada(self):
        """Verifica se a escala está aprovada"""
        return self.status == 'APROVADA'


class GrupoServico(models.Model):
    """Model para agrupar serviços similares no Kanban"""
    
    VAN_CHOICES = [
        ('VAN1', 'Van 1'),
        ('VAN2', 'Van 2'),
    ]
    
    escala = models.ForeignKey(Escala, on_delete=models.CASCADE, related_name='grupos')
    van = models.CharField(max_length=10, choices=VAN_CHOICES)
    ordem = models.IntegerField(default=0, help_text="Ordem do grupo dentro da van")
    
    # Dados consolidados do grupo
    cliente_principal = models.CharField(max_length=200)
    servico_principal = models.TextField()
    local_pickup_principal = models.CharField(max_length=200, blank=True)
    
    # Totais calculados
    total_pax = models.IntegerField(default=0)
    total_valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Controle
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['van', 'ordem']
        verbose_name = 'Grupo de Serviços'
        verbose_name_plural = 'Grupos de Serviços'
    
    def __str__(self):
        return f"{self.cliente_principal} - {self.van} ({self.servicos.count()} serviços)"
    
    def recalcular_totais(self):
        """Recalcula totais do grupo baseado nos serviços"""
        servicos = self.servicos.all()
        self.total_pax = sum(s.servico.pax for s in servicos)
        self.total_valor = sum(s.preco_calculado or 0 for s in servicos)
        self.save()
    
    def get_clientes_unicos(self):
        """Retorna lista de clientes únicos do grupo"""
        return list(set(s.servico.cliente for s in self.servicos.all()))
    
    def get_servicos_unicos(self):
        """Retorna lista de serviços únicos do grupo"""
        return list(set(s.servico.servico for s in self.servicos.all()))
    
    def get_pickups_unicos(self):
        """Retorna lista de pickups únicos do grupo"""
        return list(set(s.servico.local_pickup for s in self.servicos.all() if s.servico.local_pickup))
    
    def get_vendas_unicas(self):
        """Retorna números de venda únicos concatenados com '/' """
        vendas = []
        for s in self.servicos.all():
            if s.servico.numero_venda:
                # Remove .0 do final se existir
                venda = str(s.servico.numero_venda).replace('.0', '')
                if venda not in vendas:
                    vendas.append(venda)
        return ' / '.join(vendas) if vendas else ''
    
    def get_vendas_unicas_lista(self):
        """Retorna lista de números de venda únicos (para uso interno)"""
        vendas = []
        for s in self.servicos.all():
            if s.servico.numero_venda:
                # Remove .0 do final se existir
                venda = str(s.servico.numero_venda).replace('.0', '')
                if venda not in vendas:
                    vendas.append(venda)
        return vendas


class ServicoGrupo(models.Model):
    """Relacionamento entre serviços e grupos"""
    
    grupo = models.ForeignKey(GrupoServico, on_delete=models.CASCADE, related_name='servicos')
    alocacao = models.OneToOneField('AlocacaoVan', on_delete=models.CASCADE, related_name='grupo_info')
    
    class Meta:
        verbose_name = 'Serviço no Grupo'
        verbose_name_plural = 'Serviços nos Grupos'
    
    @property
    def servico(self):
        """Acesso direto ao serviço"""
        return self.alocacao.servico
    
    @property
    def preco_calculado(self):
        """Acesso direto ao preço calculado"""
        return self.alocacao.preco_calculado


class AlocacaoVan(models.Model):
    """Model para gerenciar a alocação específica de serviços nas vans"""
    
    VAN_CHOICES = [
        ('VAN1', 'Van 1'),
        ('VAN2', 'Van 2'),
    ]
    
    escala = models.ForeignKey(Escala, on_delete=models.CASCADE, related_name='alocacoes')
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, null=True, blank=True)
    van = models.CharField(max_length=10, choices=VAN_CHOICES)
    ordem = models.IntegerField(default=0, help_text="Ordem dentro da van")
    automatica = models.BooleanField(default=True, help_text="Se foi alocada automaticamente")
    
    # Campos calculados para otimização
    preco_calculado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    veiculo_recomendado = models.CharField(max_length=50, null=True, blank=True)
    lucratividade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Score de lucratividade")
    
    class Meta:
        ordering = ['van', 'ordem']
        unique_together = ['escala', 'servico']
        verbose_name = 'Alocação Van'
        verbose_name_plural = 'Alocações Van'
    
    def __str__(self):
        return f"{self.servico.cliente} - {self.van} (Ordem: {self.ordem})"
    
    def calcular_preco_e_veiculo(self):
        """Calcula e armazena preço e veículo recomendado"""
        from core.tarifarios import calcular_preco_servico
        veiculo, preco = calcular_preco_servico(self.servico)
        
        self.veiculo_recomendado = veiculo
        self.preco_calculado = preco
        
        # Calcular lucratividade (baseado no valor vs pax)
        if self.servico.pax > 0:
            self.lucratividade = float(preco) / self.servico.pax
        else:
            self.lucratividade = 0
        
        self.save()
        return veiculo, preco
