# 🚐 Fretamento Intertouring - Sistema de Gestão de Escalas

<div align="center">

![Django](https://img.shields.io/badge/Django-4.2.7-092E20?style=flat&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=flat&logo=bootstrap&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)

**Sistema avançado de gerenciamento de escalas de fretamento com interface Kanban, otimização inteligente de rotas e precificação automatizada.**

[📚 Documentação](docs/) | [🚀 Deploy](DEPLOY_VERCEL.md) | [🐳 Docker](docker-compose.yml) | [📊 Demo](#screenshots)

</div>

---

## � Índice

- [🎯 Sobre o Projeto](#-sobre-o-projeto)
- [✨ Funcionalidades](#-funcionalidades)
- [🏗️ Arquitetura](#️-arquitetura)
- [🚀 Instalação](#-instalação)
- [💻 Uso](#-uso)
- [🐳 Deploy](#-deploy)
- [🔧 Tecnologias](#-tecnologias)
- [📊 Screenshots](#-screenshots)
- [🤝 Contribuição](#-contribuição)
- [📄 Licença](#-licença)

---

## 🎯 Sobre o Projeto

O **Fretamento Intertouring** é um sistema completo de gestão de escalas de fretamento desenvolvido para otimizar operações de transporte turístico. O sistema combina:

- **Interface Kanban intuitiva** para visualização e organização de serviços
- **Algoritmos de otimização** para alocação eficiente de vans
- **Precificação inteligente** com busca fuzzy em tarifários
- **Exportação avançada** para Excel com formatação brasileira
- **Sistema de aprovação** com controle de usuários
- **Análise de lucratividade** em tempo real

### 🎯 Objetivos

- **Automatizar** o processo de criação e gestão de escalas
- **Otimizar** a alocação de veículos para maximizar ocupação
- **Padronizar** preços usando tarifários inteligentes
- **Simplificar** aprovação e exportação de escalas
- **Aumentar** eficiência operacional e lucratividade

---

## ✨ Funcionalidades

### 🗂️ Gestão de Escalas

- **📅 Calendário Interativo**: Visualização mensal com status das escalas
- **📊 Dashboard Analítico**: KPIs de performance e lucratividade
- **🔄 Importação Automática**: Integração com planilhas de dados
- **✅ Sistema de Aprovação**: Workflow com controle de usuários

### 🎯 Interface Kanban

- **🏷️ Agrupamento Inteligente**: Serviços similares agrupados automaticamente
- **🖱️ Drag & Drop**: Reorganização visual de serviços entre vans
- **🎨 Código de Cores**: Status visual para diferentes tipos de serviço
- **🔍 Filtros Avançados**: Por cliente, PAX, valor, status

### 🚐 Otimização de Vans

- **🧠 Algoritmo Inteligente**: Otimização baseada em PAX e rotas
- **💰 Análise de Lucratividade**: Cálculo automático de margem
- **🚗 Recomendação de Veículos**: Sugestão do veículo ideal por serviço
- **📈 Relatórios de Ocupação**: Métricas detalhadas de utilização

### 💲 Precificação Automatizada

- **🔍 Busca Fuzzy**: Algoritmo inteligente para encontrar preços similares
- **📋 Múltiplos Tarifários**: Integração com tarifários JW e Motoristas
- **⚡ Cálculo em Tempo Real**: Preços atualizados automaticamente
- **📊 Histórico de Preços**: Rastreamento de variações de preço

### 📤 Exportação Avançada

- **📊 Excel Profissional**: Formatação brasileira completa
- **🎨 Formatação Condicional**: Células coloridas por status
- **📈 Gráficos Automáticos**: Visualizações de performance
- **💾 Templates Personalizados**: Modelos para diferentes relatórios

---

## 🏗️ Arquitetura

### 🎨 Frontend
```
Bootstrap 5 + JavaScript
├── Interface Kanban interativa
├── Filtros em tempo real
├── Modais de confirmação
├── Drag & Drop nativo
└── Responsividade completa
```

### 🖥️ Backend
```
Django 4.2.7 + Python 3.10+
├── Models otimizados com índices
├── Views baseadas em classes
├── Middleware de segurança
├── Sistema de cache inteligente
└── APIs RESTful para frontend
```

### 🗄️ Banco de Dados
```
SQLite (Dev) / PostgreSQL (Prod)
├── Escalas e Serviços
├── Alocações de Van
├── Grupos de Serviços
├── Logs de Auditoria
└── Usuários e Permissões
```

### 🧮 Algoritmos Especializados
```
Otimização e Precificação
├── Busca Fuzzy para preços
├── Algoritmo de agrupamento
├── Otimização de PAX/Van
├── Cálculo de lucratividade
└── Recomendação de veículos
```

---

## 🚀 Instalação

### 📋 Pré-requisitos

- **Python 3.10+** 
- **Git**
- **Virtualenv** (recomendado)

### 🔧 Instalação Local

```bash
# 1. Clonar o repositório
git clone https://github.com/andersonodev/fretamento-intertouring.git
cd fretamento-intertouring

# 2. Criar ambiente virtual
python -m venv venv

# 3. Ativar ambiente virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Configurar banco de dados
python manage.py migrate

# 6. Criar superusuário
python manage.py createsuperuser

# 7. Executar servidor
python manage.py runserver
```

### 🌐 Acesso ao Sistema

```
URL: http://127.0.0.1:8000
Admin: http://127.0.0.1:8000/admin
Login: Use as credenciais do superusuário criado
```

---

## 💻 Uso

### 📅 1. Criando uma Nova Escala

```python
# Via interface web ou programaticamente:
from escalas.models import Escala
from datetime import date

escala = Escala.objects.create(
    data=date.today(),
    etapa='ESTRUTURA'
)
```

### 📊 2. Importando Dados

1. **Acesse** a escala criada
2. **Clique** em "Puxar Dados"
3. **Selecione** a planilha de serviços
4. **Aguarde** o processamento automático

### 🎯 3. Usando o Kanban

```javascript
// Arrastar serviços entre vans
document.addEventListener('DOMContentLoaded', function() {
    // Drag & Drop automático ativado
    // Filtragem em tempo real disponível
    // Agrupamento inteligente ativo
});
```

### ⚡ 4. Otimizando Escalas

1. **Na interface Kanban**, clique em "Otimizar"
2. **Algoritmo** rearanja serviços automaticamente
3. **Resultado** maximiza ocupação e lucratividade
4. **Revisão** manual sempre possível

### 📤 5. Exportando para Excel

```python
# Formatação completa em português brasileiro
from escalas.views import ExportarEscalaExcelView

# Exportação inclui:
# - Formatação de moeda (R$)
# - Datas em formato brasileiro
# - Cores condicionais por status
# - Totalizadores automáticos
```

---

## 🐳 Deploy

### ☁️ Deploy na Vercel (Recomendado para demonstração)

```bash
# 1. Configurar variáveis de ambiente
DJANGO_SECRET_KEY=sua-chave-secreta
DJANGO_SETTINGS_MODULE=fretamento_project.settings_vercel

# 2. Deploy automático via GitHub
git push origin main
# Conectar repositório na Vercel Dashboard

# 3. Configurar domínio (opcional)
# Interface da Vercel > Settings > Domains
```

### 🐳 Deploy com Docker (Produção)

```bash
# 1. Configurar ambiente
cp .env.example .env
nano .env  # Editar variáveis

# 2. Deploy completo
chmod +x deploy.sh
./deploy.sh

# 3. Acessar aplicação
# http://seu-servidor.com
```

### 📚 Guias Detalhados

- **[📄 Deploy Vercel](DEPLOY_VERCEL.md)**: Guia completo com SQLite
- **[🐳 Deploy Docker](AMBIENTES_DEPLOY.md)**: Comparação de ambientes
- **[⚙️ Configuração](docs/deployment.md)**: Configurações avançadas

---

## 🔧 Tecnologias

### 🖥️ Backend

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **Django** | 4.2.7 | Framework web principal |
| **Python** | 3.10+ | Linguagem de programação |
| **SQLite** | 3.x | Banco de dados (desenvolvimento) |
| **PostgreSQL** | 15+ | Banco de dados (produção) |
| **Crispy Forms** | 2.0+ | Formulários estilizados |

### 🎨 Frontend

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **Bootstrap** | 5.3 | Framework CSS |
| **JavaScript** | ES6+ | Interatividade |
| **Font Awesome** | 6.0+ | Ícones |
| **Chart.js** | 4.0+ | Gráficos (futuro) |

### 🧮 Algoritmos Especializados

| Componente | Descrição |
|------------|-----------|
| **Busca Fuzzy** | Algoritmo de similaridade de strings para preços |
| **Otimização PAX** | Distribuição inteligente de passageiros |
| **Agrupamento** | Clustering de serviços similares |
| **Precificação** | Cálculo automático baseado em tarifários |

### 🛠️ Ferramentas de Desenvolvimento

| Ferramenta | Uso |
|------------|-----|
| **MkDocs** | Documentação técnica |
| **Docker** | Containerização |
| **GitHub Actions** | CI/CD |
| **Vercel** | Deploy serverless |

---

## 📊 Screenshots

### 🗓️ Dashboard Principal
![Dashboard](docs/images/dashboard.png)
*Visão geral das escalas com KPIs de performance*

### 🎯 Interface Kanban
![Kanban](docs/images/kanban.png)
*Sistema de arrastar e soltar para organização de serviços*

### 📈 Análise de Lucratividade
![Analytics](docs/images/analytics.png)
*Relatórios detalhados de performance e lucratividade*

### 📤 Exportação Excel
![Excel](docs/images/excel-export.png)
*Planilhas profissionais com formatação brasileira*

---

## 🤝 Contribuição

Contribuições são muito bem-vindas! Por favor, siga estas diretrizes:

### 🔄 Processo de Contribuição

1. **Fork** o projeto
2. **Crie** uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. **Abra** um Pull Request

### 📝 Padrões de Código

```python
# Siga as convenções do Django
class MinhaView(TemplateView):
    """Docstring obrigatória para todas as classes"""
    template_name = 'app/template.html'
    
    def get_context_data(self, **kwargs):
        """Método bem documentado"""
        context = super().get_context_data(**kwargs)
        # Sua lógica aqui
        return context
```

### 🧪 Testes

```bash
# Executar todos os testes
python manage.py test

# Testes específicos
python manage.py test escalas.tests.TestEscalaModel

# Coverage
coverage run --source='.' manage.py test
coverage report
```

### 📚 Documentação

Este projeto inclui documentação abrangente hospedada no GitHub Pages:

- **📚 [Documentação Online](https://seu-usuario.github.io/fretamento-intertouring/)** - Acesse a documentação completa
- **🏗️ [Arquitetura do Sistema](https://seu-usuario.github.io/fretamento-intertouring/architecture/)** - Diagramas e documentação técnica
- **⚙️ [Algoritmos e Lógica](https://seu-usuario.github.io/fretamento-intertouring/algorithms/)** - Fluxogramas detalhados
- **📊 [Business Intelligence](https://seu-usuario.github.io/fretamento-intertouring/business-intelligence/)** - Analytics e relatórios

#### Executar Documentação Localmente

```bash
# Instalar MkDocs
pip install mkdocs mkdocs-material

# Navegar para o diretório de documentação
cd docs

# Servir localmente
mkdocs serve

# Acessar em http://127.0.0.1:8000
```

#### Deploy Automático

A documentação é automaticamente deployada no GitHub Pages através do GitHub Actions sempre que há push na branch `main`. O workflow inclui:

- ✅ Validação da sintaxe MkDocs
- 🔧 Build da documentação
- 🚀 Deploy automático no GitHub Pages
- 📋 Validação de links e referências

#### Contribuindo com a Documentação

- **Sempre** documente novas funcionalidades
- **Atualize** README.md se necessário  
- **Inclua** exemplos de uso
- **Mantenha** docs/ atualizada

---

## 📁 Estrutura do Projeto

```
fretamento-intertouring/
├── 📁 core/                     # App principal de serviços
│   ├── models.py               # Serviços, clientes, tarifários
│   ├── views.py                # Views de negócio
│   ├── busca_inteligente_precos.py  # Algoritmo de precificação
│   └── tarifarios.py           # Gestão de tarifários
├── 📁 escalas/                  # App de escalas e alocações
│   ├── models.py               # Escalas, grupos, alocações
│   ├── views.py                # Kanban, otimização, export
│   ├── services.py             # Lógica de negócio
│   └── urls.py                 # Rotas específicas
├── 📁 authentication/           # Sistema de autenticação
├── 📁 templates/                # Templates HTML
│   ├── 📁 base/                # Templates base
│   ├── 📁 escalas/             # Templates de escalas
│   └── 📁 core/                # Templates de serviços
├── 📁 static/                   # Arquivos estáticos
│   ├── 📁 css/                 # Estilos customizados
│   ├── 📁 js/                  # JavaScript
│   └── 📁 images/              # Imagens
├── 📁 docs/                     # Documentação MkDocs
├── 📁 docker/                   # Configurações Docker
├── 📄 requirements.txt          # Dependências Python
├── 📄 docker-compose.yml        # Orquestração Docker
├── 📄 vercel.json              # Configuração Vercel
└── 📄 README.md                # Este arquivo
```

---

## 🔐 Segurança

### 🛡️ Configurações de Segurança

```python
# settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

### 🔑 Autenticação

- **Login obrigatório** para todas as funcionalidades
- **Permissions** baseadas em grupos
- **Sessions** com timeout configurável
- **CSRF** protection ativada

### 📊 Auditoria

```python
# Logs automáticos de todas as ações
LogEscala.objects.create(
    escala=escala,
    acao='OTIMIZAR',
    usuario=request.user,
    ip_address=get_client_ip(request),
    descricao="Escala otimizada automaticamente"
)
```

---

## 🐛 Solução de Problemas

### ❗ Problemas Comuns

#### 1. Erro de Migração
```bash
# Resetar migrações
python manage.py migrate --fake escalas zero
python manage.py migrate escalas
```

#### 2. Problemas de Static Files
```bash
# Recolher arquivos estáticos
python manage.py collectstatic --noinput
```

#### 3. Erro de Dependências
```bash
# Reinstalar dependências
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

#### 4. Problemas no Kanban
```javascript
// Verificar console do browser
// Recarregar página com Ctrl+F5
// Limpar cache do navegador
```

### 📞 Suporte

- **📧 Email**: suporte@intertouring.com
- **🐛 Issues**: [GitHub Issues](https://github.com/andersonodev/fretamento-intertouring/issues)
- **📚 Docs**: [Documentação Completa](docs/)
- **💬 Discussions**: [GitHub Discussions](https://github.com/andersonodev/fretamento-intertouring/discussions)

---

## 📈 Roadmap

### 🎯 Próximas Funcionalidades

- [ ] **API REST completa** para integrações
- [ ] **App mobile** para motoristas
- [ ] **Notificações em tempo real** via WebSockets
- [ ] **Relatórios avançados** com Business Intelligence
- [ ] **Integração GPS** para tracking de vans
- [ ] **Sistema de rating** de clientes e motoristas

### 🔮 Visão de Longo Prazo

- [ ] **Machine Learning** para previsão de demanda
- [ ] **Otimização de rotas** com mapas reais
- [ ] **Integração financeira** com ERP
- [ ] **Dashboard executivo** em tempo real
- [ ] **Marketplace** de prestadores de serviço

---

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

```
MIT License

Copyright (c) 2024 Intertouring

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Agradecimentos

- **Django Community** pela framework excepcional
- **Bootstrap Team** pelo framework CSS
- **Contribuidores** que ajudaram no desenvolvimento
- **Intertouring** pela oportunidade de desenvolvimento

---

<div align="center">

**Desenvolvido com ❤️ para otimizar operações de fretamento**

[⭐ Star no GitHub](https://github.com/andersonodev/fretamento-intertouring) | [🐛 Reportar Bug](https://github.com/andersonodev/fretamento-intertouring/issues) | [💡 Sugerir Feature](https://github.com/andersonodev/fretamento-intertouring/issues)

</div>

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