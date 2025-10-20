#!/bin/bash

# ============================================
# DEPLOY DE CORREÇÕES - FRETAMENTO INTERTOURING
# ============================================

set -e  # Sair em caso de erro

echo "🔧 APLICANDO CORREÇÕES NO SISTEMA..."
echo "=================================="

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para log colorido
log() {
    echo -e "${GREEN}✅ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

info "Verificando status do Git..."
git status

echo ""
info "Adicionando arquivos modificados..."
git add core/views.py
git add core/urls.py
git add Procfile
git add PROBLEMA_DNS_SOLUCAO.md

echo ""
info "Fazendo commit das correções..."
git commit -m "fix: adiciona endpoint /api/dashboard/updates/ e otimiza Gunicorn

- Adiciona DashboardUpdatesView para verificar atualizações em tempo real
- Corrige erro 404 no endpoint /api/dashboard/updates/
- Otimiza Procfile: 4 workers, timeout 60s, preload habilitado
- Documenta problema de DNS e soluções em PROBLEMA_DNS_SOLUCAO.md

Correções implementadas:
✅ Endpoint AJAX funcionando
✅ Gunicorn otimizado para melhor performance
✅ Documentação completa do problema de DNS
"

echo ""
log "Commit realizado com sucesso!"

echo ""
warning "PRÓXIMOS PASSOS:"
echo ""
echo "1️⃣  FAZER DEPLOY NO HEROKU:"
echo "   git push heroku main"
echo ""
echo "2️⃣  TESTAR ENDPOINT AJAX:"
echo "   curl https://fretamento-intertouring-d423e478ec7f.herokuapp.com/api/dashboard/updates/"
echo ""
echo "3️⃣  RESOLVER PROBLEMA DNS:"
echo "   Leia o arquivo PROBLEMA_DNS_SOLUCAO.md"
echo "   Opção recomendada: Migrar para Cloudflare DNS"
echo ""
echo "4️⃣  VERIFICAR HEALTH CHECK:"
echo "   curl https://fretamento-intertouring-d423e478ec7f.herokuapp.com/core/health/"
echo ""

info "Deseja fazer deploy no Heroku agora? (y/n)"
read -p "Resposta: " deploy_now

if [[ $deploy_now == "y" || $deploy_now == "Y" ]]; then
    echo ""
    info "Iniciando deploy no Heroku..."
    
    # Fazer push para o Heroku
    git push heroku main
    
    echo ""
    log "Deploy concluído!"
    
    echo ""
    info "Aguardando 10 segundos para a aplicação reiniciar..."
    sleep 10
    
    echo ""
    info "Testando endpoint AJAX..."
    curl -s https://fretamento-intertouring-d423e478ec7f.herokuapp.com/api/dashboard/updates/ | python3 -m json.tool || echo "Endpoint ainda não está respondendo"
    
    echo ""
    info "Verificando health check..."
    curl -s https://fretamento-intertouring-d423e478ec7f.herokuapp.com/core/health/ | python3 -m json.tool || echo "Health check ainda não está respondendo"
    
    echo ""
    log "Testes concluídos!"
    
    echo ""
    warning "IMPORTANTE: O domínio fretamentointertouring.tech ainda não funcionará"
    warning "até você seguir as instruções em PROBLEMA_DNS_SOLUCAO.md"
else
    echo ""
    info "Deploy não realizado. Você pode fazer manualmente depois com:"
    echo "   git push heroku main"
fi

echo ""
log "Script finalizado!"
