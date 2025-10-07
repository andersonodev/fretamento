# Ambientes de Deploy - Comparação Completa

Esta documentação compara as diferentes opções de deploy para o Fretamento Intertouring.

## 🏗️ Visão Geral dos Ambientes

| Ambiente | Complexidade | Custo | Performance | Escalabilidade | Banco de Dados |
|----------|--------------|-------|-------------|----------------|----------------|
| **Desenvolvimento Local** | ⭐ | Gratuito | Boa | N/A | SQLite |
| **Vercel (Serverless)** | ⭐⭐ | Gratuito/Pago | Ótima | Alta | SQLite/Externo |
| **Docker (VPS/Cloud)** | ⭐⭐⭐ | Variável | Excelente | Média | PostgreSQL |
| **Kubernetes** | ⭐⭐⭐⭐⭐ | Alto | Excelente | Muito Alta | PostgreSQL |

## 🖥️ 1. Desenvolvimento Local

### Características
- **Propósito**: Desenvolvimento e testes
- **Banco**: SQLite (`db.sqlite3`)
- **Servidor**: `runserver` do Django
- **Performance**: Adequada para desenvolvimento

### Configuração
```bash
# Instalar dependências
pip install -r requirements.txt

# Aplicar migrações
python manage.py migrate

# Executar servidor
python manage.py runserver
```

### Prós e Contras
✅ **Prós**:
- Setup instantâneo
- Debug fácil
- Reload automático
- Zero custo

❌ **Contras**:
- Não escalável
- SQLite limitado
- Apenas desenvolvimento

---

## ☁️ 2. Vercel (Serverless)

### Características
- **Propósito**: Protótipos, demos, MVP
- **Banco**: SQLite temporário ou DB externo
- **Servidor**: Functions serverless
- **Performance**: Cold start ~500ms, depois rápido

### Estrutura de Arquivos
```
projeto/
├── vercel.json                    # Configuração da Vercel
├── build.sh                      # Script de build
├── requirements-vercel.txt        # Dependências otimizadas
├── fretamento_project/
│   ├── settings_vercel.py        # Settings para Vercel
│   └── wsgi.py                   # WSGI compatível
└── static/                       # Servidos pelo CDN
```

### Limitações Importantes

#### SQLite na Vercel
⚠️ **Dados Temporários**: SQLite é recriado a cada deploy
- Dados perdidos em novos deploys
- Apenas para dados de exemplo/teste
- Não adequado para produção real

#### Soluções para Persistência
```python
# Opção 1: Banco externo (Railway/Supabase)
DATABASES = {
    'default': dj_database_url.parse(
        os.environ.get('DATABASE_URL', 'sqlite:///tmp/db.sqlite3')
    )
}

# Opção 2: Fixtures para dados iniciais
python manage.py loaddata fixtures/dados_exemplo.json
```

### Custos Vercel
```yaml
Gratuito:
  - Bandwidth: 100GB/mês
  - Builds: 6.000 min/mês
  - Functions: 12 exec/hora/função
  - Domínio: .vercel.app

Pro ($20/mês):
  - Bandwidth: 1TB/mês
  - Builds: ilimitado
  - Functions: 1.000 exec/hora/função
  - Domínios customizados: ilimitados
```

### Deploy na Vercel
```bash
# 1. Configurar variáveis
DJANGO_SECRET_KEY=sua-chave-secreta
DJANGO_SETTINGS_MODULE=fretamento_project.settings_vercel

# 2. Deploy automático via GitHub
git push origin main

# 3. Ou via CLI
vercel --prod
```

---

## 🐳 3. Docker (VPS/Cloud)

### Características
- **Propósito**: Produção robusta
- **Banco**: PostgreSQL dedicado
- **Servidor**: Gunicorn + Nginx
- **Performance**: Excelente e consistente

### Estrutura de Arquivos
```
projeto/
├── Dockerfile                    # Imagem da aplicação
├── docker-compose.yml           # Orquestração completa
├── nginx.conf                   # Proxy reverso
├── deploy.sh                    # Script de deploy
├── fretamento_project/
│   └── settings_production.py   # Settings para produção
└── requirements.txt             # Dependências completas
```

### Stack Completa
```yaml
Services:
  web:
    - Django + Gunicorn
    - Volumes para media/static
    - Health checks
  
  db:
    - PostgreSQL 15
    - Volumes persistentes
    - Backup automático
  
  nginx:
    - Proxy reverso
    - SSL termination
    - Compressão gzip
    - Cache de estáticos
  
  redis (opcional):
    - Cache do Django
    - Sessions
    - Celery queue
```

### Provedores Recomendados

#### DigitalOcean Droplets
```yaml
Básico ($6/mês):
  - 1 vCPU, 1GB RAM
  - 25GB SSD
  - Ideal para testes

Produção ($24/mês):
  - 2 vCPUs, 4GB RAM
  - 80GB SSD
  - Backup automático
```

#### AWS EC2
```yaml
t3.micro (Free Tier):
  - 1 vCPU, 1GB RAM
  - 750h/mês gratuitas
  - Ideal para começar

t3.small ($16/mês):
  - 2 vCPUs, 2GB RAM
  - Performance consistente
```

#### Railway
```yaml
Hobby ($5/mês):
  - 512MB RAM
  - 1GB storage
  - Deploy automático

Pro ($20/mês):
  - 8GB RAM
  - 100GB storage
  - Múltiplos ambientes
```

