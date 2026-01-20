# 📧 Configuração DNS para Autodescobrimento de Email

## 🎯 Objetivo

Configurar registros DNS para facilitar o autodescobrimento de email, permitindo que clientes de email (Outlook, Thunderbird, Apple Mail, etc.) configurem automaticamente as contas.

## 📋 Registros DNS Necessários

### 1. Registros A (Endereços IP)

```
imap.innexar.app    → IP do servidor (sem proxy Cloudflare)
smtp.innexar.app    → IP do servidor (sem proxy Cloudflare)
```

### 2. Registros SRV (Autodescobrimento)

```
_imaps._tcp.innexar.app        → imap.innexar.app:993 (IMAP SSL/TLS)
_imap._tcp.innexar.app         → imap.innexar.app:143 (IMAP STARTTLS - opcional)
_submission._tcp.innexar.app   → smtp.innexar.app:587 (SMTP Submission STARTTLS)
_smtp._tcp.innexar.app         → smtp.innexar.app:25 (SMTP - opcional)
```

### 3. Registros MX (Mail Exchange) - Se necessário

Se você usar `@innexar.app` como domínio de email:

```
innexar.app    MX    10    mail.innexar.app
```

## 🚀 Como Configurar

### Opção 1: Script Automático (Recomendado)

```bash
cd /projetos/innexar-crm

# Configure as variáveis de ambiente
export CLOUDFLARE_API_TOKEN='seu-token-aqui'
export CLOUDFLARE_EMAIL='seu-email@example.com'

# Execute o script
./configurar_email_dns_cloudflare.sh
```

### Opção 2: Manual no Cloudflare

1. Acesse o painel do Cloudflare
2. Selecione o domínio `innexar.app`
3. Vá em **DNS** → **Records**

#### Adicionar Registros A:

| Type | Name | IPv4 address | Proxy status | TTL |
|------|------|--------------|--------------|-----|
| A | imap | [IP do servidor] | DNS only (cinza) | Auto |
| A | smtp | [IP do servidor] | DNS only (cinza) | Auto |

#### Adicionar Registros SRV:

| Type | Name | Service | Protocol | Priority | Weight | Port | Target | TTL |
|------|------|---------|----------|----------|--------|------|--------|-----|
| SRV | _imaps._tcp | imaps | tcp | 10 | 5 | 993 | imap.innexar.app | Auto |
| SRV | _submission._tcp | submission | tcp | 10 | 5 | 587 | smtp.innexar.app | Auto |

## ✅ Verificação

Após configurar, aguarde alguns minutos e verifique:

```bash
# Verificar registros A
dig +short imap.innexar.app A
dig +short smtp.innexar.app A

# Verificar registros SRV
dig +short _imaps._tcp.innexar.app SRV
dig +short _submission._tcp.innexar.app SRV
```

## 📱 Como Funciona o Autodescobrimento

### Outlook / Microsoft 365
- Usa registros SRV `_autodiscover._tcp.innexar.app` (pode ser necessário adicionar)
- Também tenta `autodiscover.innexar.app`

### Thunderbird
- Usa registros SRV `_imaps._tcp` e `_submission._tcp`
- Funciona automaticamente após configurar os registros

### Apple Mail (macOS/iOS)
- Usa registros SRV e também tenta autodescobrimento via HTTPS
- Pode precisar de `autodiscover.innexar.app` também

### Gmail / Google Workspace
- Não usa autodescobrimento, mas os registros ajudam na validação

## 🔧 Configuração Adicional (Opcional)

### Autodiscover para Outlook

Se quiser suporte completo ao Outlook, adicione:

```
autodiscover.innexar.app    A    [IP do servidor]
```

E configure um servidor web respondendo em:
- `https://autodiscover.innexar.app/autodiscover/autodiscover.xml`

### Registros TXT para Validação

Para melhor validação, adicione registros TXT:

```
_inbox._tcp.innexar.app    TXT    "imap=imap.innexar.app:993"
_submission._tcp.innexar.app    TXT    "smtp=smtp.innexar.app:587"
```

## ⚠️ Importante

1. **Proxy Cloudflare**: Configure os registros A como **DNS only** (cinza), não como **Proxied** (laranja), pois o proxy não funciona com email.

2. **Portas**: Certifique-se de que as portas estão abertas no firewall:
   - 993 (IMAPS)
   - 587 (SMTP Submission)
   - 143 (IMAP - opcional)
   - 25 (SMTP - opcional)

3. **Propagação**: Aguarde 5-15 minutos para a propagação DNS.

4. **SSL/TLS**: Certifique-se de que os certificados SSL estão configurados corretamente nos servidores de email.

## 🧪 Teste de Configuração

Após configurar, teste com:

```bash
# Testar conectividade IMAP
openssl s_client -connect imap.innexar.app:993 -showcerts

# Testar conectividade SMTP
openssl s_client -connect smtp.innexar.app:587 -starttls smtp
```

## 📚 Referências

- [RFC 6186 - Use of SRV Records for Locating Email Submission/Access Services](https://tools.ietf.org/html/rfc6186)
- [Cloudflare DNS API](https://developers.cloudflare.com/api/operations/dns-records-for-a-zone-create-dns-record)

