# Sistema de## 🚀 Funcionalidades

### Core Features
- **Upload de Planilhas**: Processa planilhas de OS (Excel/CSV) automaticamente
- **Agrupamento Inteligente**: Agrupa serviços por proximidade temporal (35 minutos)
- **Priorização Automática**: Hotelbeds/Holiday e Barra da Tijuca têm prioridade
- **Alocação de Veículos**: Recomenda veículos baseado no número de PAX
- **Cálculos de Preços**: Sistema integrado de tarifários JW e Motoristas
- **Escalas Diárias**: Gerenciamento de Van 1 e Van 2 com intervalos de 2 horas
- **Interface Web**: Dashboard completo para gestão

### Sistema de Tarifários
- **Tarifário JW**: Preços específicos por tipo de veículo (Executivo, Van 15, Van 18, Micro, Ônibus)
- **Tarifário Motoristas**: Preços base multiplicados por número de venda
- **Simulador de Preços**: Interface para teste e simulação de preços
- **Histórico de Cálculos**: Registro completo de todos os cálculos realizados
- **Busca Inteligente**: Localização rápida de preços específicos nos tarifários
![Sistema de Fretamento](https://img.shields.io/badge/Django-4.2-green) ![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Status](https://img.shields.io/badge/Status-Pronto-success)

Sistema completo para gerenciamento de escalas de fretamento, baseado na lógica original do Google Apps Script, agora implementado em Django para melhor performance e escalabilidade.

## 🚀 Funcionalidades

### ✅ Upload e Processamento de Planilhas
- **Formatos suportados**: `.xlsx`, `.xls`, `.csv`
- **Limpeza automática** de dados desnecessários
- **Normalização** de serviços e cabeçalhos
- **Validação** e tratamento de erros

### 🧠 Agrupamento Inteligente
- **Janela de agrupamento**: 35 minutos para serviços similares
- **Soma automática** de PAX
- **Concatenação** de números de venda
- **Detecção de prioridades** (Hotelbeds, Holiday, Barra)

### 🚐 Gestão de Escalas
- **Criação automática** de estruturas diárias
- **Distribuição inteligente** entre Van 1 e Van 2
- **Otimização** com regras de negócio
- **Visualização completa** das escalas

### 📊 Exportação e Relatórios
- **Export para Excel** com formatação
- **Cálculos automáticos** de custos e receitas
- **Diagnósticos detalhados** do sistema
- **Histórico completo** de processamentos

## 🛠️ Instalação Rápida

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Setup Automático (Linux/Mac)
```bash
# Execute o script de setup
./setup.sh
```

### Setup Manual
```bash
# 1. Crie um ambiente virtual
python -m venv venv

# 2. Ative o ambiente virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute as migrações
python manage.py makemigrations
python manage.py migrate

# 5. Crie um superusuário
python manage.py createsuperuser

# 6. Inicie o servidor
python manage.py runserver
```

## 📋 Uso Básico

### 1. Processamento de Planilhas
```bash
# Acesse a URL de upload
http://localhost:8000/upload/

# Faça upload da planilha OS (Excel)
# O sistema automaticamente:
# - Remove colunas desnecessárias
# - Normaliza dados de clientes e voos
# - Agrupa serviços por proximidade temporal
# - Calcula preços usando tarifários integrados
# - Gera escalas otimizadas
```

### 2. Gerenciamento de Tarifários
```bash
# Visualizar tarifários
http://localhost:8000/tarifarios/

# Simular preços
http://localhost:8000/simulador-precos/

# Buscar preço específico
http://localhost:8000/buscar-preco/

# Ver histórico de cálculos
http://localhost:8000/historico-calculos/
```

### 3. Gestão de Escalas
```bash
# Criar escala para data específica
http://localhost:8000/escalas/criar/

# Gerenciar escalas existentes
http://localhost:8000/escalas/

# Exportar relatórios
http://localhost:8000/escalas/relatorio/
```

## 🔧 Arquitetura

### Lógica de Agrupamento (Baseada no Script Original)

#### Etapa 1: Agrupamento por Nome
- Serviços com **mesmo nome**
- Diferença de até **35 minutos**
- PAX somados automaticamente
- Números de venda concatenados

#### Etapa 2: Seleção e Priorização
- Grupos entre **4 e 10 PAX**
- **Prioridade 1**: Clientes Hotelbeds/Holiday
- **Prioridade 2**: Destino Barra da Tijuca
- Transfers OUT regulares com ≥4 PAX

#### Etapa 3: Distribuição nas Vans
- **Van 1**: Prioritários primeiro
- **Van 2**: Complementares
- **Intervalo mínimo**: 2 horas entre serviços
- Distribuição alternada para melhor balanceamento

## 📁 Estrutura do Projeto

```
fretamento/
├── core/                   # App principal
│   ├── models.py          # Modelos de dados (Servico, GrupoServico)
│   ├── logic.py           # Lógica de agrupamento
│   ├── processors.py      # Processamento de planilhas OS
│   └── views.py           # Views da web
├── escalas/               # App de escalas
│   ├── models.py          # Modelos de escala
│   ├── services.py        # Serviços de escala
│   └── views.py           # Views de escala
├── templates/             # Templates HTML
├── setup.sh              # Script de configuração
└── requirements.txt       # Dependências
```

## 🎯 Principais Recursos

### 🔄 Processamento da Planilha OS
Implementa a função `limparOS()` original:
- Remove colunas desnecessárias (File Operadora, Fone Contato, etc.)
- Limpa linhas com "folga" ou dados inválidos
- Separa Cliente/Titular
- Padroniza serviços (Disposição, transfers)
- Normaliza cabeçalhos

### 🧩 Sistema de Escalas
Implementa as funções originais:
- `_processarCriacao()`: Cria estrutura do dia
- `_processarPuxada()`: Importa dados da OS
- `_processarOtimizacao()`: Aplica agrupamento inteligente

### 📊 Interface Web Moderna
- Dashboard com estatísticas
- Upload com feedback visual
- Visualização completa das escalas
- Exportação para Excel

## 🚀 Próximos Passos

1. **Instale o sistema** executando `./setup.sh`
2. **Acesse** http://localhost:8000
3. **Faça upload** da sua planilha OS
4. **Crie e otimize** suas escalas
5. **Exporte** os resultados

---

**🚌 Sistema completo de fretamento desenvolvido com Django**

*Automatize suas escalas com a mesma lógica confiável do Google Apps Script, agora com interface web moderna e recursos avançados.*