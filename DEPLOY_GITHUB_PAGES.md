# 🚀 Deploy do MkDocs no GitHub Pages

Este documento fornece instruções detalhadas para configurar e fazer o deploy da documentação MkDocs no GitHub Pages.

## 📋 Pré-requisitos

- Repositório GitHub
- Permissões de administrador no repositório
- GitHub Actions habilitado

## ⚙️ Configuração do GitHub Pages

### 1. Habilitar GitHub Pages

1. Vá para **Settings** do seu repositório
2. Role até a seção **Pages**
3. Em **Source**, selecione **GitHub Actions**
4. Salve as configurações

### 2. Configurar Workflow do GitHub Actions

O arquivo `.github/workflows/docs.yml` já está configurado e inclui:

```yaml
name: Deploy MkDocs to GitHub Pages

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install mkdocs mkdocs-material pymdown-extensions mkdocs-mermaid2-plugin

      - name: Build documentation
        run: |
          cd docs
          mkdocs build --strict

      - name: Setup Pages
        uses: actions/configure-pages@v3

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v2
        with:
          path: docs/site

  deploy:
    if: github.ref == 'refs/heads/main'
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v2
```

### 3. Estrutura da Documentação

```
docs/
├── mkdocs.yml              # Configuração principal
├── docs/
│   ├── index.md           # Página inicial
│   ├── architecture.md    # Arquitetura do sistema
│   ├── algorithms.md      # Algoritmos e lógica
│   ├── business-intelligence.md  # BI e analytics
│   ├── stylesheets/
│   │   └── extra.css      # Estilos customizados
│   └── javascripts/
│       └── extra.js       # Scripts customizados
└── site/                  # Build output (gerado automaticamente)
```

## 🔧 Configurações Importantes

### mkdocs.yml

```yaml
site_name: Sistema de Fretamento - Documentação
site_description: Documentação completa do sistema de gestão de fretamento
site_url: https://seu-usuario.github.io/fretamento-intertouring/

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.path
    - navigation.top
    - search.highlight
    - search.share
    - toc.follow
    - content.code.copy
    - content.code.select

plugins:
  - search:
      lang: pt
  - mermaid2:
      arguments:
        theme: default

markdown_extensions:
  - pymdownx.mermaid
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:mermaid2.fence_mermaid
```

## 🚀 Processo de Deploy

### Automático (Recomendado)

1. **Faça commit** das alterações na documentação
2. **Push** para a branch `main`
3. **GitHub Actions** executa automaticamente
4. **Documentação** é publicada em poucos minutos

### Manual (Desenvolvimento)

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/fretamento-intertouring.git
cd fretamento-intertouring

# Instalar dependências
pip install mkdocs mkdocs-material pymdown-extensions mkdocs-mermaid2-plugin

# Navegar para docs
cd docs

# Servir localmente
mkdocs serve

# Build para produção
mkdocs build

# Deploy manual (opcional)
mkdocs gh-deploy
```

## 🔍 Verificação do Deploy

### Após o Deploy Automático

1. Vá para **Actions** no GitHub
2. Verifique se o workflow **Deploy MkDocs to GitHub Pages** foi executado com sucesso
3. Acesse a URL: `https://seu-usuario.github.io/fretamento-intertouring/`

### Logs de Debug

Se houver problemas, verifique os logs do GitHub Actions:

1. Clique no workflow com falha
2. Expanda os steps para ver os detalhes
3. Verifique mensagens de erro específicas

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Build Falha - Dependências

```bash
# Erro: ModuleNotFoundError
# Solução: Verificar requirements no workflow
pip install mkdocs mkdocs-material pymdown-extensions mkdocs-mermaid2-plugin
```

#### 2. Build Falha - Sintaxe MkDocs

```bash
# Erro: Configuration error
# Solução: Validar mkdocs.yml
mkdocs build --strict
```

#### 3. Páginas Não Carregam

- Verificar se GitHub Pages está habilitado
- Confirmar que a source é **GitHub Actions**
- Verificar permissões do repositório

#### 4. CSS/JS Não Carrega

```yaml
# Verificar paths no mkdocs.yml
extra_css:
  - stylesheets/extra.css
extra_javascript:
  - javascripts/extra.js
```

### Comandos de Debug

```bash
# Verificar configuração
mkdocs config

# Build com verbose
mkdocs build --verbose

# Verificar plugins
mkdocs --help

# Testar localmente
mkdocs serve --dev-addr=0.0.0.0:8000
```

## 📊 Monitoramento

### GitHub Actions Status Badge

Adicione ao README.md:

```markdown
[![Deploy MkDocs](https://github.com/seu-usuario/fretamento-intertouring/actions/workflows/docs.yml/badge.svg)](https://github.com/seu-usuario/fretamento-intertouring/actions/workflows/docs.yml)
```

### Analytics

Para adicionar Google Analytics:

```yaml
# mkdocs.yml
google_analytics:
  - 'G-XXXXXXXXXX'
  - 'auto'
```

## 🔄 Workflow de Contribuição

1. **Fork** do repositório
2. **Branch** para feature/docs-update
3. **Editar** documentação em `docs/docs/`
4. **Commit** com mensagem descritiva
5. **Push** e criar **Pull Request**
6. **Review** e merge na main
7. **Deploy automático** via GitHub Actions

## 📝 Checklist de Deploy

- [ ] GitHub Pages habilitado
- [ ] Workflow `.github/workflows/docs.yml` configurado
- [ ] `mkdocs.yml` válido
- [ ] Todas as páginas em `docs/docs/` existem
- [ ] CSS/JS customizados funcionando
- [ ] Links internos funcionando
- [ ] Mermaid diagrams renderizando
- [ ] Build local sem erros
- [ ] Commit e push na main
- [ ] GitHub Actions executando
- [ ] Site acessível na URL do GitHub Pages

## 🎯 URLs Importantes

- **Documentação Online**: https://seu-usuario.github.io/fretamento-intertouring/
- **GitHub Actions**: https://github.com/seu-usuario/fretamento-intertouring/actions
- **Configurações Pages**: https://github.com/seu-usuario/fretamento-intertouring/settings/pages
- **Repositório**: https://github.com/seu-usuario/fretamento-intertouring

## 📞 Suporte

Para problemas com o deploy:

1. Verificar [GitHub Actions logs](https://github.com/seu-usuario/fretamento-intertouring/actions)
2. Consultar [MkDocs Documentation](https://www.mkdocs.org/)
3. Verificar [GitHub Pages Documentation](https://docs.github.com/en/pages)
4. Abrir issue no repositório para suporte adicional