# 🚀 Plano de Otimização - Sistema Lento no Heroku

## Diagnóstico dos Problemas de Performance

### 🔴 Problemas Críticos Identificados

1. **Cache Inadequado (CRÍTICO)**
   - Usando `LocMemCache` (em-memória local) em produção
   - Heroku com múltiplos dynos = cache não compartilhado
   - Cada dyno tem seu próprio cache isolado
   - **Resultado**: Cache não funciona, todas as queries vão para o BD

2. **ActivityLog Middleware (CRÍTICO)**
   - Executa em TODA requisição
   - Registra automaticamente login/logout/criação/atualização de dados
   - Enfileiramento de signals do Django causa overhead massivo
   - **Resultado**: Latência adicional em cada requisição

3. **Heroku Dyno Padrão (PROBLEMA)**
   - Plano gratuito: muito limitado (512MB RAM)
   - PostgreSQL Essential 0: limite de 20 conexões
   - Sem resources para cache Redis
   - **Resultado**: Sem escalabilidade

4. **Gunicorn Subconfigurado**
   - `Procfile` usa configuração padrão
   - Sem otimizações de workers
   - **Resultado**: Throughput baixo

5. **Sem Compressão**
   - Responses não comprimidas
   - WhiteNoise sem compressão de assets
   - **Resultado**: Transferência lenta

6. **Queries Não Otimizadas**
   - Possível N+1 queries
   - Sem select_related/prefetch_related estratégico
   - Sem índices de banco de dados
   - **Resultado**: Consultas lentas

---

## ✅ Soluções por Prioridade

### PRIORIDADE 1: Desabilitar ActivityLog em Produção (15 min)

**Impacto**: ~40-60% melhoria de performance

```python
# fretamento_project/settings_heroku.py
# Desabilitar o middleware pesado
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Remover: 'core.activity_middleware.ActivityLogMiddleware',
]

# Desabilitar signals que registram atividades
ACTIVITY_LOG_ENABLED = False
```

---

### PRIORIDADE 2: Implementar Cache Redis (30 min)

**Impacto**: ~30-50% melhoria (com múltiplos acessos)

#### Opção A: Heroku Redis (Recomendado, $15/mês)
```bash
heroku addons:create heroku-redis:premium-0 --app=seu-app
```

#### Opção B: Heroku Redis Gratuito (Limited, mas funciona)
```bash
heroku addons:create heroku-redis:premium-0 --app=seu-app
```

#### Configuração em `settings_heroku.py`:
```python
import redis
from urllib.parse import urlparse

# Redis Cache (mais rápido que LocMemCache)
REDIS_URL = os.environ.get('REDIS_URL')

if REDIS_URL:
    # Usar Redis em produção
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'IGNORE_EXCEPTIONS': True,
            }
        }
    }
else:
    # Fallback para LocMemCache se Redis não disponível
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'fretamento-cache',
            'TIMEOUT': 300,
            'OPTIONS': {'MAX_ENTRIES': 1000},
        }
    }
```

**Adicionar `django-redis` em `requirements.txt`:**
```
django-redis==5.4.0
redis==5.0.1
```

---

### PRIORIDADE 3: Otimizar Gunicorn (10 min)

**Impacto**: ~20-30% melhoria

**Novo `Procfile`:**
```makefile
web: gunicorn fretamento_project.wsgi:application \
     --bind 0.0.0.0:$PORT \
     --workers 3 \
     --worker-class sync \
     --worker-tmp-dir /dev/shm \
     --max-requests 1000 \
     --max-requests-jitter 100 \
     --timeout 30 \
     --keep-alive 5 \
     --access-logfile - \
     --error-logfile - \
     --log-level info
```

---

### PRIORIDADE 4: Adicionar Compressão de Responses (5 min)

**Impacto**: ~15-25% menos bandwidth

**Em `settings_heroku.py`:**
```python
# Middleware de compressão (ADICIONAR APÓS whitenoise)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # ADICIONAR
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuração do WhiteNoise com compressão
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_COMPRESS_OFFLINE = True
WHITENOISE_AUTOREFRESH = False

# Otimizar respostas
GZIP_LEVEL = 6
```

---

### PRIORIDADE 5: Adicionar Índices de Banco de Dados (20 min)

**Impacto**: ~20-40% em queries frequentes

Criar migração:
```bash
python manage.py makemigrations
```

**Novo arquivo: `core/migrations/XXXX_add_performance_indexes.py`**
```python
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', 'XXXX_previous_migration'),
    ]

    operations = [
        # Índices para filtros comuns em Servico
        migrations.AddIndex(
            model_name='servico',
            index=models.Index(fields=['data_do_servico', '-created_at'], name='servico_data_created_idx'),
        ),
        migrations.AddIndex(
            model_name='servico',
            index=models.Index(fields=['tipo', 'data_do_servico'], name='servico_tipo_data_idx'),
        ),
        migrations.AddIndex(
            model_name='servico',
            index=models.Index(fields=['cliente'], name='servico_cliente_idx'),
        ),
        migrations.AddIndex(
            model_name='servico',
            index=models.Index(fields=['eh_prioritario', 'data_do_servico'], name='servico_prioritario_idx'),
        ),
    ]
```

