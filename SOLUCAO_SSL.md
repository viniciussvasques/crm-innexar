# 🔧 Solução para Erro SSL - api.sales.innexar.app

## 📋 Status Atual

✅ **DNS Configurado**: `api.sales.innexar.app` aponta para Cloudflare  
✅ **Certificado Gerado**: Certificado está no `acme.json` do Traefik  
✅ **Backend Funcionando**: Backend está rodando corretamente  
❌ **SSL Handshake Falhando**: Erro `ERR_SSL_VERSION_OR_CIPHER_MISMATCH`

## 🔍 Diagnóstico

O erro `TLS connect error: error:0A000410:SSL routines::ssl/tls alert handshake failure` indica que:

1. O certificado foi gerado com sucesso
2. O Traefik tem o certificado no `acme.json`
3. Mas o handshake SSL está falhando

## 💡 Possíveis Causas

### 1. Cloudflare Proxy Interferindo
Como o DNS está com proxy Cloudflare ativado (nuvem laranja), o SSL pode estar sendo terminado no Cloudflare e não no Traefik. Isso pode causar conflitos.

### 2. Certificado Não Sendo Aplicado
O Traefik pode não estar aplicando o certificado corretamente para o domínio `api.sales.innexar.app`.

### 3. Configuração do Traefik
Pode haver um problema na configuração do Traefik para este domínio específico.

## 🛠️ Soluções

### Opção 1: Desativar Proxy Cloudflare para API (Recomendado)

1. Acesse o Cloudflare Dashboard
2. Vá em DNS → Records
3. Encontre o registro `api.sales` (tipo A)
4. **Clique no ícone laranja (nuvem)** para desativar o proxy
5. Deve ficar **cinza** (DNS only)
6. Salve

Isso permite que o SSL seja terminado diretamente no Traefik.

### Opção 2: Verificar Configuração do Traefik

Verificar se o Traefik está detectando o serviço corretamente:

```bash
docker logs traefik | grep -i "api.sales"
docker logs traefik | grep -i "crm-api"
```

### Opção 3: Forçar Renovação do Certificado

```bash
# Parar Traefik
docker stop traefik

# Remover certificado específico do acme.json (fazer backup antes!)
# Ou limpar todo o acme.json para forçar renovação

# Reiniciar Traefik
docker start traefik
```

## ✅ Verificação

Após aplicar a solução, verificar:

```bash
# Testar HTTP (deve redirecionar para HTTPS)
curl -I http://api.sales.innexar.app

# Testar HTTPS
curl -I https://api.sales.innexar.app

# Verificar certificado
openssl s_client -connect api.sales.innexar.app:443 -servername api.sales.innexar.app
```

## 📝 Nota

O frontend (`sales.innexar.app`) está funcionando porque provavelmente o Cloudflare está terminando o SSL corretamente. Para a API, é melhor desativar o proxy Cloudflare para que o Traefik gerencie o SSL diretamente.

