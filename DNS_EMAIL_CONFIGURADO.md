# ✅ DNS de Email Configurado com Sucesso!

## 📋 Registros Configurados

### Registros A (Endereços IP)
- ✅ `imap.innexar.app` → `38.100.203.70` (DNS only - sem proxy)
- ✅ `smtp.innexar.app` → `38.100.203.70` (DNS only - sem proxy)

### Registros SRV (Autodescobrimento)
- ✅ `_imaps._tcp.innexar.app` → `imap.innexar.app:993` (IMAP SSL/TLS)
- ✅ `_imap._tcp.innexar.app` → `imap.innexar.app:143` (IMAP STARTTLS)
- ✅ `_submission._tcp.innexar.app` → `smtp.innexar.app:587` (SMTP Submission)
- ✅ `_smtp._tcp.innexar.app` → `smtp.innexar.app:25` (SMTP padrão)

## 🎯 Configuração de Email

### Para Clientes de Email (Outlook, Thunderbird, Apple Mail, etc.)

**IMAP (Receber):**
- Servidor: `imap.innexar.app`
- Porta: `993`
- Segurança: SSL/TLS
- Autenticação: Normal

**SMTP (Enviar):**
- Servidor: `smtp.innexar.app`
- Porta: `587`
- Segurança: STARTTLS
- Autenticação: Normal

## ⏱️ Propagação DNS

Os registros DNS podem levar de **5 a 15 minutos** para propagar completamente.

Para verificar se já propagou:

```bash
# Verificar registros A
dig +short imap.innexar.app A
dig +short smtp.innexar.app A

# Verificar registros SRV
dig +short _imaps._tcp.innexar.app SRV
dig +short _submission._tcp.innexar.app SRV
```

## 🔧 Testar Conectividade

Após a propagação, teste a conectividade:

```bash
# Testar IMAP (porta 993)
openssl s_client -connect imap.innexar.app:993 -showcerts

# Testar SMTP (porta 587)
openssl s_client -connect smtp.innexar.app:587 -starttls smtp
```

## 📱 Autodescobrimento

Agora os clientes de email modernos (Thunderbird, Apple Mail, etc.) devem conseguir descobrir automaticamente as configurações ao adicionar uma conta `@innexar.app`.

### Thunderbird
1. Abra o Thunderbird
2. Vá em **Contas** → **Adicionar conta de email**
3. Digite: `seu-email@innexar.app`
4. Digite a senha
5. O Thunderbird deve descobrir automaticamente as configurações

### Apple Mail (macOS/iOS)
1. Abra **Preferências do Sistema** → **Internet Accounts**
2. Adicione uma conta de email
3. Digite: `seu-email@innexar.app`
4. Digite a senha
5. O macOS deve descobrir automaticamente

### Outlook
O Outlook pode precisar de configuração adicional (registro `autodiscover.innexar.app`), mas os registros SRV já ajudam.

## ⚠️ Importante

1. **Certificados SSL**: Certifique-se de que os certificados SSL estão configurados corretamente nos servidores de email (portas 993 e 587).

2. **Firewall**: Verifique se as portas estão abertas:
   - 993 (IMAPS)
   - 587 (SMTP Submission)
   - 143 (IMAP - opcional)
   - 25 (SMTP - opcional)

3. **Proxy Cloudflare**: Os registros A estão configurados como **DNS only** (sem proxy), o que é necessário para email funcionar corretamente.

## 🔄 Reconfigurar (se necessário)

Se precisar reconfigurar, execute:

```bash
cd /projetos/innexar-crm
./configurar_email_dns_cloudflare.sh
```

## 📚 Documentação

Veja também: `/projetos/innexar-crm/CONFIGURACAO_EMAIL_DNS.md`

