#!/bin/bash

# Script de Deploy - Fretamento Intertouring
# Este script automatiza o processo de deploy para produção

set -e  # Parar em caso de erro

echo "🚀 Iniciando deploy do Fretamento Intertouring..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Verificar se está no diretório correto
if [ ! -f "manage.py" ]; then
    error "Script deve ser executado no diretório raiz do projeto Django"
fi

# 1. Verificar dependências
log "Verificando dependências..."

if ! command -v docker &> /dev/null; then
    warn "Docker não encontrado. Instalando via script de conveniência..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    log "Docker instalado. Faça logout/login para aplicar permissões de grupo."
fi

if ! command -v docker-compose &> /dev/null; then
    warn "Docker Compose não encontrado. Instalando..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    log "Docker Compose instalado."
fi

# 2. Verificar arquivo .env
if [ ! -f ".env" ]; then
    warn "Arquivo .env não encontrado. Copiando template..."
    cp .env.example .env
    warn "Configure o arquivo .env antes de continuar!"
    read -p "Pressione Enter para continuar após configurar o .env..."
fi

# 3. Criar diretórios necessários
log "Criando diretórios necessários..."
mkdir -p logs
mkdir -p nginx/ssl
mkdir -p backups

# 4. Gerar certificados SSL auto-assinados (para desenvolvimento)
if [ ! -f "nginx/ssl/cert.pem" ]; then
    log "Gerando certificados SSL auto-assinados..."
    openssl req -x509 -newkey rsa:4096 -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem -days 365 -nodes \
        -subj "/C=BR/ST=SP/L=Sao Paulo/O=Fretamento Intertouring/CN=localhost"
    warn "Usando certificados auto-assinados. Para produção, use certificados válidos!"
fi

# 5. Build da aplicação
log "Fazendo build da aplicação..."
docker-compose build

# 6. Iniciar serviços
log "Iniciando serviços..."
docker-compose up -d db redis

# Aguardar banco de dados estar pronto
log "Aguardando banco de dados..."
sleep 10

# 7. Executar migrações
log "Executando migrações..."
docker-compose run --rm web python manage.py migrate --settings=fretamento_project.settings_production

# 8. Coletar arquivos estáticos
log "Coletando arquivos estáticos..."
docker-compose run --rm web python manage.py collectstatic --noinput --settings=fretamento_project.settings_production

# 9. Criar superusuário (se não existir)
log "Verificando superusuário..."
if ! docker-compose run --rm web python manage.py shell --settings=fretamento_project.settings_production -c "
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    exit(1)
"; then
    log "Criando superusuário..."
    docker-compose run --rm web python manage.py createsuperuser --settings=fretamento_project.settings_production
fi

# 10. Iniciar todos os serviços
log "Iniciando todos os serviços..."
docker-compose up -d

# 11. Verificar saúde dos serviços
log "Verificando saúde dos serviços..."
sleep 15

# Verificar se os serviços estão rodando
if ! docker-compose ps | grep -q "Up"; then
    error "Alguns serviços não estão rodando corretamente"
fi

# 12. Executar testes básicos
log "Executando verificações básicas..."
if curl -f http://localhost/health/ > /dev/null 2>&1; then
    log "✅ Aplicação respondendo na porta 80"
else
    warn "⚠️ Aplicação não está respondendo na porta 80"
fi

# 13. Backup inicial
log "Criando backup inicial..."
docker-compose exec -T db pg_dump -U fretamento_user fretamento_prod > "backups/initial_backup_$(date +%Y%m%d_%H%M%S).sql"

# 14. Configurar scripts de manutenção
log "Configurando scripts de manutenção..."

# Script de backup
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Criar backup do banco
docker-compose exec -T db pg_dump -U fretamento_user fretamento_prod > "$BACKUP_DIR/backup_$TIMESTAMP.sql"

# Manter apenas os últimos 7 backups
ls -t $BACKUP_DIR/backup_*.sql | tail -n +8 | xargs -r rm

echo "Backup criado: backup_$TIMESTAMP.sql"
EOF

chmod +x backup.sh

# Script de atualização
cat > update.sh << 'EOF'
#!/bin/bash
echo "Atualizando aplicação..."

# Fazer backup antes da atualização
./backup.sh

# Atualizar código
git pull

# Rebuild e restart
docker-compose build
docker-compose up -d

# Executar migrações
docker-compose run --rm web python manage.py migrate --settings=fretamento_project.settings_production

# Coletar estáticos
docker-compose run --rm web python manage.py collectstatic --noinput --settings=fretamento_project.settings_production

echo "Atualização concluída!"
EOF

chmod +x update.sh

# Script de logs
cat > logs.sh << 'EOF'
#!/bin/bash
echo "Escolha o serviço para ver os logs:"
echo "1) Web Application"
echo "2) Database"
echo "3) Redis"
echo "4) Nginx"
echo "5) Todos"

read -p "Opção (1-5): " option

case $option in
    1) docker-compose logs -f web ;;
    2) docker-compose logs -f db ;;
    3) docker-compose logs -f redis ;;
    4) docker-compose logs -f nginx ;;
    5) docker-compose logs -f ;;
    *) echo "Opção inválida" ;;
esac
EOF

chmod +x logs.sh

# 15. Configurar crontab para backups automáticos
log "Configurando backups automáticos..."
(crontab -l 2>/dev/null; echo "0 2 * * * cd $(pwd) && ./backup.sh") | crontab -

log "✅ Deploy concluído com sucesso!"
log ""
log "🌐 Aplicação disponível em:"
log "   - HTTP: http://localhost"
log "   - HTTPS: https://localhost (certificado auto-assinado)"
log ""
log "🔧 Scripts disponíveis:"
log "   - ./backup.sh - Criar backup manual"
log "   - ./update.sh - Atualizar aplicação"
log "   - ./logs.sh - Ver logs dos serviços"
log ""
log "📊 Comandos úteis:"
log "   - docker-compose ps - Status dos serviços"
log "   - docker-compose logs -f - Ver todos os logs"
log "   - docker-compose down - Parar todos os serviços"
log "   - docker-compose up -d - Iniciar todos os serviços"
log ""
log "⚠️  IMPORTANTE:"
log "   - Configure certificados SSL válidos para produção"
log "   - Ajuste as variáveis de ambiente no arquivo .env"
log "   - Configure firewall para expor apenas portas 80 e 443"
log "   - Considere usar um proxy reverso como Cloudflare"