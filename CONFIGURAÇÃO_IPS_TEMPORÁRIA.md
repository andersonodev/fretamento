# 🔧 CONFIGURAÇÃO TEMPORÁRIA COM IPs

## Para configurar AGORA no seu provedor (MyOrderBox):

### 1. Domínio Raiz (fretamentointertouring.tech)
Como seu provedor só aceita registro A, use:

**Configuração no painel:**
- **Tipo**: A (Address Record)
- **Host Name**: @ (ou deixe vazio)
- **Destination IPv4 Address**: `99.83.220.108`
- **TTL**: 300 (5 minutos)

### 2. Subdomínio WWW
- **Tipo**: CNAME
- **Host Name**: www
- **Destination**: `cardiovascular-weasel-6zih5pju7yb0s9t0v1c7ezmq.herokudns.com`
- **TTL**: 300

## 🚨 IPs ADICIONAIS (Opcional)

Se seu provedor permitir múltiplos registros A, adicione também:
- `13.248.244.96`
- `35.71.179.82` 
- `75.2.60.68`

## ⚠️ IMPORTANTE

Esta é uma **solução temporária**. Os IPs do Heroku podem mudar e seu site ficará fora do ar. 

**Monitore seu site diariamente** e considere migrar para um provedor DNS melhor como Cloudflare.

## 🧪 COMO TESTAR

Execute estes comandos para verificar:

```bash
# Verificar se está funcionando
nslookup fretamentointertouring.tech

# Deve retornar um dos IPs: 99.83.220.108, 13.248.244.96, 35.71.179.82, ou 75.2.60.68
```

## 📞 PRÓXIMOS PASSOS

1. **Configure conforme acima**
2. **Aguarde 5-15 minutos** para propagação
3. **Teste o site**: https://fretamentointertouring.tech
4. **Considere migrar para Cloudflare** para uma solução permanente