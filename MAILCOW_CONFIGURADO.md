# ✅ Mailcow Configurado para imap.innexar.app e smtp.innexar.app

## 📋 Configuração Aplicada

### 1. DNS Configurado
- ✅ `imap.innexar.app` → `38.100.203.70` (porta 993)
- ✅ `smtp.innexar.app` → `38.100.203.70` (porta 587)
- ✅ Registros SRV para autodescobrimento configurados

### 2. Mailcow Configurado
- ✅ `ADDITIONAL_SAN=imap.innexar.app,smtp.innexar.app` adicionado ao `mailcow.conf`
- ✅ Certificados SSL sendo gerados para os novos domínios
- ✅ Portas expostas corretamente:
  - IMAP: 143, 993
  - SMTP: 25, 465, 587

## 🔧 Status dos Serviços

### Dovecot (IMAP)
- Porta 993 (IMAPS) - SSL/TLS
- Porta 143 (IMAP) - STARTTLS
- Hostname: `mail.innexar.app`
- Aceita conexões em: `imap.innexar.app`

### Postfix (SMTP)
- Porta 587 (Submission) - STARTTLS
- Porta 465 (SMTPS) - SSL/TLS
- Porta 25 (SMTP) - STARTTLS
- Hostname: `mail.innexar.app`
- Aceita conexões em: `smtp.innexar.app`

## 📧 Configuração de Email

### Para Clientes de Email

**IMAP (Receber):**
- Servidor: `imap.innexar.app`
- Porta: `993`
- Segurança: SSL/TLS
- Usuário: `seu-email@innexar.app`
- Senha: (senha da conta)

**SMTP (Enviar):**
- Servidor: `smtp.innexar.app`
- Porta: `587`
- Segurança: STARTTLS
- Usuário: `seu-email@innexar.app`
- Senha: (senha da conta)

## ✅ Verificação

Para verificar se está funcionando:

```bash
# Testar IMAP
openssl s_client -connect imap.innexar.app:993 -servername imap.innexar.app

# Testar SMTP
openssl s_client -connect smtp.innexar.app:587 -starttls smtp -servername smtp.innexar.app
```

## 🔄 Próximos Passos

1. **Aguardar geração de certificados** (pode levar alguns minutos)
2. **Verificar certificados**:
   ```bash
   cd /projetos/mailcow
   docker compose logs acme-mailcow | grep -i "imap\|smtp\|certificate"
   ```
3. **Testar conectividade** com um cliente de email
4. **Criar contas de email** no painel do Mailcow (se ainda não criou)

## 📝 Notas

- O Mailcow aceita conexões em qualquer domínio que aponte para o servidor
- Os certificados SSL são necessários para evitar avisos de segurança
- O autodescobrimento funciona automaticamente com os registros SRV configurados

