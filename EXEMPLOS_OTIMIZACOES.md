# 💻 Exemplos de Código - Otimizações Futuras

## 📌 Fase 2: Próximas Implementações

Estes são exemplos de código para implementar nas próximas sprints para melhorar ainda mais a performance.

---

## 1. Adicionar Índices de Banco de Dados

### Arquivo: `core/models.py`

```python
class Servico(models.Model):
    """Model para representar um serviço de fretamento"""
    
    # ... campos do modelo ...
    
    class Meta:
        ordering = ['data_do_servico', 'horario']
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'
        # ✅ ADICIONAR ESTES ÍNDICES
        indexes = [
            # Índice composto para filtrar por data e ordenar
            models.Index(
                fields=['data_do_servico', '-created_at'],
                name='servico_data_created_idx'
            ),
            # Índice para filtro de tipo e data
            models.Index(
                fields=['tipo', 'data_do_servico'],
                name='servico_tipo_data_idx'
            ),
            # Índice para busca por cliente
            models.Index(
                fields=['cliente'],
                name='servico_cliente_idx'
            ),
            # Índice para filtro de prioritários
            models.Index(
                fields=['eh_prioritario', 'data_do_servico'],
                name='servico_prioritario_idx'
            ),
        ]
```

### Criar e Aplicar Migração

```bash
# 1. Gerar a migração
python manage.py makemigrations

# 2. Aplicar localmente para testar
python manage.py migrate

# 3. Fazer push
git add migrations/
git commit -m "Add database indexes for Servico model"
git push heroku main

# 4. Heroku irá aplicar automaticamente
heroku logs --tail --app seu-app
```

---

## 2. Otimizar Queries com select_related e prefetch_related

### Arquivo: `escalas/views.py`

```python
from django.db.models import Prefetch

class EscalaDetailView(DetailView):
    """Exemplo de view otimizada com prefetch_related"""
    
    model = Escala
    template_name = 'escalas/visualizar.html'
    
    def get_queryset(self):
        # ❌ ANTES: N+1 queries
        # return Escala.objects.all()
        
        # ✅ DEPOIS: Otimizado com prefetch
        return Escala.objects.prefetch_related(
            # Prefetch servicos relacionados
            Prefetch(
                'servicos',
                queryset=Servico.objects.select_related(
                    'processamentplanilha'  # Se houver FK
                ).filter(data_do_servico__isnull=False)
            ),
            # Prefetch alocações de van
            'alocacoes',
            # Prefetch grupos de serviços
            'grupos'
        ).select_related(
            # Select relacionamentos Um-para-Um
            'usuario'
        )


class ListaEscalasView(ListView):
    """Exemplo de list view otimizada com agregação"""
    
    model = Escala
    template_name = 'escalas/lista.html'
    paginate_by = 20
    
    def get_queryset(self):
        # ✅ Otimizar com select_related e filtro
        from datetime import date, timedelta
        from django.db.models import Count, Q
        
        data_inicio = date.today()
        data_fim = data_inicio + timedelta(days=30)
        
        return Escala.objects.filter(
            data__range=[data_inicio, data_fim]
        ).select_related(
            'usuario'  # Evitar N+1 queries de usuário
        ).prefetch_related(
            'servicos'  # Prefetch de muitos-para-muitos
        ).annotate(
            total_servicos=Count('servicos', distinct=True)
        ).order_by('-data')
```

---

## 3. Implementar Cache em Views Críticas

### Arquivo: `core/views.py`

