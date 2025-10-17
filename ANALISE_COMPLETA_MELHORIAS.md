# 📋 ANÁLISE COMPLETA - Próximas Melhorias de Performance

## 🔍 Análise do Codebase (Verificação Completa)

### ✅ O QUE JÁ ESTÁ BOM

1. **Cache implementado no HomeView**
   - ✅ Cache por usuário e data
   - ✅ TTL de 5 minutos
   - ✅ Fallback funcional

2. **Agregação otimizada**
   - ✅ Use de `.aggregate()` em vez de `.count()` separado
   - ✅ Filtros Q() para múltiplas condições
   - ✅ Batch de queries reduzido

3. **Select_related/Prefetch já implementado**
   - ✅ Linha 315-317 em escalas/views.py
   - ✅ Reduz N+1 queries

---

## ⚠️ PROBLEMAS IDENTIFICADOS

### 1. **N+1 QUERIES CRÍTICO** (escalas/views.py linha 147-148)

```python
# ❌ PROBLEMA CRÍTICO - PIOR GARGALO!
total_servicos = sum(e.alocacoes.count() for e in escalas_ano)
total_valor = sum((e.total_van1_valor or 0) + (e.total_van2_valor or 0) for e in escalas_ano)
```

**Impacto**: Para 100 escalas = 100+ queries extras!

**Solução**:
```python
# ✅ CORRIGIR
escalas_ano.annotate(
    total_servicos=Count('alocacoes'),
    valor_total=F('total_van1_valor') + F('total_van2_valor')
).aggregate(
    total_servicos_sum=Sum('total_servicos'),
    valor_total_sum=Sum('valor_total')
)
```

**Ganho**: 100+ queries → 1 query

---

### 2. **N+1 QUERIES NO PROCESSAMENTO DE ARQUIVOS** (core/views.py linha 294-317)

```python
# ❌ PROBLEMA - Loop com queries dentro
for arquivo in queryset:
    # ...
    for servico in servicos:
        if AlocacaoVan.objects.filter(servico=servico).exists():  # QUERY POR SERVICO!
```

**Impacto**: 1000 serviços = 1000 queries extras!

**Solução**:
```python
# ✅ CORRIGIR
# Batch fetch todas as alocações de uma vez
alocacoes_ids = set(AlocacaoVan.objects.filter(
    servico__in=servicos
).values_list('servico_id', flat=True))

for servico in servicos:
    if servico.id in alocacoes_ids:  # Verificação em memória
```

**Ganho**: 1000 queries → 1 query

---

### 3. **TEMPLATE CALLS N+1** (escalas/visualizar.html)

```django
{# ❌ PROBLEMA - Count() em cada iteração #}
{% for grupo in grupos_van1 %}
    {{ grupo.servicos.count }} serviços  <!-- QUERY POR GRUPO! -->
{% endfor %}
```

**Impacto**: 10 grupos = 10 queries extras!

**Solução**:
```python
# ✅ Na view, usar Prefetch com Count
from django.db.models import Prefetch, Count

grupos = GrupoServico.objects.annotate(
    servicos_count=Count('servicos')
)
```

```django
{# No template #}
{{ grupo.servicos_count }} serviços
```

**Ganho**: 10 queries → 0 queries

---

### 4. **MÚLTIPLAS QUERIES NOS LOOPS** (escalas/views.py linha 508-514)

```python
# ❌ PROBLEMA - Filter em cada linha
total_alocados = escala.alocacoes.filter(status_alocacao='ALOCADO').count()  # Q1
total_nao_alocados = escala.alocacoes.filter(status_alocacao='NAO_ALOCADO').count()  # Q2
# ...
van1_servicos = escala.alocacoes.filter(..., van='VAN1').count()  # Q3+
```

