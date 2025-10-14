# 🔧 Instruções para Corrigir a Configuração DNS

## ❌ Problema Identificado

O seu domínio `fretamentointertouring.tech` está configurado incorretamente no provedor de DNS. Atualmente, ele está apontando para um IP fixo (`208.91.112.55`) em vez dos DNS targets dinâmicos do Heroku.

## ✅ Solução

Você precisa acessar o painel do seu provedor de DNS (onde registrou o domínio) e **alterar/criar** os seguintes registros:

### 1. Domínio Raiz (fretamentointertouring.tech)

**REMOVER:**
- Qualquer registro A apontando para `208.91.112.55`

**CRIAR/ALTERAR:**
- **Tipo**: ALIAS ou ANAME (dependendo do seu provedor)
- **Nome**: `@` ou deixar vazio (representa o domínio raiz)
- **Valor**: `arcane-beaver-7psequd0tj2n91fqxy4h2e73.herokudns.com`
- **TTL**: 300 (5 minutos) ou menor

### 2. Subdomínio WWW (www.fretamentointertouring.tech)

**REMOVER:**
- Qualquer registro A apontando para `208.91.112.55`

**CRIAR/ALTERAR:**
- **Tipo**: CNAME
- **Nome**: `www`
- **Valor**: `cardiovascular-weasel-6zih5pju7yb0s9t0v1c7ezmq.herokudns.com`
- **TTL**: 300 (5 minutos) ou menor

## 📋 Tipos de Registro por Provedor

### Cloudflare
- Use **CNAME** para ambos (o Cloudflare aceita CNAME no root)

### Namecheap
- Use **ALIAS** para o domínio raiz
- Use **CNAME** para www

### GoDaddy
- Use **CNAME** para ambos

### DNSimple
- Use **ALIAS** para o domínio raiz
- Use **CNAME** para www

### AWS Route 53
- Use **ALIAS** para o domínio raiz
- Use **CNAME** para www

## ⏰ Tempo de Propagação

- **Mínimo**: 5-15 minutos
- **Máximo**: 24-48 horas
- **Recomendação**: Reduza o TTL antes de fazer a alteração

## 🧪 Como Testar

Após fazer as alterações, teste com estes comandos:

```bash
# Teste o domínio raiz
nslookup fretamentointertouring.tech

# Teste o subdomínio www  
nslookup www.fretamentointertouring.tech

# Deve retornar IPs do Heroku (não 208.91.112.55)
```

## ✅ Configuração Atual do Heroku

Seus domínios já estão corretamente configurados no Heroku:

- ✅ `fretamentointertouring.tech` → `arcane-beaver-7psequd0tj2n91fqxy4h2e73.herokudns.com`
- ✅ `www.fretamentointertouring.tech` → `cardiovascular-weasel-6zih5pju7yb0s9t0v1c7ezmq.herokudns.com`
- ✅ ALLOWED_HOSTS configurado no Django
- ✅ SSL/HTTPS configurado

## 🚨 Importante

1. **NÃO use registros A** - Heroku usa IPs dinâmicos
2. **Sempre use CNAME/ALIAS** - Eles seguem as mudanças do Heroku automaticamente
3. **Remova registros antigos** - Para evitar conflitos
4. **TTL baixo** - Para propagação mais rápida

## 📞 Suporte

Se precisar de ajuda específica do seu provedor:
- Procure a documentação de "Custom Domains" ou "CNAME records"
- Entre em contato com o suporte técnico do provedor
- Mencione que precisa configurar um "CNAME para Heroku"