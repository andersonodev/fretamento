#!/bin/bash

echo "🔄 Monitorando propagação DNS para fretamentointertouring.tech"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

while true; do
    echo "⏰ $(date '+%H:%M:%S') - Testando..."
    
    # Teste WWW
    WWW_RESULT=$(nslookup www.fretamentointertouring.tech 8.8.8.8 2>/dev/null | grep "canonical name")
    if [[ $WWW_RESULT == *"herokudns.com"* ]] && [[ $WWW_RESULT != *"fretamentointertouring.tech."* ]]; then
        echo "✅ WWW: DNS correto propagado!"
        
        # Teste HTTP
        HTTP_RESULT=$(curl -s -I https://www.fretamentointertouring.tech 2>&1 | head -1)
        if [[ $HTTP_RESULT == *"HTTP"* ]]; then
            echo "🎉 HTTP: Funcionando! $HTTP_RESULT"
            echo ""
            echo "🚀 SUCESSO! Seu domínio está funcionando:"
            echo "   https://www.fretamentointertouring.tech"
            break
        else
            echo "⏳ HTTP: Ainda propagando..."
        fi
    else
        echo "⏳ WWW: Ainda propagando DNS..."
    fi
    
    # Teste domínio raiz
    ROOT_RESULT=$(nslookup fretamentointertouring.tech 8.8.8.8 2>/dev/null | grep "Address:")
    if [[ $ROOT_RESULT == *"99.83.220.108"* ]]; then
        echo "✅ ROOT: DNS correto!"
    else
        echo "⏳ ROOT: Ainda propagando..."
    fi
    
    echo ""
    sleep 30
done