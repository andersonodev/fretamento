#!/bin/bash

# Script para deploy no Heroku
# Uso: ./heroku_deploy.sh

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 Script de Deploy no Heroku${NC}"
echo "==============================="

# Verificar se está logado no Heroku
echo -e "${BLUE}🔐 Verificando login no Heroku...${NC}"
heroku auth:whoami > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Não está logado no Heroku${NC}"
    echo -e "${BLUE}🔑 Fazendo login...${NC}"
    heroku login
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Erro no login do Heroku${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Login no Heroku confirmado${NC}"

# Listar apps disponíveis
echo ""
echo -e "${BLUE}📱 Apps disponíveis no Heroku:${NC}"
heroku apps

echo ""
read -p "Digite o nome do app Heroku (ou pressione Enter para usar 'fretamento-intertouring'): " app_name

if [ -z "$app_name" ]; then
    app_name="fretamento-intertouring"
fi

echo ""
echo -e "${BLUE}🎯 App selecionado: ${YELLOW}$app_name${NC}"

# Verificar se o app existe
echo -e "${BLUE}🔍 Verificando se o app existe...${NC}"
heroku apps:info -a $app_name > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ App '$app_name' não encontrado${NC}"
    echo -e "${BLUE}💡 Use 'heroku apps' para ver seus apps disponíveis${NC}"
    exit 1
fi

# Verificar se há alterações não commitadas
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Há alterações não commitadas${NC}"
    echo -e "${BLUE}📋 Status atual:${NC}"
    git status --short
    echo ""
    read -p "Deseja fazer commit automático das alterações? (y/n): " auto_commit
    
    if [ "$auto_commit" = "y" ] || [ "$auto_commit" = "Y" ]; then
        read -p "Digite a mensagem do commit: " commit_message
        if [ -n "$commit_message" ]; then
            git add .
            git commit -m "$commit_message"
            echo -e "${GREEN}✅ Commit realizado${NC}"
        else
            echo -e "${RED}❌ Mensagem de commit é obrigatória${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️  Deploy continuará com último commit${NC}"
    fi
fi

# Fazer deploy
echo ""
echo -e "${BLUE}🚀 Iniciando deploy no Heroku...${NC}"
echo -e "${PURPLE}📡 Enviando código para $app_name...${NC}"

git push heroku main

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 Deploy realizado com sucesso!${NC}"
    
    # Executar migrações
    echo ""
    echo -e "${BLUE}🔄 Executando migrações...${NC}"
    heroku run python manage.py migrate -a $app_name
    
    # Coletar arquivos estáticos
    echo ""
    echo -e "${BLUE}📦 Coletando arquivos estáticos...${NC}"
    heroku run python manage.py collectstatic --noinput -a $app_name
    
    # Mostrar logs recentes
    echo ""
    echo -e "${BLUE}📋 Logs recentes do app:${NC}"
    heroku logs --tail -n 20 -a $app_name
    
    echo ""
    echo -e "${GREEN}✨ Deploy concluído!${NC}"
    echo -e "${BLUE}🌐 Seu app está disponível em: ${GREEN}https://$app_name.herokuapp.com${NC}"
    
else
    echo -e "${RED}❌ Erro no deploy${NC}"
    echo -e "${BLUE}📋 Verifique os logs para mais informações:${NC}"
    echo -e "${YELLOW}heroku logs --tail -a $app_name${NC}"
    exit 1
fi

# Opção para abrir o app
echo ""
read -p "Deseja abrir o app no navegador? (y/n): " open_app

if [ "$open_app" = "y" ] || [ "$open_app" = "Y" ]; then
    heroku open -a $app_name
fi

echo ""
echo -e "${GREEN}🏁 Processo finalizado!${NC}"