#!/bin/bash

echo "=== TESTE DIAGNÓSTICO COMPLETO ==="

echo "1. Verificando se precisa de login..."
STATUS=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:8000/escalas/visualizar/07-10-2025/)
echo "Status HTTP: $STATUS"

if [ "$STATUS" = "302" ]; then
    echo "❌ Redirecionamento detectado - provavelmente precisa de login"
    echo ""
    echo "📋 Instruções:"
    echo "1. Acesse: http://localhost:8000/auth/login/"
    echo "2. Faça login no navegador"
    echo "3. Depois acesse: http://localhost:8000/escalas/visualizar/07-10-2025/"
    echo "4. Teste os botões 'Teste' e 'Agrupar'"
    echo ""
    echo "🔍 Se você já está logado, verifique:"
    echo "- Se a sessão expirou"
    echo "- Se há cookies bloqueados"
    echo "- Se precisa fazer login novamente"
else
    echo "✅ Acesso direto permitido - Status: $STATUS"
fi

echo ""
echo "=== VERIFICANDO LOGS DO SERVIDOR ==="
echo "Verifique o terminal onde o Django está rodando para ver logs como:"
echo "🔥 POST CHAMADO! VisualizarEscalaView"
echo "🟢 GET CHAMADO! VisualizarEscalaView"