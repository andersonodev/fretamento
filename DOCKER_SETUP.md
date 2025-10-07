# 🐳 Configuração Multi-Database - Fretamento Intertouring

O sistema agora suporta tanto **SQLite** (desenvolvimento local) quanto **PostgreSQL** (Docker/Produção) automaticamente.

## 🚀 Como usar

### Opção 1: Desenvolvimento Local (SQLite)
```bash
# Usar o script de conveniência
./start.sh local

# OU manualmente:
# Configure USE_DOCKER=False no .env
python manage.py migrate
python manage.py runserver
```

### Opção 2: Docker com PostgreSQL (Híbrido)
```bash
# Usar o script de conveniência
./start.sh docker

# OU manualmente:
# Configure USE_DOCKER=True no .env
docker-compose up -d db redis
python manage.py migrate
python manage.py runserver
```

### Opção 3: Tudo no Docker
```bash
# Usar o script de conveniência
./start.sh docker-full

# OU manualmente:
docker-compose up --build
```

## ⚙️ Configuração automática

O sistema detecta automaticamente qual banco usar baseado nas variáveis de ambiente:

- **USE_DOCKER=False** → SQLite local
- **USE_DOCKER=True** → PostgreSQL no Docker
- **DATABASE_URL definida** → Usa a URL fornecida

## 📝 Scripts de conveniência

```bash
./start.sh help         # Mostra ajuda
./start.sh local        # SQLite local
./start.sh docker       # PostgreSQL + Django local
./start.sh docker-full  # Tudo no Docker
./start.sh stop         # Para containers
./start.sh clean        # Limpeza completa
./start.sh migrate      # Executa migrações
./start.sh superuser    # Cria superusuário
./start.sh logs         # Mostra logs
```

## 🔧 Arquivo .env

Copie o `.env.example` para `.env` e configure conforme necessário:

```bash
# Para SQLite (desenvolvimento)
DEBUG=True
USE_DOCKER=False

# Para PostgreSQL (Docker)
DEBUG=True
USE_DOCKER=True
DB_PASSWORD=sua_senha_aqui
```

## 🐘 PostgreSQL com Docker

O `docker-compose.yml` inclui:
- PostgreSQL 15 Alpine
- Redis para cache
- Volumes persistentes
- Health checks
- Nginx (perfil production)

## 📁 Estrutura

- `Dockerfile` - Container da aplicação Django
- `docker-compose.yml` - Orquestração completa
- `.env.example` - Template de configuração
- `start.sh` - Script de conveniência
- `settings.py` - Configuração multi-database

## 🔒 Produção

Para produção, configure:
```bash
DEBUG=False
USE_DOCKER=True
# Configure DATABASE_URL ou variáveis DB_*
# Configure SECRET_KEY única
# Configure ALLOWED_HOSTS com seu domínio
```