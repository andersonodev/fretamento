# Sistema de Tarifários Integrado

## Visão Geral

O sistema Django agora inclui um sistema completo de tarifários integrado que replica a funcionalidade do Google Apps Script original, permitindo cálculos precisos de preços para diferentes tipos de serviços e veículos.

## Componentes Principais

### 1. Tarifários (`core/tarifarios.py`)

#### TARIFARIO_JW
- **Descrição**: Tarifário específico por tipo de veículo
- **Formato**: `{ "Serviço": { "Executivo": 229.00, "Van 15 lugares": 300.00, ... } }`
- **Uso**: Para serviços que têm preços diferenciados por tipo de veículo
- **Exemplos**: 
  - SDU / Zona Sul
  - Transfer Petrópolis
  - Tours específicos

#### TARIFARIO_MOTORISTAS
- **Descrição**: Tarifário com preço fixo por serviço
- **Formato**: `{ "Serviço": 40.00 }`
- **Uso**: Para serviços com preço base que multiplica pelo número de venda
- **Cálculo**: `preço_base * ceil(pax / 4)` (máximo 4 PAX por carro)

### 2. Funções de Cálculo

#### `calcular_preco_servico(servico_obj)`
- Função principal que calcula preço e veículo recomendado
- Retorna: `(veiculo_recomendado, preco_estimado)`
- Processo:
  1. Gera chave do tarifário baseada no serviço
  2. Busca no TARIFARIO_JW primeiro
  3. Se não encontrar, busca no TARIFARIO_MOTORISTAS
  4. Se não encontrar, usa preços básicos

#### `gerar_chave_tarifario(servico_obj)`
- Gera chave de busca baseada nas propriedades do serviço
- Exemplos de chaves geradas:
  - "SDU / Zona Sul"
  - "AIRJ / Barra + Recreio"
  - "À disposição / Tour de 4 horas"
  - "Tour em Petrópolis"

#### `calcular_veiculo_recomendado(pax)`
- Recomenda veículo baseado no número de passageiros:
  - 1-3 PAX: Executivo
  - 4-11 PAX: Van 15 lugares
  - 12-14 PAX: Van 18 lugares
  - 15-26 PAX: Micro
  - 27+ PAX: Ônibus

### 3. Modelo de Dados (`CalculoPreco`)

Armazena histórico de cálculos realizados:

```python
class CalculoPreco(models.Model):
    chave_servico = models.CharField(max_length=255)
    tipo_servico = models.CharField(max_length=100)
    pax = models.IntegerField()
    veiculo_recomendado = models.CharField(max_length=20)
    preco_base = models.DecimalField(max_digits=10, decimal_places=2)
    preco_final = models.DecimalField(max_digits=10, decimal_places=2)
    custo_operacional = models.DecimalField(max_digits=10, decimal_places=2)
    margem = models.DecimalField(max_digits=10, decimal_places=2)
    rentabilidade = models.DecimalField(max_digits=5, decimal_places=2)
    data_calculo = models.DateTimeField(default=timezone.now)
```

### 4. Interface Web

#### Views Disponíveis:
1. **`/tarifarios/`** - Visualização completa dos tarifários
2. **`/simulador-precos/`** - Simulador interativo de preços
3. **`/buscar-preco/`** - Busca específica nos tarifários
4. **`/historico-calculos/`** - Histórico de cálculos realizados
5. **`/api/calcular-preco/`** - API AJAX para cálculos rápidos

#### Funcionalidades:
- **Visualização dos Tarifários**: Tabelas organizadas por JW e Motoristas
- **Simulação de Preços**: Formulário interativo para teste de preços
- **Busca Inteligente**: Busca por chaves específicas nos tarifários
- **Histórico Completo**: Registro de todos os cálculos realizados
- **API AJAX**: Cálculos em tempo real sem recarregar página

### 5. Integração com Sistema Existente

#### Lógica de Processamento (`core/logic.py`)
- Atualizada função `_alocarVeiculoEPreco()` para usar tarifários
- Cálculos automáticos durante processamento de planilhas
- Preços mais precisos baseados em dados reais

#### Admin Interface
- Gerenciamento de cálculos realizados
- Filtros por tipo de tarifário e veículo
- Visualização de margens e rentabilidade

## Exemplos de Uso

### Cálculo Simples
```python
from core.tarifarios import calcular_preco_servico
from core.models import Servico

# Criar serviço
servico = Servico(
    servico="Transfer SDU para Zona Sul",
    tipo="TRANSFER",
    aeroporto="SDU",
    regiao="ZONA SUL",
    pax=2
)

# Calcular preço
veiculo, preco = calcular_preco_servico(servico)
# Retorna: ("Executivo", 229.00)
```

### Busca em Tarifário Específico
```python
from core.tarifarios import buscar_preco_jw, buscar_preco_motoristas

# Busca no tarifário JW
preco_jw = buscar_preco_jw("SDU / Zona Sul", "Executivo")
# Retorna: 229.00

# Busca no tarifário de motoristas
preco_motorista = buscar_preco_motoristas("Transfer In ou Out Sdu / Centro", 3)
# Retorna: 40.00 (1 carro) ou 80.00 (2 carros se PAX > 4)
```

## Configuração e Manutenção

### Atualizando Tarifários
1. Edite `core/tarifarios.py`
2. Atualize as constantes `TARIFARIO_JW` e `TARIFARIO_MOTORISTAS`
3. Reinicie o servidor Django

### Adicionando Novos Serviços
1. Adicione entrada no tarifário apropriado
2. Se necessário, atualize a função `gerar_chave_tarifario()` para reconhecer o novo padrão
3. Teste usando o simulador de preços

### Monitoramento
- Use o admin para visualizar cálculos realizados
- Analise margens e rentabilidade
- Identifique serviços sem preços definidos

## Benefícios da Implementação

1. **Precisão**: Preços baseados em tarifários reais
2. **Flexibilidade**: Suporte a diferentes tipos de veículos e serviços
3. **Rastreabilidade**: Histórico completo de cálculos
4. **Interface Amigável**: Simulador e visualizadores web
5. **Integração**: Funciona automaticamente com o sistema de escalas
6. **Manutenibilidade**: Fácil atualização dos tarifários
7. **Escalabilidade**: Suporte a novos tipos de serviços e veículos

## Próximos Passos

1. **Testes**: Validar todos os cálculos com dados reais
2. **Otimização**: Cache de cálculos frequentes
3. **Relatórios**: Análises de rentabilidade por período
4. **API**: Endpoints para integração externa
5. **Machine Learning**: Sugestões de preços baseadas em histórico