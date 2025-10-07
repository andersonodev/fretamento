# Guia de Deploy com SQLite

## 1. Preparar Ambiente

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2. Variáveis de Ambiente

Crie um arquivo `.env` (ou configure no serviço de deploy) com pelo menos:

```env
DJANGO_SECRET_KEY=uma-chave-secreta-segura
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=seu-dominio.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
```

Outras opções disponíveis estão documentadas em [Segurança](security.md).

## 3. Migrar Banco de Dados

```bash
python manage.py migrate
python manage.py createsuperuser
```

## 4. Coletar Arquivos Estáticos

```bash
python manage.py collectstatic --no-input
```

WhiteNoise cuidará da entrega dos arquivos coletados em `staticfiles/`.

## 5. Executar Checks do Django

```bash
python manage.py check --deploy
```

Ajuste eventuais avisos antes do deploy final.

## 6. Servir a Aplicação

Para um ambiente simples com Gunicorn:

```bash
gunicorn fretamento_project.wsgi:application --bind 0.0.0.0:8000
```

Configure um serviço de supervisão (systemd, pm2, etc.) e um proxy reverso (Nginx/Caddy) para HTTPS.

## 7. Backups

- Faça cópias versionadas do arquivo `db.sqlite3`.
- Armazene o diretório `media/` se houver upload de arquivos.

Pronto! O sistema estará disponível com otimizações de performance e segurança habilitadas por padrão.
