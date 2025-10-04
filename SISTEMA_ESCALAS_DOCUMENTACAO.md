# Sistema de Escalas de Fretamento - Documentação Completa

## 🎯 Visão Geral
Sistema completo de gerenciamento de escalas de fretamento com duas etapas de criação, distribuição automática e interface Kanban para organização manual dos serviços entre vans.

## ✨ Funcionalidades Implementadas

### 1. Processo de Duas Etapas
**Etapa 1: Criação da Estrutura**
- Cria estrutura básica da escala para uma data específica
- Status: `ESTRUTURA`
- Pronta para receber dados

**Etapa 2: Puxar Dados**
- Puxa serviços de uma data de origem selecionada
- Distribui automaticamente entre Van 1 e Van 2
- Status: `DADOS_PUXADOS`

**Etapa 3: Otimização (Opcional)**
- Redistribui serviços baseado em lucratividade
- Status: `OTIMIZADA`

### 2. Distribuição Inteligente
- **Distribuição Inicial**: Alterna automaticamente entre Van 1 e Van 2
- **Balanceamento**: Embaralha serviços para distribuição mais equilibrada
- **Cálculo Automático**: Preço e veículo recomendado calculados automaticamente

### 3. Interface Kanban
- **Drag & Drop**: Arraste serviços entre Van 1 e Van 2
- **Atualização em Tempo Real**: Move serviços via AJAX
- **Feedback Visual**: Indicadores visuais durante arraste
- **Preservação de Estado**: Marca movimentações manuais

### 4. Visualização Completa dos Dados
**Informações Exibidas por Serviço:**
- ✅ Cliente
- ✅ Número da compra
- ✅ PAX (passageiros)
- ✅ Valor calculado
- ✅ Serviço/destino
- ✅ Local de pickup
- ✅ Horário
- ✅ Número de venda
- ✅ Veículo recomendado
- ✅ Score de lucratividade
- ✅ Indicador de alocação (automática/manual)

### 5. Estatísticas e Resumos
**Por Van:**
- Total de PAX
- Valor total
- Quantidade de serviços

**Geral:**
- Soma de todas as vans
- Status da otimização
- Data de origem dos dados

## 🗂️ Estrutura do Sistema

### Modelos (models.py)
```python
class Escala:
    - data: Data da escala
    - etapa: ESTRUTURA → DADOS_PUXADOS → OTIMIZADA
    - data_origem: Data de onde vieram os dados
    - criado_em: Timestamp de criação

class AlocacaoVan:
    - escala: FK para Escala
    - servico: FK para Servico (core app)
    - van: VAN1 ou VAN2
    - ordem: Posição na van
    - preco_calculado: Valor calculado automaticamente
    - veiculo_recomendado: Tipo de veículo sugerido
    - lucratividade: Score de lucratividade
    - automatica: Se foi alocação automática ou manual
```

### Views Principais
1. **GerenciarEscalasView**: Lista e gerencia escalas existentes
2. **PuxarDadosView**: Interface para selecionar data origem e puxar dados
3. **VisualizarEscalaView**: Interface Kanban com todos os dados
4. **MoverServicoView**: API para movimentar serviços via drag & drop
5. **ExportarEscalaView**: Exportação para Excel

### Templates
1. **gerenciar.html**: Lista de escalas com ações
2. **puxar_dados.html**: Seleção de data com preview
3. **visualizar.html**: Interface Kanban completa

## 🚀 Como Usar

### 1. Criar Nova Escala
1. Acesse "Gerenciar Escalas"
2. Insira data desejada
3. Clique "Criar Escala"
4. Estrutura criada com status `ESTRUTURA`

### 2. Puxar Dados
1. Na escala criada, clique "Puxar Dados"
2. Selecione data de origem na lista
3. Visualize preview com estatísticas
4. Confirme para distribuir automaticamente
5. Status muda para `DADOS_PUXADOS`

### 3. Visualizar e Reorganizar
1. Clique "Visualizar" na escala
2. Veja distribuição entre Van 1 e Van 2
3. Arraste serviços entre vans conforme necessário
4. Sistema salva automaticamente via AJAX

