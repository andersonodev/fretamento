# 🎯 Guia: Banco de Dados Persistente GRATUITO para Heroku

## 🔴 PROBLEMA: SQLite no Heroku

**SQLite NO HEROKU = PERDA DE DADOS!** 

O Heroku usa **filesystem efêmero**:
- ✅ Dados salvos normalmente durante execução
- ❌ **PERDA TOTAL** a cada restart/deploy/sleep
- ⚠️ Apps gratuitos "dormem" após 30 min inatividade

## 🎯 SOLUÇÕES GRATUITAS (PostgreSQL)

### Opção 1: Neon (RECOMENDADA) 🚀
**Plano Gratuito:**
- ✅ 3GB de armazenamento
- ✅ 100 horas compute/mês
- ✅ Conexões ilimitadas
- ✅ Backups automáticos
- ✅ SSL incluído

**Como configurar:**
1. Acesse: https://neon.tech
2. Crie conta gratuita
3. Crie database: `fretamento_db`
4. Copie a CONNECTION STRING

### Opção 2: Supabase
**Plano Gratuito:**
- ✅ 500MB armazenamento
- ✅ 2 projetos
- ✅ API automática
- ✅ Auth integrada

**Como configurar:**
1. Acesse: https://supabase.com
2. Crie conta gratuita
3. Novo projeto: `fretamento-app`
4. Vá em Settings > Database
5. Copie URI de conexão

### Opção 3: Aiven
**Plano Gratuito:**
- ✅ 1 mês trial
- ✅ PostgreSQL 15
- ✅ Backups diários

## 🔧 CONFIGURAÇÃO NO HEROKU

### Passo 1: Configure a variável DATABASE_URL
```bash
# Exemplo para Neon
heroku config:set DATABASE_URL="postgresql://usuario:senha@ep-exemplo.us-east-2.aws.neon.tech/fretamento_db?sslmode=require"

# Exemplo para Supabase  
heroku config:set DATABASE_URL="postgresql://postgres:senha@db.projeto.supabase.co:5432/postgres"
```

### Passo 2: Use as novas configurações
```bash
# Atualizar configuração do Django
heroku config:set DJANGO_SETTINGS_MODULE="fretamento_project.settings_heroku_persistent"
```

### Passo 3: Aplicar migrações
```bash
# Executar migrações no novo banco
heroku run python manage.py migrate

# Criar superusuário
heroku run python manage.py createsuperuser
```

## 💡 VANTAGENS DA SOLUÇÃO

### ✅ Dados Seguros
- Persistência REAL dos dados
- Backups automáticos
- Disponibilidade 24/7

### ✅ 100% Gratuito
- Neon: 3GB grátis permanente
- Supabase: 500MB grátis permanente
- Zero custos adicionais no Heroku

### ✅ Escalável
- Fácil upgrade quando crescer
- Métricas de uso incluídas
- Performance superior ao SQLite

## 🎯 PRÓXIMOS PASSOS

1. **Escolha um provedor** (Recomendo Neon)
2. **Crie conta gratuita**
3. **Configure DATABASE_URL no Heroku**
4. **Execute migrações**
5. **Teste a persistência!**

## 🔍 VERIFICAÇÃO DE FUNCIONAMENTO

### Teste 1: Criar dados
```bash
heroku run python manage.py shell

# No shell Django:
from django.contrib.auth.models import User
User.objects.create_user('teste', 'teste@teste.com', 'senha123')
exit()
```

### Teste 2: Forçar restart
```bash
heroku restart
```

### Teste 3: Verificar dados
```bash
heroku run python manage.py shell

# No shell Django:
from django.contrib.auth.models import User
print(User.objects.filter(username='teste').exists())
# Se retornar True = SUCESSO! Dados persistentes ✅
```

## 📞 PRÓXIMA AÇÃO

**Qual provedor você prefere?**
- 🚀 **Neon** (3GB, mais recursos)
- 🎯 **Supabase** (500MB, mais features)
- ⚡ **Outro** (me diga qual!)

Após escolher, te ajudo a configurar em **5 minutos**!