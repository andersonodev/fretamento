#!/bin/bash

echo "=== TESTE CURL PARA AGRUPAMENTO ==="

# Primeiro, fazer GET para obter o token CSRF
echo "1. Obtendo token CSRF..."
CSRF_TOKEN=$(curl -s -c cookies.txt http://localhost:8000/escalas/visualizar/07-10-2025/ | grep 'name="csrfmiddlewaretoken"' | sed 's/.*value="\([^"]*\)".*/\1/')

if [ -z "$CSRF_TOKEN" ]; then
    echo "❌ Erro: Não foi possível obter o token CSRF"
    echo "Tentando método alternativo..."
    CSRF_TOKEN=$(curl -s -c cookies.txt http://localhost:8000/escalas/visualizar/07-10-2025/ | grep -o 'csrfmiddlewaretoken[^>]*value="[^"]*"' | grep -o 'value="[^"]*"' | cut -d'"' -f2)
fi

if [ -z "$CSRF_TOKEN" ]; then
    echo "❌ Erro: Ainda não foi possível obter o token CSRF"
    exit 1
fi

echo "✅ Token CSRF obtido: $CSRF_TOKEN"

# Fazer POST para testar
echo ""
echo "2. Enviando POST para teste..."
RESPONSE=$(curl -s -b cookies.txt -c cookies.txt \
    -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "csrfmiddlewaretoken=$CSRF_TOKEN&acao=teste" \
    -w "HTTPCODE:%{http_code}\n" \
    http://localhost:8000/escalas/visualizar/07-10-2025/)

echo "📊 Resposta completa:"
echo "$RESPONSE"

echo ""
echo "3. Enviando POST para agrupamento..."
RESPONSE2=$(curl -s -b cookies.txt -c cookies.txt \
    -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "csrfmiddlewaretoken=$CSRF_TOKEN&acao=agrupar" \
    -w "HTTPCODE:%{http_code}\n" \
    http://localhost:8000/escalas/visualizar/07-10-2025/)

echo "📊 Resposta agrupamento:"
echo "$RESPONSE2"

# Limpar cookies
rm -f cookies.txt