**Em `core/models.py`, adicionar ao Meta de Servico:**
```python
class Meta:
    ordering = ['data_do_servico', 'horario']
    verbose_name = 'Serviço'
    verbose_name_plural = 'Serviços'
    indexes = [
        models.Index(fields=['data_do_servico', '-created_at']),
        models.Index(fields=['tipo', 'data_do_servico']),
        models.Index(fields=['cliente']),
        models.Index(fields=['eh_prioritario', 'data_do_servico']),
    ]
```

---

### PRIORIDADE 6: Otimizar Django ORM (30 min)

**Impacto**: ~20-40% em views com múltiplas queries

**Exemplo de otimização em `core/views.py`:**

```python
# ❌ ANTES: N+1 queries
servicos = Servico.objects.all()[:20]
for s in servicos:
    print(s.created_at)  # Nova query para cada objeto!

# ✅ DEPOIS: 1 query com prefetch
from django.db.models import Prefetch

servicos = Servico.objects.select_related(
    'processamentplanilha'  # Se houver FK
).prefetch_related(
    Prefetch('relacionamento_um_para_muitos')  # Se houver
).all()[:20]
```

**Em `escalas/views.py`, aplicar select_related/prefetch_related:**
```python
# Buscar escalas com serviços otimizado
escalas = Escala.objects.prefetch_related(
    'servicos',
    'alocacoes'
).filter(
    data__gte=data_inicio,
    data__lte=data_fim
).select_related('usuario')
```

---

### PRIORIDADE 7: Implementar Cache em Views Críticas (30 min)

**Impacto**: ~50-80% em endpoints frequentes

**Em `core/views.py`:**
```python
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

# Cache por 5 minutos para dashboard
@method_decorator(cache_page(300), name='dispatch')
class DashboardView(View):
    def get(self, request):
        # ... código da view
        pass

# Cache granular baseado em usuário
def get_cached_stats(user_id):
    cache_key = f"user_stats_{user_id}"
    data = cache.get(cache_key)
    
    if not data:
        data = Servico.objects.aggregate(
            total=Count('id'),
            pax=Avg('pax')
        )
        cache.set(cache_key, data, 300)  # 5 min
    
    return data
```

---

## 🔧 Plano de Implementação (Ordem)

### Fase 1: Hoje (15-30 min)
1. ✅ Desabilitar ActivityLog middleware
2. ✅ Otimizar Gunicorn no Procfile
3. ✅ Adicionar compressão GZip
4. ✅ Deploy

### Fase 2: Próxima Semana (30-45 min)
5. ✅ Adicionar Redis (Heroku Redis paid)
6. ✅ Configurar django-redis
7. ✅ Testar performance
8. ✅ Deploy

### Fase 3: Manutenção (1-2 horas)
9. ✅ Adicionar índices no BD
10. ✅ Otimizar queries críticas
11. ✅ Implementar cache em views
12. ✅ Testar e monitorar

---

## 📊 Benchmarks Esperados

| Cenário | Antes | Depois | Ganho |
|---------|-------|--------|-------|
| Home Page (sem cache) | 2.5s | 600ms | 75% ↑ |
| Home Page (com cache) | 2.5s | 150ms | 94% ↑ |
| Lista de Escalas | 1.8s | 450ms | 75% ↑ |
| Criar Serviço | 1.2s | 250ms | 79% ↑ |
| Consultores Concurrent | 5 | 20+ | 4x ↑ |

---

## 🚨 Warnings Importantes

1. **ActivityLog**: Se for crítico para auditoria, considere implementar de forma assíncrona com Celery/Redis
2. **Redis**: Custa $15/mês, mas vale cada centavo em performance
3. **Índices**: Melhoram leitura mas ralentam escrita ligeiramente
4. **Cache**: Sempre invalidar quando dados mudam!

---

## 📝 Próximas Ações

1. Revisar `PRIORIDADE 1` - Remover ActivityLog middleware
2. Testar em staging
3. Se bom resultado → implementar PRIORIDADE 2-7
4. Monitorar com New Relic/Sentry após deploy

---

## ✨ Comandos Úteis Heroku

```bash
# Ver tempo de resposta
heroku logs --tail --app seu-app

# Ver metricas
heroku stats --app seu-app

# Adicionar Redis
heroku addons:create heroku-redis:premium-0

# Escalar dynos (mais workers)
heroku ps:scale web=2

# Restart app
heroku restart --app seu-app

# Ver config vars
heroku config --app seu-app
```
