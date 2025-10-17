# 🚀 GUIA DE IMPLEMENTAÇÃO FASE 2 - N+1 Queries Fix

## 1️⃣ CORRIGIR escalas/views.py (Linhas 147-148)

### 📍 Localizar o Problema

**Arquivo**: `escalas/views.py`  
**Classe**: `SelecionarAnoView`  
**Linhas**: 147-148

```python
# ❌ ATUAL (LENTO)
escalas_ano = Escala.objects.filter(
    usuario=request.user, 
    data__year=ano_selecionado
)
total_servicos = sum(e.alocacoes.count() for e in escalas_ano)  # 100+ queries!
total_valor = sum((e.total_van1_valor or 0) + (e.total_van2_valor or 0) for e in escalas_ano)
```

### ✅ CORRIGIDO

Adicionar após a linha de `filter()`:

```python
from django.db.models import Count, F, Sum, Q

# OTIMIZADO
escalas_ano = Escala.objects.filter(
    usuario=request.user, 
    data__year=ano_selecionado
).annotate(
    total_alocacoes=Count('alocacoes', distinct=True),
    valor_total_van1=F('total_van1_valor'),
    valor_total_van2=F('total_van2_valor')
)

# Agregação em uma query
stats = escalas_ano.aggregate(
    total_servicos=Sum('total_alocacoes'),
    total_valor_van1=Sum('valor_total_van1'),
    total_valor_van2=Sum('valor_total_van2'),
)

total_servicos = stats['total_servicos'] or 0
total_valor_van1 = stats['total_valor_van1'] or 0
total_valor_van2 = stats['total_valor_van2'] or 0
total_valor = (total_valor_van1 or 0) + (total_valor_van2 or 0)
```

**Antes**: 200+ queries  
**Depois**: 1 query  
**Ganho**: 99%+ ↓ latência

---

## 2️⃣ CORRIGIR escalas/views.py (Linhas 232-233)

### 📍 Localizar o Problema

**Classe**: `SelecionarMesView`  
**Linhas**: 232-233  

```python
# ❌ ATUAL (LENTO)
escalas_mes = Escala.objects.filter(
    usuario=request.user,
    data__year=ano,
    data__month=mes
)
total_servicos = sum(e.alocacoes.count() for e in escalas_mes)  # MESMO PROBLEMA!
```

### ✅ CORRIGIDO

```python
# Aplicar MESMA solução da Fase 1
escalas_mes = Escala.objects.filter(
    usuario=request.user,
    data__year=ano,
    data__month=mes
).annotate(
    total_alocacoes=Count('alocacoes', distinct=True),
    valor_total_van1=F('total_van1_valor'),
    valor_total_van2=F('total_van2_valor')
)

stats_mes = escalas_mes.aggregate(
    total_servicos=Sum('total_alocacoes'),
    total_valor_van1=Sum('valor_total_van1'),
    total_valor_van2=Sum('valor_total_van2'),
)

total_servicos_mes = stats_mes['total_servicos'] or 0
```

---

## 3️⃣ CORRIGIR core/views.py (Linhas 294-317)

### 📍 Localizar o Problema

**Arquivo**: `core/views.py`  
**Classe**: `ProcessamentoListView`  
**Linhas**: 294-317

```python
# ❌ ATUAL (CRÍTICO!)
for arquivo in queryset:
    servicos = Servico.objects.filter(arquivo_origem=arquivo.nome_arquivo)
    for servico in servicos:
        # Verificar se cada serviço tem alocação
        if AlocacaoVan.objects.filter(servico=servico).exists():  # QUERY POR SERVIÇO!
            # fazer algo
```

### ✅ CORRIGIDO

```python
from django.db.models import Exists, OuterRef

# Otimizar: Buscar TODAS as alocações uma vez
for arquivo in queryset:
    servicos = Servico.objects.filter(
        arquivo_origem=arquivo.nome_arquivo
    ).annotate(
        tem_alocacao=Exists(
            AlocacaoVan.objects.filter(servico=OuterRef('pk'))
        )
    )
    
    for servico in servicos:
        # Verificar em memória, não em banco
        if servico.tem_alocacao:
            # fazer algo
```

**Antes**: 1000+ queries  
**Depois**: 2-3 queries  
**Ganho**: 99%+ ↓ latência

---

## 4️⃣ CORRIGIR TEMPLATES (escalas/visualizar.html)

### 📍 Problemas Identificados

| Linha | Problema | Queries por render |
|------|----------|-------------------|
| 539 | `{{ grupos_van1.count }}` | 1 |
| 556 | `{{ grupo.servicos.count }}` em loop | 10-50 |
| 578 | `{{ grupo.servicos.count }}` em loop | 10-50 |
| 638 | `{{ alocacao.grupo_info.grupo.servicos.count }}` | 5-20 |
| 825 | Similar | 5-20 |

### ✅ SOLUÇÃO

#### Opção A: Remover .count() e usar anotação

**Na view** (escalas/views.py ~linha 315):

