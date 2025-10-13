#!/usr/bin/env python
"""
Teste rápido de HTTP request
"""
import subprocess
import sys

# Teste usando curl
test_script = '''
echo "🔐 Testando login..."

# 1. Obter página de login e extrair CSRF
echo "1. Obtendo CSRF token..."
RESPONSE=$(curl -s -c cookies.txt "https://fretamento-intertouring-app-ca2ff72f9735.herokuapp.com/auth/login/")
CSRF_TOKEN=$(echo "$RESPONSE" | grep -o 'name="csrfmiddlewaretoken" value="[^"]*"' | sed 's/.*value="\\([^"]*\\)".*/\\1/')

if [ -z "$CSRF_TOKEN" ]; then
    echo "❌ CSRF token não encontrado"
    exit 1
fi

echo "   CSRF Token: ${CSRF_TOKEN:0:20}..."

# 2. Fazer login
echo "2. Fazendo login..."
LOGIN_RESPONSE=$(curl -s -b cookies.txt -c cookies.txt \
    -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "Referer: https://fretamento-intertouring-app-ca2ff72f9735.herokuapp.com/auth/login/" \
    -d "username=anderson&password=senha123&csrfmiddlewaretoken=$CSRF_TOKEN" \
    -w "HTTPSTATUS:%{http_code};REDIRECT:%{redirect_url}" \
    "https://fretamento-intertouring-app-ca2ff72f9735.herokuapp.com/auth/login/")

HTTP_STATUS=$(echo "$LOGIN_RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
REDIRECT_URL=$(echo "$LOGIN_RESPONSE" | grep -o "REDIRECT:[^;]*" | cut -d: -f2-)

echo "   Status: $HTTP_STATUS"
echo "   Redirect: $REDIRECT_URL"

if [ "$HTTP_STATUS" = "302" ]; then
    echo "✅ Login funcionando! Redirecionamento para: $REDIRECT_URL"
else
    echo "❌ Login falhou com status: $HTTP_STATUS"
fi

# Limpeza
rm -f cookies.txt
'''

print("Executando teste de login via curl...")
result = subprocess.run(['bash', '-c', test_script], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("Stderr:", result.stderr)