```python
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.views.generic import View

# Opção 1: Cache simples em toda a view (5 minutos)
@method_decorator(cache_page(300), name='dispatch')
class DashboardSimpleView(View):
    """Dashboard cacheado por 5 minutos"""
    
    def get(self, request):
        # Toda a view será cacheada
        servicos = Servico.objects.count()
        escalas = Escala.objects.count()
        
        context = {
            'total_servicos': servicos,
            'total_escalas': escalas,
        }
        
        return render(request, 'core/dashboard.html', context)


# Opção 2: Cache granular com manejo customizado
class DashboardOtimizadaView(View):
    """Dashboard com cache inteligente por usuário"""
    
    def get(self, request):
        # Cache key baseado no usuário
        cache_key = f"dashboard_{request.user.id}_{date.today()}"
        
        # Tentar obter do cache
        cached_context = cache.get(cache_key)
        if cached_context:
            # Cache hit! Retornar resultado cached
            return render(request, 'core/dashboard.html', cached_context)
        
        # Cache miss - gerar dados
        stats_servicos = self._get_servicos_stats()
        stats_escalas = self._get_escalas_stats()
        top_clientes = self._get_top_clientes()
        
        context = {
            **stats_servicos,
            **stats_escalas,
            'top_clientes': top_clientes,
        }
        
        # Guardar no cache por 5 minutos
        cache.set(cache_key, context, 300)
        
        return render(request, 'core/dashboard.html', context)
    
    def _get_servicos_stats(self):
        """Obtém estatísticas de serviços com cache"""
        cache_key = f"servicos_stats_{date.today()}"
        
        stats = cache.get(cache_key)
        if stats:
            return stats
        
        stats = Servico.objects.aggregate(
            total=Count('id'),
            pax_medio=Avg('pax'),
            prioritarios=Count('id', filter=Q(eh_prioritario=True))
        )
        
        cache.set(cache_key, stats, 300)
        return stats
    
    def _get_escalas_stats(self):
        """Obtém estatísticas de escalas com cache"""
        cache_key = f"escalas_stats_{date.today()}"
        
        stats = cache.get(cache_key)
        if stats:
            return stats
        
        stats = Escala.objects.aggregate(
            total=Count('id'),
            aprovadas=Count('id', filter=Q(status='APROVADA')),
            pendentes=Count('id', filter=Q(status='PENDENTE'))
        )
        
        cache.set(cache_key, stats, 300)
        return stats
    
    def _get_top_clientes(self, limit=10):
        """Top 10 clientes com cache"""
        cache_key = f"top_clientes_{date.today()}"
        
        top = cache.get(cache_key)
        if top:
            return top
        
        top = Servico.objects.values('cliente').annotate(
            total=Count('id')
        ).order_by('-total')[:limit]
        
        cache.set(cache_key, top, 600)  # 10 min
        return top


# Opção 3: Cache com invalidação automática
class ServicoListView(ListView):
    """Lista de serviços com cache smart"""
    
    model = Servico
    paginate_by = 20
    
    def get_queryset(self):
        # Cache key baseado em filtros
        cache_key = self._get_cache_key()
        
        # Tentar cache
        queryset = cache.get(cache_key)
        if queryset is not None:
            return queryset
        
        # Gerar queryset otimizado
        queryset = Servico.objects.filter(
            data_do_servico__gte=date.today()
        ).select_related(
            'processamentplanilha'
        ).order_by(
            'data_do_servico', 'horario'
        )
        
        # Guardar em cache
        cache.set(cache_key, queryset, 300)
        
        return queryset
    
    def _get_cache_key(self):
        """Gerar cache key baseado em filtros"""
        tipo = self.request.GET.get('tipo', '')
        cliente = self.request.GET.get('cliente', '')
        data = self.request.GET.get('data', '')
        
        return f"servicos_list_{tipo}_{cliente}_{data}"
```

---

## 4. Invalidar Cache Após Mudanças

### Arquivo: `core/views.py` ou `escalas/views.py`

```python
from django.core.cache import cache
from django.shortcuts import redirect
from django.views import View

class CriarServicoView(View):
    """View que cria serviço e invalida cache"""
    
    def post(self, request):
        # Criar novo serviço
        servico = Servico.objects.create(
            cliente=request.POST['cliente'],
            data_do_servico=request.POST['data'],
            # ... outros campos
        )
        
        # ✅ IMPORTANTE: Invalidar caches relevantes
        # Limpar cache de dashboard
        for user_id in range(1, 100):  # Ou usar um loop melhor
            cache.delete(f"dashboard_{user_id}_{date.today()}")
        
        # Limpar cache de lista de serviços
        cache.delete(f"servicos_list_*")
        
        # Limpar cache de estatísticas
        cache.delete(f"servicos_stats_{date.today()}")
        
        messages.success(request, 'Serviço criado com sucesso!')
        return redirect('escalas:home')


def invalidar_cache_dashboard():
    """Helper function para invalidar todos os dashboards"""
    from datetime import date
    
    # Invalidar cache de todos os usuários para hoje
    User = get_user_model()
    for user in User.objects.all():
        cache.delete(f"dashboard_{user.id}_{date.today()}")
    
    # Invalidar cache global
    cache.delete(f"servicos_stats_{date.today()}")
    cache.delete(f"escalas_stats_{date.today()}")
    cache.delete(f"top_clientes_{date.today()}")


# Usar em signals do Django (se reativar ActivityLog):
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Servico)
def invalidar_cache_apos_criar_servico(sender, instance, created, **kwargs):
    """Invalidar cache quando criar novo serviço"""
    if created:
        invalidar_cache_dashboard()
```

