# 🚀 Plano de Otimização de Performance - Sistema Fretamento

## 📊 Diagnóstico Atual

### Problemas Identificados:

1. **❌ Activity Middleware Pesado**
   - Registra TODA requisição no banco de dados
   - Cria múltiplos signals que fazem queries
   - Sem limite de registros antigos

2. **❌ Dashboard sem Cache Efetivo**
   - Cache de apenas 5 minutos (300s)
   - Múltiplas consultas complexas
   - Não usa select_related/prefetch_related adequadamente

3. **❌ Falta de Índices no Banco**
   - Nenhum índice customizado nos models
   - Queries lentas em campos frequentemente consultados

4. **❌ Heroku Basic Dyno Limitado**
   - 512MB RAM
   - 4 workers podem estar em excesso
   - Timeout de 60s pode ser curto

5. **❌ Queries N+1 em Templates**
   - Templates acessando relacionamentos sem prefetch
   - ActivityLog carregando 10 registros sem select_related

## 🎯 Plano de Otimização

### FASE 1: Otimizações Rápidas (Impacto Imediato)

#### 1.1 Desabilitar Activity Middleware Pesado
```python
# REMOVER de MIDDLEWARE em settings_heroku.py:
# 'core.activity_middleware.ActivityLogMiddleware'
```

**Ganho:** -30% tempo de resposta

#### 1.2 Aumentar Cache do Dashboard
```python
# Mudar de 5 minutos para 15 minutos
cache.set(cache_key, context, 900)  # 15 minutos
```

**Ganho:** -20% carga no banco

#### 1.3 Reduzir Workers do Gunicorn
```bash
# Procfile: Mudar de 4 para 2 workers
--workers 2
```

**Ganho:** +50% RAM disponível por worker

### FASE 2: Otimização de Queries (Alto Impacto)

#### 2.1 Adicionar Índices nos Models

**Servico:**
```python
class Meta:
    indexes = [
        models.Index(fields=['data_do_servico']),
        models.Index(fields=['tipo']),
        models.Index(fields=['aeroporto']),
        models.Index(fields=['eh_prioritario']),
        models.Index(fields=['-data_do_servico']),  # ordem DESC
    ]
```

**Escala:**
```python
class Meta:
    indexes = [
        models.Index(fields=['data']),
        models.Index(fields=['status']),
        models.Index(fields=['-data']),
    ]
```

**ActivityLog:**
```python
class Meta:
    indexes = [
        models.Index(fields=['-created_at']),
        models.Index(fields=['user', '-created_at']),
    ]
```

**Ganho:** -40% tempo de consultas

#### 2.2 Limitar Atividades Antigas
```python
# Adicionar em cron/management command
ActivityLog.objects.filter(
    created_at__lt=timezone.now() - timedelta(days=90)
).delete()
```

**Ganho:** Banco menor, queries mais rápidas

#### 2.3 Usar select_related/prefetch_related
```python
# ANTES
atividades_recentes = ActivityLog.objects.order_by('-created_at')[:10]

# DEPOIS
atividades_recentes = ActivityLog.objects.select_related('user').order_by('-created_at')[:10]
```

**Ganho:** -50% queries em listagens

### FASE 3: Cache Agressivo (Médio Impacto)

#### 3.1 Configurar Redis no Heroku
```bash
heroku addons:create heroku-redis:mini -a fretamento-intertouring
```

**Custo:** $3/mês  
**Ganho:** Cache distribuído, muito mais rápido

#### 3.2 Aumentar Timeouts de Cache
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 20}
        },
        'TIMEOUT': 900,  # 15 minutos default
    }
}
```

### FASE 4: Otimização Frontend (Baixo Impacto)

#### 4.1 Lazy Loading de Imagens
```html
<img src="..." loading="lazy">
```

#### 4.2 Minificar JS/CSS
- Usar WhiteNoise compressão
- Remover console.logs

#### 4.3 Reduzir Tamanho do DOM
- Limitar listas iniciais (10 itens)
- Adicionar paginação

## 📋 Checklist de Implementação

### Prioridade CRÍTICA (Fazer Agora)
- [ ] Desabilitar ActivityLogMiddleware
- [ ] Aumentar cache dashboard para 15min
- [ ] Reduzir workers Gunicorn de 4 para 2
- [ ] Limitar ActivityLog a últimas 10 atividades

### Prioridade ALTA (Próximas 24h)
- [ ] Adicionar índices em Servico
- [ ] Adicionar índices em Escala
- [ ] Adicionar índices em ActivityLog
- [ ] Fazer migration dos índices
- [ ] Adicionar select_related em queries

### Prioridade MÉDIA (Próxima semana)
- [ ] Instalar Redis no Heroku
- [ ] Configurar django-redis
- [ ] Criar comando para limpar ActivityLog antigos
- [ ] Otimizar templates (lazy loading)

### Prioridade BAIXA (Futuro)
- [ ] Implementar CDN para static files
- [ ] Implementar query caching
- [ ] Monitoramento APM (New Relic/Sentry)

## 📈 Resultados Esperados

| Otimização | Ganho Estimado | Custo |
|------------|----------------|-------|
| Desabilitar Middleware | 30% mais rápido | $0 |
| Reduzir Workers | 50% mais RAM | $0 |
| Adicionar Índices | 40% queries rápidas | $0 |
| Aumentar Cache | 20% menos load | $0 |
| Redis (opcional) | 50% mais rápido | $3/mês |
| **TOTAL SEM REDIS** | **60-70% melhoria** | **$0** |
| **TOTAL COM REDIS** | **80-90% melhoria** | **$3/mês** |

## 🎬 Começar Agora

Execute os comandos abaixo para implementar as otimizações críticas:

```bash
# 1. Desabilitar middleware (editar settings_heroku.py)
# 2. Aumentar cache (editar core/views.py)
# 3. Reduzir workers (editar Procfile)
# 4. Commit e deploy
git add -A
git commit -m "perf: Otimizações críticas de performance"
git push heroku main
```

## ⚠️ Atenção

- **Backup antes**: Sempre faça backup antes de mudanças
- **Teste local**: Teste cada mudança localmente primeiro
- **Monitor**: Use logs do Heroku para monitorar impacto
- **Rollback**: Mantenha commit anterior caso precise voltar

## 📞 Suporte

Se após implementar FASE 1 o sistema ainda estiver lento:
1. Verificar logs: `heroku logs --tail -a fretamento-intertouring`
2. Verificar memória: `heroku ps:scale -a fretamento-intertouring`
3. Considerar upgrade de dyno: Basic → Standard-1X ($25/mês)

---

**Última Atualização:** 20/01/2025  
**Status:** Aguardando implementação
