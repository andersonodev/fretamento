from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
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
        indexes = [
            models.Index(fields=['data']),
            models.Index(fields=['etapa']),
            models.Index(fields=['status']),
            models.Index(fields=['data', 'etapa']),
            models.Index(fields=['created_at']),
        ]
    
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
        total = 0
        for alocacao in self.alocacoes.filter(van='VAN1'):
            if alocacao.preco_calculado:
                total += alocacao.preco_calculado
        return total
    
    @property
    def total_van2_valor(self):
        """Retorna o valor total da Van 2"""
        total = 0
        for alocacao in self.alocacoes.filter(van='VAN2'):
            if alocacao.preco_calculado:
                total += alocacao.preco_calculado
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
    numeros_venda = models.TextField(blank=True, help_text="Números de venda concatenados separados por ' / '")
    
    # Controle
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['van', 'ordem']
        verbose_name = 'Grupo de Serviços'
        verbose_name_plural = 'Grupos de Serviços'
        # Índices para otimização de performance
        indexes = [
            models.Index(fields=['escala']),
            models.Index(fields=['van']),
            models.Index(fields=['ordem']),
            models.Index(fields=['escala', 'van']),
            models.Index(fields=['van', 'ordem']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        return f"{self.cliente_principal} - {self.van} ({self.servicos.count()} serviços)"
    
    def recalcular_totais(self):
        """Recalcula totais do grupo baseado nos serviços"""
        servicos = self.servicos.all()
        self.total_pax = sum(s.servico.pax for s in servicos)
        self.total_valor = sum(s.preco_calculado or 0 for s in servicos)
        
        # Concatenar números de venda
        vendas = []
        for s in servicos:
            if s.servico.numero_venda:
                vendas.append(s.servico.numero_venda)
        self.numeros_venda = ' / '.join(vendas)
        
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
    
    def get_servicos_concatenados(self):
        """Retorna serviços concatenados com '/' se diferentes"""
        servicos_unicos = self.get_servicos_unicos()
        return ' / '.join(servicos_unicos) if len(servicos_unicos) > 1 else (servicos_unicos[0] if servicos_unicos else '')
    
    def get_pickups_concatenados(self):
        """Retorna pickups concatenados com '/' se diferentes"""
        pickups_unicos = self.get_pickups_unicos()
        return ' / '.join(pickups_unicos) if len(pickups_unicos) > 1 else (pickups_unicos[0] if pickups_unicos else '')
    
    def get_clientes_concatenados(self):
        """Retorna clientes concatenados com '/' se diferentes"""
        clientes_unicos = self.get_clientes_unicos()
        return ' / '.join(clientes_unicos) if len(clientes_unicos) > 1 else (clientes_unicos[0] if clientes_unicos else '')
    
    def get_horarios_concatenados(self):
        """Retorna horários concatenados com '/' se diferentes"""
        horarios = []
        for s in self.servicos.all():
            if s.servico.horario:
                horario_str = s.servico.horario.strftime('%H:%M')
                if horario_str not in horarios:
                    horarios.append(horario_str)
        return ' / '.join(horarios) if len(horarios) > 1 else (horarios[0] if horarios else '')


class ServicoGrupo(models.Model):
    """Relacionamento entre serviços e grupos"""
    
    grupo = models.ForeignKey(GrupoServico, on_delete=models.CASCADE, related_name='servicos')
    alocacao = models.OneToOneField('AlocacaoVan', on_delete=models.CASCADE, related_name='grupo_info')
    
    class Meta:
        verbose_name = 'Serviço no Grupo'
        verbose_name_plural = 'Serviços nos Grupos'
        # Índices para otimização de performance
        indexes = [
            models.Index(fields=['grupo']),
            models.Index(fields=['alocacao']),
        ]
    
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
    detalhes_precificacao = models.JSONField(null=True, blank=True, help_text="Detalhes de como o preço foi calculado")
    
    # Status de alocação para otimização
    STATUS_ALOCACAO_CHOICES = [
        ('ALOCADO', 'Alocado'),
        ('NAO_ALOCADO', 'Não alocado'),
    ]
    status_alocacao = models.CharField(
        max_length=20, 
        choices=STATUS_ALOCACAO_CHOICES, 
        default='NAO_ALOCADO',  # PADRÃO ALTERADO PARA NÃO ALOCADO
        help_text="Status da alocação após otimização"
    )
    
    class Meta:
        ordering = ['van', 'ordem']
        unique_together = ['escala', 'servico']
        verbose_name = 'Alocação Van'
        verbose_name_plural = 'Alocações Van'
        # Índices para otimização de performance
        indexes = [
            models.Index(fields=['escala']),
            models.Index(fields=['van']),
            models.Index(fields=['ordem']),
            models.Index(fields=['status_alocacao']),
            models.Index(fields=['escala', 'van']),
            models.Index(fields=['van', 'ordem']),
            models.Index(fields=['escala', 'status_alocacao']),
        ]
    
    def __str__(self):
        return f"{self.servico.cliente} - {self.van} (Ordem: {self.ordem})"
    
    def calcular_preco_e_veiculo(self):
        """
        Calcula e armazena preço e veículo recomendado usando sistema inteligente
        que consulta tanto o tarifário JW quanto o de motoristas com busca fuzzy
        """
        from core.busca_inteligente_precos import BuscadorInteligentePrecosCodigoDoAnalista
        from decimal import Decimal, InvalidOperation
        from django.utils import timezone
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Inicializar buscador inteligente
            buscador = BuscadorInteligentePrecosCodigoDoAnalista()
            
            # Buscar preço usando algoritmo inteligente
            veiculo, preco, fonte = buscador.buscar_preco_inteligente(
                nome_servico=self.servico.servico,
                pax=self.servico.pax,
                numero_venda=str(self.servico.numero_venda) if self.servico.numero_venda else "1"
            )
            
            # Obter detalhes adicionais da precificação
            detalhes = {
                'metodo': 'busca_inteligente',
                'servico_original': self.servico.servico,
                'pax': self.servico.pax,
                'numero_venda': self.servico.numero_venda,
                'veiculo_calculado': veiculo,
                'preco_encontrado': float(preco),
                'fonte_tarifario': fonte,
                'data_calculo': timezone.now().isoformat(),
                'algoritmo_usado': 'fuzzy_search_v2'
            }
            
            # Tentar obter mais detalhes específicos do tarifário usado
            if 'JW' in fonte:
                # Buscar chave específica no JW
                chave_jw, preco_jw, sim_jw = buscador.buscar_melhor_match_tarifario(
                    self.servico.servico, buscador.TARIFARIO_JW, 0.4
                )
                detalhes.update({
                    'tarifario': 'JW',
                    'chave_encontrada': chave_jw,
                    'similaridade': float(sim_jw),
                    'preco_tabela': float(preco_jw.get(veiculo, 0) if isinstance(preco_jw, dict) else preco_jw),
                    'observacoes': f'Preço do veículo {veiculo} na tabela JW'
                })
            elif 'Motoristas' in fonte:
                # Buscar chave específica no Motoristas
                chave_mot, preco_mot, sim_mot = buscador.buscar_melhor_match_tarifario(
                    self.servico.servico, buscador.TARIFARIO_MOTORISTAS, 0.25
                )
                detalhes.update({
                    'tarifario': 'Motoristas',
                    'chave_encontrada': chave_mot,
                    'similaridade': float(sim_mot),
                    'preco_tabela': float(preco_mot),
                    'multiplicador': 1,  # Não usamos mais multiplicador
                    'observacoes': 'Preço base do tarifário de motoristas'
                })
            else:
                # Preço padrão
                detalhes.update({
                    'tarifario': 'Padrão',
                    'chave_encontrada': 'N/A',
                    'similaridade': 0.0,
                    'preco_tabela': float(preco),
                    'observacoes': f'Preço padrão baseado no veículo {veiculo} e {self.servico.pax} PAX'
                })
            
            # Validar resultado
            if preco is None or preco == '' or str(preco).strip() == '':
                preco = 0.0
                logger.warning(f"Preço inválido para serviço {self.servico.id}. Usando 0.0")
            
            # Converter para float seguro
            preco = float(preco) if preco else 0.0
            
            # Armazenar resultados
            self.veiculo_recomendado = veiculo
            self.preco_calculado = preco
            self.detalhes_precificacao = detalhes
            
            # Calcular lucratividade (baseado no valor vs pax)
            if self.servico.pax > 0:
                self.lucratividade = preco / self.servico.pax
            else:
                self.lucratividade = 0.0
            
            # Log detalhado para debug
            logger.info(f"Precificação - Serviço: {self.servico.servico[:50]}... | "
                       f"PAX: {self.servico.pax} | Veículo: {veiculo} | "
                       f"Preço: R$ {preco:.2f} | Fonte: {fonte}")
            
            self.save()
            return veiculo, preco
            
        except (InvalidOperation, ValueError, TypeError, ZeroDivisionError) as e:
            # Em caso de erro, usar valores padrão inteligentes baseados no PAX
            logger.error(f"Erro ao calcular preço para alocação {self.id}: {e}")
            
            # Veículo baseado no PAX
            pax = getattr(self.servico, 'pax', 0) or 0
            if pax <= 3:
                veiculo_padrao = "Executivo"
                preco_padrao = 200.0
            elif pax <= 11:
                veiculo_padrao = "Van 15 lugares"
                preco_padrao = 300.0
            elif pax <= 14:
                veiculo_padrao = "Van 18 lugares"
                preco_padrao = 350.0
            elif pax <= 26:
                veiculo_padrao = "Micro"
                preco_padrao = 500.0
            else:
                veiculo_padrao = "Ônibus"
                preco_padrao = 800.0
            
            self.veiculo_recomendado = veiculo_padrao
            self.preco_calculado = preco_padrao
            self.lucratividade = preco_padrao / max(pax, 1)
            
            # Salvar detalhes do erro também
            self.detalhes_precificacao = {
                'metodo': 'erro_fallback',
                'servico_original': getattr(self.servico, 'servico', 'N/A'),
                'pax': pax,
                'veiculo_calculado': veiculo_padrao,
                'preco_encontrado': preco_padrao,
                'fonte_tarifario': 'Padrão (erro)',
                'data_calculo': timezone.now().isoformat(),
                'erro_original': str(e),
                'tarifario': 'Padrão',
                'observacoes': f'Preço de fallback devido a erro no cálculo principal'
            }
            
            logger.info(f"Usando preço padrão - PAX: {pax} | Veículo: {veiculo_padrao} | Preço: R$ {preco_padrao:.2f}")
            
            self.save()
            return veiculo_padrao, preco_padrao


class LogEscala(models.Model):
    """Model para registrar logs de ações importantes nas escalas"""
    
    ACAO_CHOICES = [
        ('CRIAR', 'Escala Criada'),
        ('PUXAR_DADOS', 'Dados Puxados'),
        ('OTIMIZAR', 'Escala Otimizada'),
        ('FORMATAR', 'Escala Formatada'),
        ('APROVAR', 'Escala Aprovada'),
        ('REJEITAR', 'Escala Rejeitada'),
        ('EXPORTAR', 'Escala Exportada'),
        ('EXCLUIR', 'Escala Excluída'),
        ('ADICIONAR_MANUAL', 'Serviço Adicionado Manualmente'),
    ]
    
    escala = models.ForeignKey(Escala, on_delete=models.CASCADE, related_name='logs')
    acao = models.CharField(max_length=20, choices=ACAO_CHOICES)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    descricao = models.TextField(blank=True, help_text="Detalhes da ação realizada")
    dados_antes = models.JSONField(null=True, blank=True, help_text="Estado antes da ação")
    dados_depois = models.JSONField(null=True, blank=True, help_text="Estado depois da ação")
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Log de Escala'
        verbose_name_plural = 'Logs de Escalas'
        # Índices para otimização de performance
        indexes = [
            models.Index(fields=['escala']),
            models.Index(fields=['acao']),
            models.Index(fields=['usuario']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['escala', 'acao']),
            models.Index(fields=['escala', 'timestamp']),
            models.Index(fields=['usuario', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_acao_display()} - {self.escala.data.strftime('%d/%m/%Y')} por {self.usuario.username if self.usuario else 'Sistema'}"
