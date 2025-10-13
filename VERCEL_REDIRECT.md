# 🚌 Fretamento Intertouring

Sistema de Gestão de Fretamento

## 🌐 Arquitetura

### Vercel (Frontend/Redirecionamento)
- **URL**: `https://fretamentointertouring.vercel.app`
- **Função**: Redirecionamento simples e URL amigável
- **Tipo**: Redirect 302 (temporário)

### Heroku (Backend Django)
- **URL**: `https://fretamento-intertouring-d423e478ec7f.herokuapp.com`
- **Framework**: Django 4.2.7
- **Database**: PostgreSQL (Essential 0 - $5/mês)
- **Servidor**: Gunicorn + WhiteNoise

## 📁 Estrutura do Projeto

```
fretamento-intertouring/
├── authentication/          # Sistema de autenticação
├── core/                    # App principal (dashboard, tarifários)
├── escalas/                 # Gestão de escalas e alocações
├── fretamento_project/      # Configurações Django
├── static/                  # Arquivos estáticos
├── templates/               # Templates HTML
├── tests/                   # Testes e scripts de debug
├── index.html              # Página de redirecionamento Vercel
├── vercel.json             # Configuração Vercel (redirect)
├── package.json            # NPM (build Vercel)
├── Procfile                # Processo Heroku
├── requirements.txt        # Dependências Python
└── runtime.txt             # Versão Python

```

## 🚀 Como Funciona

1. **Usuário acessa**: `fretamentointertouring.vercel.app`
2. **Vercel redireciona**: Para URL do Heroku (302)
3. **Heroku responde**: Com Django + PostgreSQL

### Vantagens
- ✅ **URL Limpa**: Domínio personalizado da Vercel
- ✅ **Simples**: Sem proxy complexo
- ✅ **Rápido**: Redirecionamento direto
- ✅ **Confiável**: Sem problemas de timeout

## 🛠️ Scripts Disponíveis

### Git Push Automático
```bash
./git_push.sh "mensagem do commit"
```

### Deploy Heroku
```bash
./heroku_deploy.sh
```

## 📦 Deploy

### Vercel
- **Automático**: Push para `main` → deploy automático
- **Configuração**: `vercel.json` (redirects)

### Heroku
- **Manual**: `git push heroku main`
- **Ou usar**: `./heroku_deploy.sh`

## 🔧 Tecnologias

- **Backend**: Django 4.2.7, Python 3.10
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript
- **Hosting**: Vercel (redirect) + Heroku (app)
- **Cache**: Local (LocMem)

## 📊 Status

- 🟢 **Vercel**: Redirecionamento ativo
- 🟢 **Heroku**: Django rodando
- 🟢 **Database**: PostgreSQL conectado

---

*Sistema de gestão de fretamento para Intertouring* 🚌