#!/bin/bash
# Script para autom# Comando opcional para backup do banco de dados (antes de grandes mudanças)
echo "# mysqldump -u ${USERNAME} -p'1907@@Jr' -h ${USERNAME}.mysql.pythonanywhere-services.com \"${DB_NAME}\" > ~/db_backup_$(date +%Y%m%d).sql"izar o deploy no PythonAnywhere
# Salve este script localmente e execute antes de fazer push para o repositório

echo "Preparando deploy para PythonAnywhere..."

# Configuração
USERNAME="andersonodev"  # Nome de usuário no PythonAnywhere
PROJECT_NAME="fretamento-intertouring"
GIT_REPO="https://github.com/andersonodev/fretamento.git"
DB_NAME="andersonodev\$fretamento_intertouring"  # Nome do banco de dados MySQL

# Gerar comandos para serem executados no PythonAnywhere via SSH ou API
echo "Execute os seguintes comandos no console Bash do PythonAnywhere:"
echo "---------------------------------------------------------"
echo "# Atualizar o código via Git"
echo "cd ~/${PROJECT_NAME}"
echo "git pull"
echo ""
echo "# Ativar ambiente virtual"
echo "source ~/fretamento-venv/bin/activate"
echo ""
echo "# Instalar/atualizar dependências (incluindo MySQL)"
echo "pip install -r requirements-mysql.txt"
echo ""
echo "# Verificar estrutura do banco de dados MySQL e executar migrações"
echo "python manage.py migrate --settings=fretamento_project.settings_pythonanywhere"
echo ""
echo "# Coletar arquivos estáticos"
echo "python manage.py collectstatic --no-input --settings=fretamento_project.settings_pythonanywhere"
echo ""
echo "# Comando opcional para backup do banco de dados (antes de grandes mudanças)"
echo "# mysqldump -u ${USERNAME} -h ${USERNAME}.mysql.pythonanywhere-services.com \"${DB_NAME}\" > ~/db_backup_$(date +%Y%m%d).sql"
echo ""
echo "# Reiniciar a aplicação web"
echo "touch /var/www/${USERNAME}_pythonanywhere_com_wsgi.py"
echo "---------------------------------------------------------"

echo "Lembre-se de verificar o log de erros após o deploy em:"
echo "https://www.pythonanywhere.com/user/${USERNAME}/webapps/${USERNAME}.pythonanywhere.com/logs/"

echo "Deploy preparado com sucesso!"