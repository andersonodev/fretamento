# Segurança e Boas Práticas

## Configurações de Ambiente

- `DJANGO_SECRET_KEY`: chave secreta carregada via variável de ambiente.
- `DJANGO_DEBUG`: controla o modo debug.
- `DJANGO_ALLOWED_HOSTS`: lista separada por vírgula de hosts permitidos.
- `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SECURE_HSTS_SECONDS`: ajustes finos para ambientes com HTTPS.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: origens confiáveis adicionais para requisições CSRF.

## Proteções Ativadas

- Cookies de sessão e CSRF marcados como `HttpOnly` e `SameSite=Lax`.
- `SESSION_COOKIE_SECURE` e `CSRF_COOKIE_SECURE` ativados automaticamente em produção.
- `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_BROWSER_XSS_FILTER` e `X_FRAME_OPTIONS='DENY'`.
- `SECURE_PROXY_SSL_HEADER` configurado para ambientes atrás de proxy reverso.
- Limite de upload padrão (`DATA_UPLOAD_MAX_MEMORY_SIZE`) reduzido para 10 MB (configurável via env).

## Arquivos Estáticos e Deploy

- WhiteNoise habilitado em `MIDDLEWARE` e `STORAGES` para servir arquivos estáticos comprimidos.
- `ATOMIC_REQUESTS` ligado no SQLite para garantir consistência em operações transacionais.

## Recomendações Adicionais

- Utilizar `python -m pip install -r requirements.txt` em ambientes isolados (virtualenv/venv).
- Configurar HTTPS completo (com HSTS elevado) em produção.
- Definir rotação periódica para `DJANGO_SECRET_KEY` e renovar tokens de usuários administradores.
- Manter backups do banco SQLite (snapshot do arquivo `db.sqlite3`) com versionamento seguro.
