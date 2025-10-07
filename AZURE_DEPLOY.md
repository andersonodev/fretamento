# 🚀 Deploy Azure Web App - Fretamento

Guia completo para deploy da aplicação Django no Azure Web App.

## 📋 Pré-requisitos

- Conta Azure ativa
- Azure CLI instalado
- Repositório GitHub configurado

## 🔧 Configuração no Azure Portal

### 1. Criar Web App

```bash
# Via Azure CLI
az webapp create \
  --resource-group fretamento-rg \
  --plan fretamento-plan \
  --name fretamento \
  --runtime "PYTHON|3.11" \
  --deployment-source-url https://github.com/andersonodev/fretamento
```

### 2. Configurar Deployment Center

1. **Acesse o Azure Portal**
2. **Vá para o Web App > Deployment Center**
3. **Source:** GitHub
4. **Organização:** andersonodev
5. **Repositório:** fretamento
6. **Branch:** main

### 3. Configurar Application Settings

No Azure Portal > Configuration > Application Settings:

```json
{
  "SCM_DO_BUILD_DURING_DEPLOYMENT": "true",
  "DJANGO_SETTINGS_MODULE": "fretamento_project.settings_azure",
  "DEBUG": "False",
  "USE_DOCKER": "False",
  "SECRET_KEY": "[SUA_SECRET_KEY_AQUI]",
  "ALLOWED_HOSTS": "fretamento.azurewebsites.net,*.azurewebsites.net"
}
```

### 4. Configurar Startup Command

```bash
bash startup.sh
```

## 🗄️ Configuração de Banco de Dados

### Opção 1: PostgreSQL Azure

```bash
# Criar PostgreSQL
az postgres server create \
  --resource-group fretamento-rg \
  --name fretamento-db \
  --admin-user dbadmin \
  --admin-password [SUA_SENHA] \
  --sku-name B_Gen5_1

# Configurar firewall
az postgres server firewall-rule create \
  --resource-group fretamento-rg \
  --server fretamento-db \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

**Connection String:**
```
postgresql://dbadmin@fretamento-db:[SENHA]@fretamento-db.postgres.database.azure.com:5432/postgres?sslmode=require
```

### Opção 2: SQLite (para testes)

Usar configuração padrão do Django com SQLite.

## 📁 Arquivos de Configuração

### `startup.sh`
Script de inicialização que:
- Instala dependências
- Coleta arquivos estáticos  
- Executa migrações
- Inicia Gunicorn

### `settings_azure.py`
Configurações específicas para Azure:
- DEBUG = False
- ALLOWED_HOSTS configurado
- Database via DATABASE_URL
- Static files otimizados
- Logging para Azure

### `azure-webapps-python.yml`
Workflow GitHub Actions:
- Build automático
- Deploy no push para main
- Coleta de static files
- Execução de testes

## 🔐 Secrets Necessários

Configure no GitHub > Settings > Secrets:

```
AZUREAPPSERVICE_PUBLISHPROFILE_FRETAMENTO
SECRET_KEY
DATABASE_URL (opcional)
```

## 🧪 Testando o Deploy

### Local (simulando Azure)
```bash
export DEBUG=False
export USE_DOCKER=False
export DJANGO_SETTINGS_MODULE=fretamento_project.settings_azure

python manage.py collectstatic --noinput
python manage.py migrate
gunicorn fretamento_project.wsgi:application
```

### Verificar no Azure
1. **URL:** https://fretamento.azurewebsites.net
2. **Logs:** Azure Portal > Log Stream
3. **Diagnostics:** Azure Portal > Diagnose and solve problems

## 🔍 Troubleshooting

### Problemas Comuns

1. **Build Failing:**
   - Verificar requirements.txt
   - Checar Python version (3.11)
   - Validar syntax errors

2. **Deploy Failing:**
   - Verificar publish profile
   - Checar application settings
   - Validar startup command

3. **App não inicia:**
   - Verificar logs no Azure Portal
   - Checar DJANGO_SETTINGS_MODULE
   - Validar DATABASE_URL

### Debug Logs

```bash
# Via Azure CLI
az webapp log download --name fretamento --resource-group fretamento-rg
```

## 📊 Monitoramento

- **Application Insights:** Para métricas detalhadas
- **Log Analytics:** Para análise de logs
- **Alerts:** Para notificações de problemas

## 🔄 CI/CD Pipeline

O workflow está configurado para:
1. **Trigger:** Push para branch main
2. **Build:** Instalar deps, coletar static, rodar testes
3. **Deploy:** Deploy automático para Production slot
4. **Rollback:** Manual via Azure Portal se necessário

## 💰 Custos Estimados

- **App Service Plan B1:** ~$13/mês
- **PostgreSQL Basic:** ~$20/mês  
- **Total estimado:** ~$35/mês

## 🎯 Próximos Passos

1. Configurar domínio customizado
2. Habilitar SSL certificate
3. Configurar Application Insights
4. Setup automated backups
5. Configurar staging slot