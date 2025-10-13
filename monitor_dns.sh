#!/bin/bash

echo "🔄 Monitoramento DNS - fretamentointertouring.tech"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Função para testar DNS
test_dns() {
    echo "⏰ $(date '+%H:%M:%S') - Testando DNS..."
    
    # Teste 1: nslookup
    echo -n "📡 DNS Resolução: "
    if nslookup fretamentointertouring.tech 8.8.8.8 >/dev/null 2>&1; then
        echo "✅ RESOLVEU"
        IP=$(nslookup fretamentointertouring.tech 8.8.8.8 | grep "Address:" | tail -1 | awk '{print $2}')
        echo "   🌐 IP: $IP"
    else
        echo "❌ NÃO RESOLVEU"
    fi
    
    # Teste 2: HTTP
    echo -n "🔗 HTTP Resposta: "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 https://fretamentointertouring.tech 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
        echo "✅ $HTTP_CODE"
    elif [ -z "$HTTP_CODE" ] || [ "$HTTP_CODE" = "000" ]; then
        echo "❌ SEM CONEXÃO"
    else
        echo "⚠️  $HTTP_CODE"
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# Função para monitorar continuamente
monitor_continuous() {
    echo "🔁 Iniciando monitoramento contínuo (pressione Ctrl+C para parar)..."
    echo ""
    
    while true; do
        test_dns
        sleep 30  # Testa a cada 30 segundos
    done
}

# Função para teste único
test_once() {
    test_dns
    echo "💡 Para monitoramento contínuo, execute: $0 monitor"
}

# Main
case "${1:-once}" in
    "monitor")
        monitor_continuous
        ;;
    "once")
        test_once
        ;;
    *)
        echo "Uso: $0 [once|monitor]"
        echo "  once    - Teste único (padrão)"
        echo "  monitor - Monitoramento contínuo"
        ;;
esac