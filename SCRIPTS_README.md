# 🚀 Scripts de Deploy - Fretamento System

Scripts automatizados para facilitar o processo de desenvolvimento e deploy do sistema de fretamento.

## 📁 Scripts Disponíveis

### 1. 🔄 `git_push.sh` - Commit e Push Automático

Script para automatizar o processo de commit e push para o GitHub.

#### Como usar:
```bash
# Com mensagem direta
./git_push.sh "feat: adicionar nova funcionalidade"

# Sem mensagem (será solicitada)
./git_push.sh
```

#### O que faz:
- ✅ Verifica status do repositório
- ✅ Adiciona todos os arquivos modificados (`git add .`)
- ✅ Faz commit com mensagem personalizada
- ✅ Faz push para `origin main`
- ✅ Mostra status final
- 🔄 **Trigger automático do deploy no Vercel**

---

### 2. 🚀 `heroku_deploy.sh` - Deploy no Heroku

Script completo para deploy no Heroku com verificações e automações.

#### Como usar:
```bash
./heroku_deploy.sh
```

#### O que faz:
- 🔐 Verifica login no Heroku (faz login se necessário)
- 📱 Lista apps disponíveis
- 🎯 Permite escolher o app (padrão: `fretamento-intertouring`)
- ⚠️ Verifica alterações não commitadas
- 🚀 Faz push para o Heroku
- 🔄 Executa migrações automáticas
- 📦 Coleta arquivos estáticos
- 📋 Mostra logs recentes
- 🌐 Opção para abrir o app no navegador

---

## 🛠️ Configuração Inicial

### Pré-requisitos:
- Git configurado
- Heroku CLI instalado
- Repositório conectado ao Heroku

### Primeira execução:
```bash
# Tornar scripts executáveis (já feito)
chmod +x git_push.sh heroku_deploy.sh

# Verificar Heroku CLI
heroku --version

# Login no Heroku (se necessário)
heroku login
```

---

## 🔄 Fluxo de Trabalho Típico

### Desenvolvimento → Production:

1. **Fazer alterações no código**
2. **Commit e Push:**
   ```bash
   ./git_push.sh "descrição das alterações"
   ```
   - ✅ Código vai para GitHub
   - ✅ Vercel faz deploy automático do proxy

3. **Deploy no Heroku:**
   ```bash
   ./heroku_deploy.sh
   ```
   - ✅ Backend Django vai para produção
   - ✅ Migrações executadas
   - ✅ Arquivos estáticos coletados

### Resultado:
- 🌐 **Frontend/Proxy**: Vercel (domínio personalizado)
- 🖥️ **Backend**: Heroku (API Django)

---

## 🎨 Features dos Scripts

### Cores e Interface:
- 🔵 Azul: Informações e processos
- 🟢 Verde: Sucesso
- 🟡 Amarelo: Avisos
- 🔴 Vermelho: Erros
- 🟣 Roxo: Deploy Heroku

### Segurança:
- ✅ Verificações antes de executar
- ✅ Confirmações para ações críticas
- ✅ Tratamento de erros
- ✅ Status detalhado

### Automação:
- ✅ Login automático quando necessário
- ✅ Detecção de alterações não commitadas
- ✅ Execução automática de migrações
- ✅ Coleta automática de estáticos

---

## 🐛 Troubleshooting

### Erro no git push:
```bash
# Verificar status
git status

# Resolver conflitos se necessário
git pull origin main
```

### Erro no Heroku:
```bash
# Verificar logs
heroku logs --tail -a seu-app

# Verificar login
heroku auth:whoami
```

### Scripts não executam:
```bash
# Verificar permissões
ls -la *.sh

# Dar permissão se necessário
chmod +x git_push.sh heroku_deploy.sh
```

---

## 📞 Suporte

Em caso de problemas:
1. Verificar logs dos scripts
2. Verificar status do Git e Heroku
3. Consultar documentação oficial:
   - [Git](https://git-scm.com/docs)
   - [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
   - [Vercel](https://vercel.com/docs)

---

*Scripts criados para otimizar o fluxo de desenvolvimento do Sistema de Fretamento* 🚌✨