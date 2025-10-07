# Deploy na Vercel - Guia Completo

Este guia te mostra como fazer deploy do Fretamento Intertouring na Vercel usando SQLite.

## 🌟 Por que Vercel + SQLite?

- ✅ **Deploy Gratuito**: Tier gratuito generoso da Vercel
- ✅ **SQLite Compatível**: Banco de dados simples, sem configuração externa
- ✅ **Deploy Automático**: Push no GitHub = deploy automático
- ✅ **HTTPS Grátis**: SSL automático para domínios .vercel.app
- ✅ **CDN Global**: Performance otimizada mundialmente

## 🚀 Deploy Passo-a-Passo

### 1. Preparar o Projeto

```bash
# Instalar Vercel CLI (opcional)
npm i -g vercel

# Ou usar a interface web (recomendado para iniciantes)
```

### 2. Configurar Variáveis de Ambiente

Na dashboard da Vercel, configure estas variáveis:

```bash
# Obrigatórias
DJANGO_SECRET_KEY=sua-chave-super-secreta-aqui
DJANGO_SETTINGS_MODULE=fretamento_project.settings_vercel

# Para criar superusuário automaticamente (opcional)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@intertouring.com
DJANGO_SUPERUSER_PASSWORD=sua-senha-segura
```

### 3. Deploy via GitHub (Recomendado)

1. **Push para GitHub**:
   ```bash
   git add .
   git commit -m "feat: configurar deploy Vercel"
   git push origin main
   ```

2. **Conectar à Vercel**:
   - Acesse [vercel.com](https://vercel.com)
   - Faça login com GitHub
   - Clique "New Project"
   - Selecione seu repositório
   - Configure as variáveis de ambiente
   - Deploy!

### 4. Deploy via CLI (Alternativo)

```bash
# Login na Vercel
vercel login

# Deploy
vercel --prod

# Configurar domínio customizado (opcional)
vercel domains add fretamento.meudominio.com
```

## ⚙️ Configurações da Vercel

### vercel.json Explicado

```json
{
  "version": 2,
  "builds": [
    {
      "src": "fretamento_project/wsgi.py",  // Arquivo WSGI principal
      "use": "@vercel/python",              // Runtime Python
      "config": {
        "maxLambdaSize": "15mb"             // Limite de tamanho
      }
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",               // Arquivos estáticos
      "dest": "/static/$1"
    },
    {
      "src": "/(.*)",                      // Todas as outras rotas
      "dest": "fretamento_project/wsgi.py"
    }
  ]
}
```

### Limitações do SQLite na Vercel

⚠️ **Importante**: Na Vercel, SQLite é temporário e recriado a cada deploy:

- ✅ **Funciona para**: Demonstrações, protótipos, desenvolvimento
- ❌ **Não funciona para**: Dados permanentes, produção real

## 💾 Soluções para Persistência de Dados

### Opção 1: Dados Iniciais com Fixtures

```bash
# Criar fixtures com dados de exemplo
python manage.py dumpdata core.Servico --indent 2 > fixtures/servicos_exemplo.json

# Carregar automaticamente no build
python manage.py loaddata fixtures/servicos_exemplo.json
```

### Opção 2: Migrar para PostgreSQL (Recomendado para Produção)

```bash
# Usar Railway, Supabase ou PlanetScale
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

### Opção 3: Banco de Dados como Serviço

#### Railway (Recomendado)
```bash
# 1. Criar conta em railway.app
# 2. Adicionar PostgreSQL
# 3. Configurar variáveis na Vercel:
DATABASE_URL=postgresql://user:pass@host:port/db
```

#### Supabase (Gratuito)
```bash
# 1. Criar projeto em supabase.com
# 2. Copiar connection string
# 3. Adicionar na Vercel:
DATABASE_URL=postgresql://...
```

## 🛠️ Comandos Úteis

### Deploy e Build

```bash
# Build local para testar
python manage.py collectstatic --noinput --settings=fretamento_project.settings_vercel

# Testar configurações
python manage.py check --deploy --settings=fretamento_project.settings_vercel

# Redeploy na Vercel
vercel --prod --force
```

### Logs e Debug

```bash
# Ver logs da Vercel
vercel logs

# Debug local
python manage.py runserver --settings=fretamento_project.settings_vercel
```

## 🔧 Otimizações para Vercel

### 1. Static Files com WhiteNoise

```python
# settings_vercel.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Servir estáticos
    # ... outros middlewares
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 2. Cache de Templates

```python
# Otimização para cold starts
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]
```

### 3. Desabilitar Debug Toolbar

```python
# Não incluir django-debug-toolbar em produção
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ... apps principais
    # Não incluir 'debug_toolbar' na Vercel
]
```

## 📈 Monitoramento na Vercel

### Analytics Integrado

```javascript
// A Vercel fornece analytics automático:
// - Page views
// - Performance metrics
// - Error tracking
// - Geographic distribution
```

### Custom Health Check

```python
# views.py
def vercel_health(request):
    return JsonResponse({
        'status': 'healthy',
        'platform': 'vercel',
        'timestamp': timezone.now().isoformat()
    })
```

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Build Timeout
```bash
# Reduzir dependências no requirements-vercel.txt
# Usar apenas pacotes essenciais
```

#### 2. Lambda Size Limit
```bash
# Aumentar no vercel.json:
"config": {
  "maxLambdaSize": "50mb"
}
```

#### 3. Static Files 404
```bash
# Verificar STATIC_ROOT e collectstatic
python manage.py collectstatic --noinput
```

#### 4. Database Reset
```bash
# Normal na Vercel - usar fixtures para dados iniciais
python manage.py loaddata fixtures/initial_data.json
```

## 🎯 Exemplo de Deploy Completo

```bash
# 1. Configurar projeto
cp requirements.txt requirements-vercel.txt  # Editar conforme necessário

# 2. Testar localmente
python manage.py runserver --settings=fretamento_project.settings_vercel

# 3. Commit e push
git add .
git commit -m "feat: configurar Vercel deploy"
git push origin main

# 4. Configurar na Vercel
# - Conectar repositório
# - Adicionar variáveis de ambiente
# - Deploy automático

# 5. Verificar deploy
curl https://seu-projeto.vercel.app/health/
```

## 📊 Custos e Limites

### Tier Gratuito Vercel

- ✅ **Bandwidth**: 100GB/mês
- ✅ **Builds**: 6.000 minutos/mês
- ✅ **Functions**: 12 execuções/hora por função
- ✅ **Domains**: Subdomínio .vercel.app gratuito
- ✅ **SSL**: Certificado automático

### Upgrade para Pro (se necessário)

- 💰 **$20/mês** para uso comercial
- 📈 **Limites aumentados** significativamente
- 🔧 **Recursos avançados** (analytics, edge functions)

---

## ✅ Checklist de Deploy

- [ ] Configurar `settings_vercel.py`
- [ ] Criar `vercel.json`
- [ ] Configurar `requirements-vercel.txt`
- [ ] Atualizar `wsgi.py`
- [ ] Configurar variáveis de ambiente na Vercel
- [ ] Testar build localmente
- [ ] Push para GitHub
- [ ] Conectar repositório na Vercel
- [ ] Verificar deploy funcionando
- [ ] Configurar domínio customizado (opcional)

**🚀 Seu projeto estará online em minutos na Vercel!**