### 4. Otimizar (Opcional)
1. Na página de visualização
2. Clique "Otimizar Escala"
3. Sistema redistribui por lucratividade
4. Status muda para `OTIMIZADA`

### 5. Exportar
1. Clique "Exportar para Excel"
2. Download do arquivo com todos os dados

## 🎨 Interface Kanban

### Recursos Visuais
- **Cards Detalhados**: Mostram todas as informações do serviço
- **Badges Coloridos**: PAX, valor, status
- **Ícones Intuitivos**: Cada tipo de informação tem seu ícone
- **Cores por Van**: Van 1 (azul), Van 2 (azul claro)
- **Feedback Visual**: Hover effects, drag indicators

### Drag & Drop
- **Arrastar**: Clique e arraste qualquer card de serviço
- **Soltar**: Drop em qualquer área da van destino
- **Feedback**: Área destino fica destacada durante arraste
- **Persistência**: Mudanças salvas automaticamente

### Responsividade
- **Desktop**: Duas colunas lado a lado
- **Mobile**: Empilhamento vertical automático
- **Touch**: Funciona em dispositivos touch

## 🔧 Tecnologias Utilizadas

### Backend
- **Django 4.2.7**: Framework principal
- **Python**: Lógica de negócio
- **SQLite**: Banco de dados (configurável)

### Frontend
- **Bootstrap 5**: Interface responsiva
- **Font Awesome**: Ícones
- **JavaScript Vanilla**: Drag & Drop e AJAX
- **CSS Custom**: Animações e efeitos

### Integração
- **AJAX**: Comunicação assíncrona
- **JSON**: Formato de dados
- **CSRF Protection**: Segurança Django

## 📊 Cálculos Automáticos

### Preço Calculado
Baseado no tipo de serviço e quantidade de passageiros:
- Diferentes preços por categoria
- Cálculo automático por alocação

### Lucratividade
Score de 0-10 baseado em:
- Margem de lucro
- Número de passageiros
- Tipo de serviço

### Veículo Recomendado
Sugestão baseada em:
- Quantidade de PAX
- Tipo de serviço
- Distância/localização

## 🚨 Validações e Segurança

### Validações
- Data obrigatória para criação de escala
- Verificação de dados disponíveis na data origem
- Prevenção de duplicatas de data
- Validação de etapas do processo

### Segurança
- CSRF tokens em formulários
- Validação de permissões
- Sanitização de inputs
- Proteção contra SQL injection

## 📈 Performance

### Otimizações
- Queries otimizadas com select_related
- Agregações no banco de dados
- Transações atômicas
- Cache de cálculos

### Escalabilidade
- Paginação em listas grandes
- Lazy loading de dados
- Estrutura modular
- Separação de responsabilidades

## 🎯 Próximos Passos (Opcionais)

### Melhorias Futuras
1. **Filtros Avançados**: Por cliente, região, valor
2. **Relatórios**: Dashboards com gráficos
3. **Notificações**: Alertas para conflitos
4. **API REST**: Para integração externa
5. **Mobile App**: Aplicativo nativo
6. **Backup Automático**: Segurança de dados

### Customizações
1. **Regras de Negócio**: Configuráveis por usuário
2. **Templates de Email**: Notificações automáticas
3. **Integração GPS**: Otimização de rotas
4. **Machine Learning**: Previsão de demanda

---

## 📞 Suporte

Sistema totalmente funcional e testado. Todas as funcionalidades solicitadas foram implementadas:

✅ **Sistema de duas etapas** (estrutura → dados → otimização)  
✅ **Puxar dados da data indicada** pelo usuário  
✅ **Distribuição igual entre vans** com embaralhamento  
✅ **Interface Kanban** para mover serviços  
✅ **Todos os dados da planilha** (número compra, PAX, valor, pickup, etc.)  
✅ **Otimização por lucratividade**  
✅ **Interface moderna e responsiva**  

O sistema está pronto para uso em produção! 🎉