---

## 5. Usar Redis para Sessões (Bonus)

### Arquivo: `fretamento_project/settings_heroku.py`

```python
# Usar Redis também para sessões (mais rápido que BD)
SESSION_ENGINE = 'django_redis.cache.django_redis.SessionStore'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 3600  # 1 hora

# Alternativa: usar Django Session com Redis backend
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
# SESSION_CACHE_ALIAS = 'default'
```

---

## 6. Adicionar Middleware de Cache Condicional

### Arquivo: `core/cache_middleware.py`

```python
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.utils.cache import get_cache_key, learn_cache_key
import hashlib

class SmartCacheMiddleware(MiddlewareMixin):
    """Middleware inteligente para cache condicional"""
    
    CACHEABLE_METHODS = ['GET', 'HEAD']
    CACHEABLE_STATUS = [200, 404]
    CACHE_TIMEOUT = 300  # 5 minutos
    
    def process_request(self, request):
        """Verificar se resposta pode ser servida do cache"""
        
        # Não cachear requests autenticados ou POST/PUT/DELETE
        if request.method not in self.CACHEABLE_METHODS:
            return None
        
        if request.user.is_authenticated:
            return None  # Não cachear responses personalizadas
        
        # Gerar cache key único
        cache_key = self._get_cache_key(request)
        
        # Tentar obter do cache
        response = cache.get(cache_key)
        if response:
            response['X-Cache'] = 'HIT'
            return response
        
        # Armazenar key para depois
        request._cache_key = cache_key
        return None
    
    def process_response(self, request, response):
        """Guardar resposta em cache"""
        
        # Verificar se é cacheável
        if response.status_code not in self.CACHEABLE_STATUS:
            return response
        
        if not hasattr(request, '_cache_key'):
            return response
        
        # Adicionar header indicando que foi cachedo
        response['X-Cache'] = 'MISS'
        
        # Guardar em cache
        cache.set(
            request._cache_key,
            response,
            self.CACHE_TIMEOUT
        )
        
        return response
    
    def _get_cache_key(self, request):
        """Gerar cache key baseado em URL e query params"""
        key = f"cache_{request.path}"
        
        # Incluir query params na key
        if request.GET:
            query_string = request.GET.urlencode()
            key += f"_{query_string}"
        
        # Hash para evitar chaves muito longas
        return hashlib.md5(key.encode()).hexdigest()
```

---

## 7. Monitorar Performance com Logging

### Arquivo: `core/logging_middleware.py`

```python
import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class PerformanceLoggingMiddleware(MiddlewareMixin):
    """Middleware para logar performance de views"""
    
    SLOW_REQUEST_THRESHOLD = 1000  # 1 segundo em ms
    
    def process_request(self, request):
        """Marca início da requisição"""
        request._request_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Calcula tempo total e loga se lento"""
        
        if not hasattr(request, '_request_start_time'):
            return response
        
        # Calcular tempo em ms
        elapsed_time = (time.time() - request._request_start_time) * 1000
        
        # Log structured
        log_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'elapsed_ms': round(elapsed_time, 2),
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
        }
        
        # Log sempre (debug)
        logger.debug(
            f"Request completed",
            extra=log_data
        )
        
        # Log apenas se lento (warning)
        if elapsed_time > self.SLOW_REQUEST_THRESHOLD:
            logger.warning(
                f"Slow request detected: {elapsed_time:.0f}ms",
                extra=log_data
            )
        
        # Adicionar header para monitoramento
        response['X-Response-Time'] = f"{elapsed_time:.0f}ms"
        
        return response
```

### Adicionar ao settings_heroku.py

```python
MIDDLEWARE = [
    # ... outros middlewares ...
    'core.logging_middleware.PerformanceLoggingMiddleware',  # Adicionar no final
]

LOGGING = {
    # ... configuração existente ...
    'loggers': {
        # ... loggers existentes ...
        'core.logging_middleware': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}
```

---

## 8. Exemplo Completo: Dashboard Otimizado

### Arquivo: `core/views_otimizado.py`