**Solução**:
```python
# ✅ CORRIGIR - Aggregate tudo em uma query
stats = escala.alocacoes.aggregate(
    total_alocados=Count('id', filter=Q(status_alocacao='ALOCADO')),
    total_nao_alocados=Count('id', filter=Q(status_alocacao='NAO_ALOCADO')),
    van1_alocados=Count('id', filter=Q(van='VAN1', status_alocacao='ALOCADO')),
    van2_alocados=Count('id', filter=Q(van='VAN2', status_alocacao='ALOCADO')),
)
```

**Ganho**: 4-8 queries → 1 query

---

### 5. **FALTA DE ÍNDICES NA TEMPLATE** (escalas/visualizar.html linha 539, 556, 578)

```django
{# ❌ PROBLEMA - Count em template #}
{{ grupos_van1.count }}  <!-- Executa COUNT(*) #}
{{ grupo.servicos.count }}  <!-- Executa COUNT(*) #}
```

**Solução**: Pre-computar na view com `.count()` ou `.annotate()`

---

## 📊 QUANTIFICAÇÃO DO PROBLEMA

| Problema | Queries Atuais | Queries Otimizado | Ganho |
|----------|----------------|-------------------|-------|
| Loop de escalas (147-148) | 200+ | 1 | 99% ↓ |
| Processamento de arquivos | 1000+ | 1 | 99.9% ↓ |
| Contadores em template | 50+ | 0 | 100% ↓ |
| Stats de alocações | 20+ | 1 | 95% ↓ |
| TOTAL ESTIMADO | 1270+ | 10-15 | 98% ↓ |

---

## 🗄️ ANÁLISE DO BANCO DE DADOS (Heroku)

### Status Atual
- **Plano**: PostgreSQL Essential 0
- **Storage**: 1GB
- **Conexões**: 20 máximo
- **Performance**: Limitada

### ✅ Verificações Recomendadas no Heroku

```bash
# 1. Verificar tamanho do BD
heroku pg:info --app seu-app

# 2. Ver índices existentes
heroku pg:psql --app seu-app
\d core_servico         # Ver tabela
\d+ core_servico        # Ver índices
\d escalas_escala       # Verificar tabela de escalas

# 3. Ver plano de execução (EXPLAIN)
EXPLAIN SELECT * FROM core_servico WHERE data_do_servico > '2025-10-01';

# 4. Ver queries lentas
SELECT query, mean_time, calls, max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

# 5. Ver tamanho de tabelas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### ⚠️ Possíveis Limitações

1. **Conexões limitadas a 20**
   - Com 3 workers Gunicorn = ~5 conexões cada
   - Sob carga pode ficar sem conexão disponível

2. **1GB de storage**
   - Verificar crescimento mensal
   - Se >100MB/mês = problema em 10 meses

3. **CPU/RAM limitado**
   - Plano gratuito = recursos compartilhados
   - Picos de uso afetam performance

### 💡 Recomendações Heroku

```bash
# UPGRADE RECOMENDADO (opcional):
heroku addons:upgrade heroku-postgresql:standard-0 --app seu-app
# Custo: ~$50/mês
# Ganho: 64GB storage, 120 conexões, read replicas

# OU se quer manter atual:
# - Limpar dados antigos regularmente
# - Implementar soft deletes
# - Arquivar dados para S3
```

---

## 🔧 SERVIDOR (Dyno) - Análise

### Status Atual (com otimizações implementadas)

```
web: gunicorn ... --workers 3
```

### ✅ Análise da Configuração

```bash
# Calcular workers ideais para dyno
Workers = (2 × CPU cores) + 1
# Para dyno padrão (~1 CPU): (2 × 1) + 1 = 3 ✅ CORRETO

# Verificar latência por worker
heroku logs --tail --app seu-app | grep "measure="
# Deve estar < 100ms

