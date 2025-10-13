#!/bin/bash

# Script para commit e push automático
# Uso: ./git_push.sh "mensagem do commit"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Script de Commit e Push Automático${NC}"
echo "======================================"

# Verificar se há uma mensagem de commit
if [ -z "$1" ]; then
    echo -e "${YELLOW}⚠️  Nenhuma mensagem de commit fornecida${NC}"
    echo -e "${BLUE}💡 Uso: ./git_push.sh \"sua mensagem de commit\"${NC}"
    echo ""
    read -p "Digite a mensagem do commit: " commit_message
    if [ -z "$commit_message" ]; then
        echo -e "${RED}❌ Mensagem de commit é obrigatória${NC}"
        exit 1
    fi
else
    commit_message="$1"
fi

echo ""
echo -e "${BLUE}📋 Verificando status do repositório...${NC}"
git status

echo ""
echo -e "${BLUE}📥 Adicionando arquivos...${NC}"
git add .

echo ""
echo -e "${BLUE}💾 Fazendo commit...${NC}"
git commit -m "$commit_message"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Commit realizado com sucesso!${NC}"
else
    echo -e "${YELLOW}⚠️  Nenhuma alteração para commit ou erro no commit${NC}"
fi

echo ""
echo -e "${BLUE}🌐 Fazendo push para origin main...${NC}"
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 Push realizado com sucesso!${NC}"
    echo -e "${GREEN}📡 Alterações enviadas para o GitHub${NC}"
    echo -e "${BLUE}🔄 Deploy automático no Vercel será iniciado...${NC}"
else
    echo -e "${RED}❌ Erro no push${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📊 Status final:${NC}"
git status

echo ""
echo -e "${GREEN}✨ Processo concluído!${NC}"