#!/bin/bash

echo "🔍 Testando DNS do domínio fretamentointertouring.tech..."
echo ""

echo "📡 Verificando propagação DNS..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "1️⃣  Domínio raiz (fretamentointertouring.tech):"
dig fretamentointertouring.tech +short
echo ""

echo "2️⃣  Subdomínio WWW (www.fretamentointertouring.tech):"
dig www.fretamentointertouring.tech +short
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "🌐 Testando acesso HTTP..."
echo ""

echo "3️⃣  Testando fretamentointertouring.tech:"
curl -I -L https://fretamentointertouring.tech 2>&1 | head -1
echo ""

echo "4️⃣  Testando www.fretamentointertouring.tech:"
curl -I -L https://www.fretamentointertouring.tech 2>&1 | head -1
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Se aparecer os endereços DNS do Heroku (herokudns.com), está propagado!"
echo "✅ Se o HTTP retornar 200 OK ou 301/302, está funcionando!"
echo "⏱️  Se não aparecer nada ainda, aguarde a propagação DNS (pode levar até 48h)"