# Ver uso de memória
heroku ps --app seu-app
# Se > 90% = problema, considerar dyno maior
```

### ⚠️ Possíveis Limitações

1. **Dyno padrão (512MB)**
   - 3 workers = ~170MB por worker
   - Sem margem para spikes
   - Pode fazer swap = muito lento

2. **Timeout de 30s**
   - Algumas views podem exceder
   - Especialmente processamento de arquivos

### 💡 Recomendações

```bash
# UPGRADE SE NECESSÁRIO:
heroku ps:type web=standard-1x --app seu-app
# Custo: +$50/mês
# RAM: 512MB → 1024MB
# CPU: 1x → mais capacidade

# OU ADICIONAR WORKER DYNO:
heroku ps:scale web=2 --app seu-app
# Custo: +$7/mês
# Instância extra para distribuir carga
```

---

## 🎯 PLANO DE AÇÃO (Próximas Melhorias)

### FASE 2: Otimizar Queries (2-3 horas)

**Priority: 🔴 CRÍTICA**

#### 2.1 Corrigir N+1 em escalas/views.py

```python
# Linha 147-148 - CORRIGIR IMEDIATAMENTE
# Antes: 200+ queries
# Depois: 1 query
```

#### 2.2 Corrigir N+1 em core/views.py

```python
# Linha 317 - CORRIGIR IMEDIATAMENTE
# Antes: 1000+ queries
# Depois: 1 query
```

#### 2.3 Adicionar Anotações em Views

```python
# Pre-compute counts na view
# Remover .count() do template
```

---

### FASE 3: Adicionar Índices (30 min)

```python
# core/models.py
class Meta:
    indexes = [
        models.Index(fields=['data_do_servico']),
        models.Index(fields=['arquivo_origem']),
        models.Index(fields=['eh_prioritario', 'data_do_servico']),
    ]

# escalas/models.py
class Meta:
    indexes = [
        models.Index(fields=['data']),
        models.Index(fields=['status', 'data']),
    ]
```

---

### FASE 4: Otimizar Heroku (30 min)

```bash
# 1. Limpar dados antigos
DELETE FROM core_servico WHERE data_do_servico < '2024-01-01';
VACUUM ANALYZE;

# 2. Analisar tabelas (update statistics)
ANALYZE;

# 3. Reindex (se necessário)
REINDEX DATABASE fretamento_db;

# 4. Ver resultado
SELECT pg_size_pretty(pg_database_size('fretamento_db'));
```

---

## 📈 ESTIMATIVA DE GANHO TOTAL

| Item | Ganho |
|------|-------|
| N+1 Queries (Fase 2) | 60-80% ↑ |
| Índices (Fase 3) | 20-40% ↑ |
| Limpeza BD (Fase 4) | 10-20% ↑ |
| **TOTAL** | **60-90% ↑** |

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

### Imediato (Esta semana)
- [ ] Corrigir N+1 em escalas/views.py (linha 147-148)
- [ ] Corrigir N+1 em core/views.py (linha 317)
- [ ] Adicionar anotações nas templates
- [ ] Deploy e testar

### Próxima semana
- [ ] Adicionar índices de BD
- [ ] Criar migration e deploy
- [ ] Limpeza de dados antigos

### Próximo mês
- [ ] Considerar upgrade de dyno/BD
- [ ] Implementar monitoramento com Sentry
- [ ] Setup de alertas de performance

---

## 🚀 COMO COMEÇAR

**Recomendação**: Começar pela **FASE 2** - vai trazer ganhos MASSIVOS com mínimo esforço!

```python
# Exemplo de correção simples:

# ❌ ANTES (lento)
for escala in escalas:
    total = escala.alocacoes.count()  # QUERY POR ESCALA!

# ✅ DEPOIS (rápido)
escalas = escalas.annotate(
    total_alocacoes=Count('alocacoes')
)
for escala in escalas:
    total = escala.total_alocacoes  # Sem query!
```

---

**Resultado esperado**: 60-90% de melhoria ADCIONAL às otimizações já implementadas!
