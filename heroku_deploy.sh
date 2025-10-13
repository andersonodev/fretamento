#!/bin/bash

# ============================================
# SCRIPT DE DEPLOY HEROKU - FRETAMENTO INTERTOURING
# ============================================

set -e  # Sair em caso de erro

echo "🚀 INICIANDO DEPLOY NO HEROKU..."
echo "=================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Verificar se o Heroku CLI está instalado
if ! command -v heroku &> /dev/null; then
    error "Heroku CLI não está instalado. Instale em: https://devcenter.heroku.com/articles/heroku-cli"
fi

# Verificar se está logado no Heroku
if ! heroku auth:whoami &> /dev/null; then
    error "Você não está logado no Heroku. Execute: heroku login"
fi

# Nome da app no Heroku
APP_NAME="fretamento-intertouring"

log "Verificando se a app '$APP_NAME' existe..."

# Verificar se a app existe
if heroku apps:info $APP_NAME &> /dev/null; then
    info "App '$APP_NAME' encontrada no Heroku"
else
    warning "App '$APP_NAME' não encontrada. Criando nova app..."
    heroku create $APP_NAME --region us
    log "App '$APP_NAME' criada com sucesso!"
fi

# Configurar variáveis de ambiente
log "Configurando variáveis de ambiente..."

# Gerar SECRET_KEY se não existir
SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

heroku config:set \
    SECRET_KEY="$SECRET_KEY" \
    DJANGO_SETTINGS_MODULE="fretamento_project.settings_heroku" \
    DEBUG=False \
    --app $APP_NAME

log "Variáveis de ambiente configuradas!"

# Verificar se PostgreSQL está configurado
log "Verificando addon PostgreSQL..."
if heroku addons --app $APP_NAME | grep -q "heroku-postgresql"; then
    info "PostgreSQL já está configurado"
else
    log "Adicionando PostgreSQL Essential-0..."
    heroku addons:create heroku-postgresql:essential-0 --app $APP_NAME
    log "PostgreSQL adicionado com sucesso!"
fi

# Preparar para deploy
log "Preparando arquivos para deploy..."

# Verificar se todos os arquivos necessários existem
required_files=("Procfile" "requirements-heroku.txt" "runtime.txt")
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        error "Arquivo obrigatório '$file' não encontrado!"
    fi
done

# Coletar arquivos estáticos localmente para verificar
log "Testando coleta de arquivos estáticos..."
python manage.py collectstatic --noinput --settings=fretamento_project.settings_heroku || error "Erro na coleta de arquivos estáticos"

# Fazer commit das mudanças se houver
if [[ -n $(git status --porcelain) ]]; then
    warning "Há mudanças não commitadas. Fazendo commit automático..."
    git add .
    git commit -m "🚀 deploy: preparar para deploy no Heroku $(date '+%Y-%m-%d %H:%M:%S')"
fi

# Deploy no Heroku
log "Iniciando deploy no Heroku..."
git push heroku main

# Executar migrações
log "Executando migrações no banco de dados..."
heroku run python manage.py migrate --app $APP_NAME

# Criar superuser se necessário (interativo)
echo ""
info "Deseja criar um superuser? (y/n)"
read -p "Resposta: " create_superuser
if [[ $create_superuser == "y" || $create_superuser == "Y" ]]; then
    log "Criando superuser..."
    heroku run python manage.py createsuperuser --app $APP_NAME
fi

# Coletar arquivos estáticos no servidor
log "Coletando arquivos estáticos no servidor..."
heroku run python manage.py collectstatic --noinput --app $APP_NAME

# Verificar se a app está funcionando
log "Verificando saúde da aplicação..."
APP_URL="https://$APP_NAME.herokuapp.com"
if curl -s -o /dev/null -w "%{http_code}" "$APP_URL" | grep -q "200\|301\|302"; then
    log "✅ Aplicação está respondendo corretamente!"
else
    warning "⚠️ Aplicação pode não estar respondendo corretamente"
fi

# Abrir logs em caso de problema
info "Deseja visualizar os logs da aplicação? (y/n)"
read -p "Resposta: " show_logs
if [[ $show_logs == "y" || $show_logs == "Y" ]]; then
    heroku logs --tail --app $APP_NAME
fi

# Configurar domínio personalizado (se disponível)
echo ""
info "Deseja configurar um domínio personalizado? (y/n)"
read -p "Resposta: " setup_domain
if [[ $setup_domain == "y" || $setup_domain == "Y" ]]; then
    read -p "Digite o domínio (ex: meusite.com): " domain
    if [[ -n "$domain" ]]; then
        log "Configurando domínio personalizado: $domain"
        heroku domains:add $domain --app $APP_NAME
        log "Domínio adicionado! Configure seu DNS apontando para:"
        heroku domains --app $APP_NAME
    fi
fi

echo ""
echo "🎉 DEPLOY CONCLUÍDO COM SUCESSO!"
echo "=================================="
log "URL da aplicação: $APP_URL"
log "Painel admin: $APP_URL/admin/"
echo ""
info "Comandos úteis:"
echo "  • Ver logs: heroku logs --tail --app $APP_NAME"
echo "  • Abrir app: heroku open --app $APP_NAME"
echo "  • Shell Django: heroku run python manage.py shell --app $APP_NAME"
echo "  • Migrações: heroku run python manage.py migrate --app $APP_NAME"
echo "  • Collectstatic: heroku run python manage.py collectstatic --app $APP_NAME"
echo ""
log "Deploy finalizado em: $(date '+%Y-%m-%d %H:%M:%S')"