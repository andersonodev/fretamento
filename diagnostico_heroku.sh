#!/bin/bash

# 🔍 Script de Diagnóstico Heroku
# Use para análise de BD e servidor

set -e

echo "╔════════════════════════════════════════════════════╗"
echo "║  🔍 DIAGNÓSTICO HEROKU - Banco de Dados & Servidor║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_NAME="${1:-fretamento-intertouring}"

echo -e "${BLUE}🎯 Analisando app: ${APP_NAME}${NC}"
echo ""

# ============================================
# 1. INFORMAÇÕES DO DYNO
# ============================================
echo -e "${YELLOW}[1/6] Verificando Dynos...${NC}"
echo "────────────────────────────────────"
heroku ps --app $APP_NAME || echo "Erro ao acessar dynos"
echo ""

# ============================================
# 2. INFORMAÇÕES DO BANCO
# ============================================
echo -e "${YELLOW}[2/6] Verificando PostgreSQL...${NC}"
echo "────────────────────────────────────"
heroku pg:info --app $APP_NAME || echo "Erro ao acessar PostgreSQL"
echo ""

# ============================================
# 3. TAMANHO DO BANCO
# ============================================
echo -e "${YELLOW}[3/6] Tamanho do Banco de Dados...${NC}"
echo "────────────────────────────────────"
heroku pg:psql --app $APP_NAME -c "
SELECT 
    pg_size_pretty(pg_database_size(current_database())) AS tamanho_total,
    (SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema')) AS total_tabelas
" 2>/dev/null || echo "Erro ao ler tamanho do BD"
echo ""

# ============================================
# 4. TOP 5 TABELAS MAIORES
# ============================================
echo -e "${YELLOW}[4/6] Top 5 Tabelas Maiores...${NC}"
echo "────────────────────────────────────"
heroku pg:psql --app $APP_NAME -c "
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS tamanho,
    n_live_tup AS linhas
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 5
" 2>/dev/null || echo "Erro ao listar tabelas"
echo ""

# ============================================
# 5. ANÁLISE DE ÍNDICES
# ============================================
echo -e "${YELLOW}[5/6] Análise de Índices...${NC}"
echo "────────────────────────────────────"
heroku pg:psql --app $APP_NAME -c "
-- Ver índices não utilizados
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan AS numero_scans
FROM pg_stat_user_indexes
WHERE idx_scan = 0
LIMIT 10;
" 2>/dev/null || echo "Erro ao analisar índices"
echo ""

# ============================================
# 6. ÚLTIMAS ATIVIDADES
# ============================================
echo -e "${YELLOW}[6/6] Últimas Atividades...${NC}"
echo "────────────────────────────────────"
heroku releases --app $APP_NAME --num 5 || echo "Erro ao acessar releases"
echo ""

# ============================================
# RESUMO RECOMENDAÇÕES
# ============================================
echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  📋 PRÓXIMAS ETAPAS                               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}✅ Se tamanho do BD < 500MB:${NC}"
echo "   → Sistema OK para produção"
echo ""

echo -e "${YELLOW}⚠️  Se tamanho do BD > 500MB:${NC}"
echo "   → Considere limpar dados antigos"
echo "   → Implementar soft deletes"
echo ""

echo -e "${YELLOW}⚠️  Se conexões de BD > 15:${NC}"
echo "   → Aumentar pool de conexões"
echo "   → Ou fazer upgrade do plano"
echo ""

echo -e "${YELLOW}⚠️  Se dyno está com > 90% memória:${NC}"
echo "   → Fazer upgrade para standard-1x"
echo "   → Ou adicionar dyno worker extra"
echo ""

# ============================================
# OPÇÕES DE UPGRADE
# ============================================
echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  💰 OPÇÕES DE UPGRADE                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

echo "1️⃣  DYNO UPGRADE (atual: free/hobby → standard-1x)"
echo "   Custo: +\$50/mês"
echo "   Ganho: 1GB RAM, CPU dedicada"
echo "   Comando:"
echo "   $ heroku ps:type web=standard-1x --app $APP_NAME"
echo ""

echo "2️⃣  POSTGRESQL UPGRADE (atual: essential-0 → standard-0)"
echo "   Custo: +\$50/mês"
echo "   Ganho: 64GB storage, 120 conexões, read replicas"
echo "   Comando:"
echo "   $ heroku addons:upgrade heroku-postgresql:standard-0 --app $APP_NAME"
echo ""

echo "3️⃣  REDIS PARA CACHE (se não tem)"
echo "   Custo: +\$15/mês"
echo "   Ganho: Cache distribuído entre workers"
echo "   Comando:"
echo "   $ heroku addons:create heroku-redis:premium-0 --app $APP_NAME"
echo ""

echo "4️⃣  ADICIONAR WORKER DYNO (escalar horizontalmente)"
echo "   Custo: +\$7/mês por dyno"
echo "   Ganho: 2x de throughput"
echo "   Comando:"
echo "   $ heroku ps:scale web=2 --app $APP_NAME"
echo ""

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ⚡ OTIMIZAÇÕES GRATUITAS (ANTES DE UPGRADE)     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

echo "1. Implementar FASE 2 (N+1 Queries) → 60-80% de melhoria"
echo "2. Adicionar índices de BD → 20-40% de melhoria"
echo "3. Limpar dados antigos → libera espaço"
echo "4. Implementar cache inteligente → 30-50% de melhoria"
echo ""

echo -e "${GREEN}✅ Recomendação: Fazer FASE 2 ANTES de fazer upgrade!${NC}"
echo ""
