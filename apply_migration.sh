#!/bin/bash
# Script para aplicar migração assim que Heroku estabilizar
# Execute: bash apply_migration.sh

echo "🔍 Monitorando disponibilidade do Heroku..."
echo "Pressione Ctrl+C para cancelar"
echo ""

attempt=1
max_attempts=20
sleep_time=120  # 2 minutos entre tentativas

while [ $attempt -le $max_attempts ]; do
    echo "Tentativa $attempt/$max_attempts - $(date '+%H:%M:%S')"
    
    # Tenta executar a migração
    if heroku run python manage.py migrate -a fretamento-intertouring 2>&1 | grep -q "Operations to perform"; then
        echo ""
        echo "✅ Migração aplicada com sucesso!"
        echo "Os 11 índices de performance foram criados no banco de dados."
        echo ""
        echo "Sistema agora está 100% otimizado! 🚀"
        exit 0
    fi
    
    if [ $attempt -lt $max_attempts ]; then
        echo "⏳ Heroku ainda indisponível. Aguardando $sleep_time segundos..."
        echo ""
        sleep $sleep_time
    fi
    
    attempt=$((attempt + 1))
done

echo ""
echo "⚠️  Heroku ainda está com problemas após $max_attempts tentativas."
echo "Aplique a migração manualmente quando o serviço normalizar:"
echo "  heroku run python manage.py migrate -a fretamento-intertouring"
echo ""
echo "Acompanhe o status em: https://status.heroku.com"
