#!/bin/bash

# Script para iniciar o projeto em diferentes ambientes

set -e

echo "🚀 Fretamento Intertouring - Setup"
echo "=================================="

# Função para mostrar ajuda
show_help() {
    echo "Uso: ./start.sh [OPÇÃO]"
    echo ""
    echo "Opções:"
    echo "  local      Inicia com SQLite (desenvolvimento local)"
    echo "  docker     Inicia com PostgreSQL no Docker"
    echo "  docker-full Inicia tudo com Docker (aplicação + banco)"
    echo "  stop       Para todos os containers"
    echo "  clean      Para e remove containers e volumes"
    echo "  migrate    Executa migrações"
    echo "  superuser  Cria superusuário"
    echo "  logs       Mostra logs dos containers"
    echo "  help       Mostra esta ajuda"
    echo ""
}

# Função para iniciar local (SQLite)
start_local() {
    echo "📦 Iniciando em modo local (SQLite)..."
    
    # Configura .env para SQLite
    cat > .env << EOF
DEBUG=True
USE_DOCKER=False
DATABASE_URL=
SECRET_KEY=django-insecure-!ybpw6s0nsg=d_j@n(4aj7z1tu2ok&y99r_$1&t-2&%xst-9p)
ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0
EOF
    
    echo "✅ Configurado para SQLite"
    echo "🔧 Executando migrações..."
    python manage.py migrate
    
    echo "📊 Coletando arquivos estáticos..."
    python manage.py collectstatic --noinput
    
    echo "🌐 Iniciando servidor..."
    python manage.py runserver
}

# Função para iniciar com Docker (PostgreSQL)
start_docker() {
    echo "🐳 Iniciando PostgreSQL com Docker..."
    
    # Configura .env para Docker
    cat > .env << EOF
DEBUG=True
USE_DOCKER=True
DATABASE_URL=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fretamento_db
DB_USER=fretamento_user
DB_PASSWORD=fretamento_password
SECRET_KEY=django-insecure-!ybpw6s0nsg=d_j@n(4aj7z1tu2ok&y99r_$1&t-2&%xst-9p)
ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0
REDIS_URL=redis://localhost:6379/1
EOF
    
    echo "🚀 Iniciando banco PostgreSQL e Redis..."
    docker-compose up -d db redis
    
    echo "⏳ Aguardando PostgreSQL ficar disponível..."
    sleep 10
    
    echo "🔧 Executando migrações..."
    python manage.py migrate
    
    echo "📊 Coletando arquivos estáticos..."
    python manage.py collectstatic --noinput
    
    echo "🌐 Iniciando servidor Django..."
    python manage.py runserver
}

# Função para iniciar tudo com Docker
start_docker_full() {
    echo "🐳 Iniciando aplicação completa com Docker..."
    
    # Configura .env para Docker
    cat > .env << EOF
DEBUG=False
USE_DOCKER=True
DATABASE_URL=
DB_HOST=db
DB_PORT=5432
DB_NAME=fretamento_db
DB_USER=fretamento_user
DB_PASSWORD=fretamento_password
SECRET_KEY=django-insecure-!ybpw6s0nsg=d_j@n(4aj7z1tu2ok&y99r_$1&t-2&%xst-9p)
ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0
REDIS_URL=redis://redis:6379/1
EOF
    
    echo "🚀 Construindo e iniciando todos os serviços..."
    docker-compose up --build
}

# Função para parar containers
stop_containers() {
    echo "🛑 Parando containers..."
    docker-compose down
}

# Função para limpeza completa
clean_containers() {
    echo "🧹 Limpeza completa (containers + volumes)..."
    docker-compose down -v
    docker system prune -f
}

# Função para executar migrações
run_migrations() {
    echo "🔧 Executando migrações..."
    if [ -f .env ] && grep -q "USE_DOCKER=True" .env; then
        docker-compose exec web python manage.py migrate
    else
        python manage.py migrate
    fi
}

# Função para criar superusuário
create_superuser() {
    echo "👤 Criando superusuário..."
    if [ -f .env ] && grep -q "USE_DOCKER=True" .env; then
        docker-compose exec web python manage.py createsuperuser
    else
        python manage.py createsuperuser
    fi
}

# Função para mostrar logs
show_logs() {
    echo "📋 Mostrando logs dos containers..."
    docker-compose logs -f
}

# Menu principal
case "${1:-help}" in
    "local")
        start_local
        ;;
    "docker")
        start_docker
        ;;
    "docker-full")
        start_docker_full
        ;;
    "stop")
        stop_containers
        ;;
    "clean")
        clean_containers
        ;;
    "migrate")
        run_migrations
        ;;
    "superuser")
        create_superuser
        ;;
    "logs")
        show_logs
        ;;
    "help"|*)
        show_help
        ;;
esac