```python
from django.shortcuts import render
from django.core.cache import cache
from django.db.models import Count, Avg, Q, Prefetch
from django.views import View
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from datetime import date, timedelta
from core.models import Servico
from escalas.models import Escala

class DashboardOtimizadoView(View):
    """
    Dashboard MUITO otimizado com:
    ✅ Prefetch related para N+1
    ✅ Aggregation no BD
    ✅ Cache multi-nível
    ✅ Index-aware queries
    """
    
    CACHE_TIMEOUT = 300  # 5 minutos
    
    def get(self, request):
        # Autenticação obrigatória
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Cache key por usuário
        cache_key = f"dashboard_v2_{request.user.id}_{date.today()}"
        
        # Tentar cache primeiro
        context = cache.get(cache_key)
        if context:
            context['from_cache'] = True
            return render(request, 'core/dashboard.html', context)
        
        # Cache miss - gerar dados
        context = {
            'user_info': self._get_user_info(request),
            'stats_servicos': self._get_stats_servicos(),
            'stats_escalas': self._get_stats_escalas(),
            'servicos_recentes': self._get_servicos_recentes(),
            'escalas_proximas': self._get_escalas_proximas(),
            'from_cache': False,
        }
        
        # Guardar em cache
        cache.set(cache_key, context, self.CACHE_TIMEOUT)
        
        return render(request, 'core/dashboard.html', context)
    
    def _get_user_info(self, request):
        """Info do usuário (não cachear)"""
        return {
            'nome': request.user.get_full_name() or request.user.username,
            'last_login': request.user.last_login,
        }
    
    def _get_stats_servicos(self):
        """Estatísticas de serviços com agregação no BD"""
        cache_key = f"stats_servicos_{date.today()}"
        
        stats = cache.get(cache_key)
        if stats:
            return stats
        
        # UMA ÚNICA QUERY com agregação
        stats = Servico.objects.aggregate(
            total=Count('id'),
            pax_medio=Avg('pax'),
            prioritarios=Count('id', filter=Q(eh_prioritario=True)),
            regulares=Count('id', filter=Q(eh_regular=True)),
        )
        
        cache.set(cache_key, stats, self.CACHE_TIMEOUT)
        return stats
    
    def _get_stats_escalas(self):
        """Estatísticas de escalas com agregação"""
        cache_key = f"stats_escalas_{date.today()}"
        
        stats = cache.get(cache_key)
        if stats:
            return stats
        
        # UMA ÚNICA QUERY com agregação
        stats = Escala.objects.aggregate(
            total=Count('id'),
            aprovadas=Count('id', filter=Q(status='APROVADA')),
            pendentes=Count('id', filter=Q(status='PENDENTE')),
        )
        
        cache.set(cache_key, stats, self.CACHE_TIMEOUT)
        return stats
    
    def _get_servicos_recentes(self, limit=10):
        """Últimos serviços com prefetch"""
        cache_key = f"servicos_recentes_{date.today()}"
        
        servicos = cache.get(cache_key)
        if servicos:
            return servicos
        
        servicos = list(Servico.objects.filter(
            data_do_servico=date.today()
        ).order_by('-created_at')[:limit].values(
            'id', 'cliente', 'servico', 'pax', 'horario'
        ))
        
        cache.set(cache_key, servicos, self.CACHE_TIMEOUT)
        return servicos
    
    def _get_escalas_proximas(self, limit=10):
        """Escalas próximas com prefetch"""
        cache_key = f"escalas_proximas_{date.today()}"
        
        escalas = cache.get(cache_key)
        if escalas:
            return escalas
        
        data_inicio = date.today()
        data_fim = data_inicio + timedelta(days=7)
        
        escalas = list(Escala.objects.filter(
            data__range=[data_inicio, data_fim],
            status__in=['PENDENTE', 'APROVADA']
        ).order_by('data').values(
            'id', 'data', 'status', 'usuario__username'
        ))
        
        cache.set(cache_key, escalas, self.CACHE_TIMEOUT)
        return escalas
```

---

## 📝 Checklist de Implementação

### Fase 2 (Próximas semanas)
- [ ] Adicionar índices de BD (migration)
- [ ] Otimizar queries principais com prefetch_related
- [ ] Implementar cache em views críticas
- [ ] Testar performance após cada mudança

### Fase 3 (Próximo mês)
- [ ] Adicionar middleware de logging de performance
- [ ] Implementar alertas de requests lentas
- [ ] Otimizar templates (diminuir loops)
- [ ] Considerar Celery para tasks longas

---

**💡 Lembrete**: Teste localmente antes de fazer push! Sempre use `DEBUG=False` localmente para validar otimizações.