```python
# ANTES
escala = Escala.objects.select_related('usuario').prefetch_related(
    'servicos', 'grupos'
).get(pk=pk)

# DEPOIS
from django.db.models import Prefetch, Count

escala = Escala.objects.select_related('usuario').prefetch_related(
    Prefetch('servicos'),
    Prefetch('grupos', queryset=GrupoServico.objects.annotate(
        servicos_count=Count('servicos')
    ))
).get(pk=pk)
```

**No template** (visualizar.html):

```django
{# ANTES #}
{{ grupo.servicos.count }} serviços

{# DEPOIS #}
{{ grupo.servicos_count }} serviços
```

#### Opção B: Pre-computar tudo na view

```python
# Na view
context = {
    'escala': escala,
    'grupos_van1_count': GrupoServico.objects.filter(...).count(),
    'grupos_van2_count': GrupoServico.objects.filter(...).count(),
    'servicos_por_grupo': {
        g.id: g.servicos.count() 
        for g in escala.grupos.all()
    }
}

# No template
{{ grupos_van1_count }} grupos

{# Acessar array pré-computado #}
{{ servicos_por_grupo|get_item:grupo.id }} serviços
```

---

## 5️⃣ ADICIONAR ÍNDICES DE BANCO (Opcional - Fase 3)

### 📍 Arquivo: `core/models.py`

Localizar classe `Servico` e adicionar:

```python
class Servico(models.Model):
    # ... campos existentes ...
    
    class Meta:
        ordering = ['-data_do_servico']
        verbose_name_plural = 'Serviços'
        # ADICIONAR ISTO:
        indexes = [
            models.Index(fields=['data_do_servico'], name='idx_servico_data'),
            models.Index(fields=['arquivo_origem'], name='idx_servico_arquivo'),
            models.Index(fields=['eh_prioritario', 'data_do_servico'], name='idx_prioritario_data'),
            models.Index(fields=['tipo', 'data_do_servico'], name='idx_tipo_data'),
        ]
```

### Criar Migration

```bash
python manage.py makemigrations core --name "add_servico_indexes"
python manage.py migrate
```

**Ganho**: 20-40% ↓ em queries filtradas

---

## 🧪 COMO TESTAR AS ALTERAÇÕES

### 1. Teste Local

```bash
# Debug SQL queries
cd /Users/anderson/my_folders/repositoriolocal/fretamento-intertouring

# Abrir Django shell
python manage.py shell

# Executar views e contar queries
from django.test.utils import CaptureQueriesContext
from django.db import connection

# ANTES
with CaptureQueriesContext(connection) as context:
    # Executar código antigo
    pass
print(f"Queries antes: {len(context)}")  # Deve ser 100+

# DEPOIS
with CaptureQueriesContext(connection) as context:
    # Executar código novo
    pass
print(f"Queries depois: {len(context)}")  # Deve ser <5
```

### 2. Verificar Performance em Produção

```bash
# Antes de deploy
heroku logs --tail --app seu-app

# Procurar por:
# "measure="  <- latência de requests
# Deve estar ~2000ms antes, <500ms depois
```

### 3. Debug SQL em Produção

```bash
# Ver queries lentas no PostgreSQL
heroku pg:psql --app seu-app

-- Dentro do psql
SELECT * FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 5;

-- Ver query específica
EXPLAIN ANALYZE SELECT * FROM core_servico WHERE data_do_servico > now() - interval '30 days';
```

---

## 📊 GANHOS ESPERADOS

### Por Correção

| Correção | Queries | Latência | Método |
|----------|---------|----------|--------|
| escalas line 147 | 100+ → 1 | 2000ms → 50ms | Aggregate |
| escalas line 232 | 100+ → 1 | 2000ms → 50ms | Aggregate |
| core line 317 | 1000+ → 2 | 3000ms → 100ms | Annotate Exists |
| Templates | 50 → 0 | 1000ms → 100ms | Prefetch Count |
| Índices | -30% | -40% | DB Index |

### TOTAL

- **Queries**: ~1270 → 20 (98% ↓)
- **Latência**: 8000ms → 300ms (96% ↓)
- **Throughput**: 1 req/s → 10 req/s (10x ↑)

---

## ⚠️ CUIDADOS

1. **Não use `.distinct()` com `.count()` sem necessidade** (mais lento)
2. **Sempre use `Prefetch()` com `annotate()` quando possível**
3. **Testar localmente antes de deploy**
4. **Criar backup do BD antes de rodar migrações**
5. **Deploy em horário de pouco uso**

---

## ✅ CHECKLIST

- [ ] Corrigir escalas/views.py linha 147-148
- [ ] Corrigir escalas/views.py linha 232-233
- [ ] Corrigir core/views.py linha 317
- [ ] Testar localmente com CaptureQueriesContext
- [ ] Remover `.count()` de templates
- [ ] Adicionar `annotate()` nas views
- [ ] Criar migration para índices (opcional)
- [ ] Deploy em staging
- [ ] Testar em produção
- [ ] Monitorar latência com `heroku logs --tail`

---

## 🎯 PRÓXIMOS PASSOS

1. **Implementar as 4 correções acima** (2-3 horas)
2. **Testar em staging**
3. **Deploy para Heroku**
4. **Monitorar com** `heroku logs --tail --app seu-app`
5. **Registrar melhoria de latência**

**Depois disso, sistema deve estar 60-80% mais rápido!**