### Deploy Docker
```bash
# 1. Configurar servidor
ssh user@servidor
sudo apt update && sudo apt install docker.io docker-compose

# 2. Clonar projeto
git clone https://github.com/seu-usuario/fretamento-intertouring.git
cd fretamento-intertouring

# 3. Configurar ambiente
cp .env.example .env
nano .env  # Editar variáveis

# 4. Deploy
chmod +x deploy.sh
./deploy.sh
```

---

## ⚖️ 4. Comparação Detalhada

### Performance

| Métrica | Local | Vercel | Docker VPS | Docker Cloud |
|---------|-------|--------|------------|--------------|
| **Cold Start** | N/A | ~500ms | N/A | N/A |
| **Response Time** | <100ms | 100-300ms | 50-150ms | 50-100ms |
| **Throughput** | Baixo | Médio | Alto | Muito Alto |
| **Uptime** | N/A | 99.9% | 99.5% | 99.99% |

### Custos Mensais (USD)

#### Cenários de Uso

**MVP/Demonstração**:
- Vercel Gratuito: $0
- DigitalOcean Basic: $6
- Railway Hobby: $5

**Pequena Empresa (< 1000 usuários)**:
- Vercel Pro: $20
- DigitalOcean Standard: $24
- AWS t3.small: $16

**Empresa Média (1000-10000 usuários)**:
- Vercel Pro + DB: $40
- DigitalOcean + DB: $50
- AWS + RDS: $80

**Enterprise (10000+ usuários)**:
- Múltiplas instâncias: $200+
- Load balancer: $20+
- CDN: $50+
- Monitoring: $30+

### Segurança

| Aspecto | Local | Vercel | Docker |
|---------|-------|--------|--------|
| **HTTPS** | Manual | Automático | Manual |
| **Firewall** | SO | Vercel | Manual |
| **Updates** | Manual | Automático | Manual |
| **Backup** | Manual | N/A | Manual |
| **Monitoring** | Manual | Integrado | Manual |

### Escalabilidade

#### Vercel (Serverless)
```yaml
Vantagens:
  - Escala automaticamente
  - Zero configuração
  - Global CDN

Limitações:
  - Cold starts
  - Timeout de execução (10s)
  - Tamanho da função (50MB)
  - Sem estado persistente
```

#### Docker (Container)
```yaml
Vantagens:
  - Controle total
  - Performance consistente
  - Estado persistente
  - Sem timeouts

Escalabilidade:
  - Manual: docker-compose scale web=3
  - Kubernetes: auto-scaling
  - Load balancer necessário
```

---

## 🎯 5. Recomendações por Cenário

### 🚀 Início Rápido (Protótipo/Demo)
**Recomendação**: Vercel + SQLite
```bash
✅ Deploy em 5 minutos
✅ HTTPS automático
✅ Custo zero
❌ Dados não persistem
```

### 🏢 Pequena Empresa
**Recomendação**: Vercel + Railway PostgreSQL
```bash
✅ Escalabilidade automática
✅ Backup gerenciado
✅ Baixa manutenção
💰 ~$25/mês
```

### 🏭 Produção Robusta
**Recomendação**: Docker + VPS
```bash
✅ Controle total
✅ Performance consistente
✅ Dados seguros
⚙️ Requer DevOps
💰 $30-100/mês
```

### 🌐 Enterprise
**Recomendação**: Kubernetes + Cloud
```bash
✅ Alta disponibilidade
✅ Auto-scaling
✅ Multi-região
⚙️ Complexidade alta
💰 $200+/mês
```

---

## 📋 6. Checklist de Decisão

### Para Vercel, escolha se:
- [ ] É um protótipo ou MVP
- [ ] Quer deploy instantâneo
- [ ] Tem orçamento limitado
- [ ] Não precisa de dados persistentes
- [ ] Quer zero manutenção

### Para Docker, escolha se:
- [ ] É um projeto de produção
- [ ] Precisa de dados persistentes
- [ ] Quer controle total
- [ ] Tem conhecimento de DevOps
- [ ] Performance é crítica

### Para ambos:
- [ ] Configure monitoramento
- [ ] Implemente backup
- [ ] Configure SSL/HTTPS
- [ ] Monitore custos
- [ ] Documente o processo

---

## 🔧 7. Scripts de Migração Entre Ambientes

### De Vercel para Docker
```bash
# 1. Exportar dados (se usando DB externo)
python manage.py dumpdata > backup.json

# 2. Configurar Docker
cp .env.vercel .env.docker
# Editar configurações de PostgreSQL

# 3. Deploy Docker
docker-compose up -d

# 4. Importar dados
docker-compose exec web python manage.py loaddata backup.json
```

### De Docker para Vercel
```bash
# 1. Exportar dados para fixtures
docker-compose exec web python manage.py dumpdata > fixtures/dados.json

# 2. Configurar Vercel
git add vercel.json settings_vercel.py
git commit -m "feat: adicionar suporte Vercel"
git push

# 3. Deploy na Vercel
vercel --prod
```

---

## 📊 8. Monitoramento e Métricas

### Métricas Importantes
```python
# Django + PostgreSQL
from django.db import connection

def get_db_metrics():
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM escalas_escala")
        return cursor.fetchone()[0]

# Logs estruturados
import logging
logger = logging.getLogger(__name__)

def track_performance(view_name, duration):
    logger.info(f"View: {view_name}, Duration: {duration}ms")
```

### Alertas Recomendados
- Response time > 2s
- Error rate > 5%
- Disk usage > 80%
- Memory usage > 85%
- Database connections > 80%

---

**🎯 Escolha o ambiente ideal para seu projeto e contexto!**