# Permissões Cloudflare API Token - Versão Atualizada (2025)

## ✅ Permissões Corretas (Documentação Oficial)

### Account Permissions (Account →)

Para nosso sistema, você precisa das seguintes permissões de **Account**:

1. **Workers Scripts** → **Write**
   - Permite criar, editar e deletar Workers scripts
   - Necessário para Workers AI

2. **Workers AI** → **Write**
   - Permite usar Workers AI (modelos de IA)
   - Necessário para geração de sites via IA

3. **Workers R2 Storage** → **Write**
   - Permite criar, editar e deletar buckets R2
   - Permite upload/download de objetos
   - Necessário para armazenar assets

4. **Pages** → **Write**
   - Permite criar, editar e deletar projetos Pages
   - Permite fazer deploy
   - Necessário para preview automático

5. **Account Settings** → **Read** (Opcional)
   - Permite ler informações da conta
   - Útil para validações

### Zone Permissions (Zone →)

Para nosso sistema, você precisa das seguintes permissões de **Zone**:

1. **DNS** → **Write**
   - Permite criar, editar e deletar registros DNS
   - Necessário para criar subdomínios automaticamente

2. **Zone** → **Read** (Opcional)
   - Permite ler informações da zone
   - Útil para validações

---

## 📋 Passo a Passo Atualizado

### 1. Criar Token Customizado

1. Acesse: https://dash.cloudflare.com/profile/api-tokens
2. Clique em **"Create Token"**
3. Selecione **"Create Custom Token"**

### 2. Configurar Permissões

#### Account Permissions

Adicione estas permissões na seção **"Account"**:

- ✅ **Workers Scripts** → **Write**
- ✅ **Workers AI** → **Write**
- ✅ **Workers R2 Storage** → **Write**
- ✅ **Pages** → **Write**
- ✅ **Account Settings** → **Read** (opcional)

#### Zone Permissions

Adicione estas permissões na seção **"Zone"**:

- ✅ **DNS** → **Write**
- ✅ **Zone** → **Read** (opcional)

### 3. Configurar Recursos

#### Account Resources

- Selecione sua conta (ou "Include - All accounts")

#### Zone Resources

- **Opção 1**: "Include - All zones" (mais simples)
- **Opção 2**: Selecione zonas específicas (mais seguro)

### 4. Finalizar

1. Clique em **"Continue to summary"**
2. Revise as permissões
3. Clique em **"Create Token"**
4. **COPIE O TOKEN** imediatamente!

---

## 🔍 Verificar Permissões

Após criar o token, você pode testar:

```bash
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

Se retornar `"status": "active"`, o token está funcionando!

---

## ⚠️ Notas Importantes

1. **Workers Scripts Write** ≠ "Workers Edit" (não existe mais)
2. **Pages Write** ≠ "Pages Edit" (não existe mais)
3. **Workers R2 Storage Write** é diferente de criar tokens R2 separados
4. O token de Account cobre Workers AI, Pages e R2
5. Para R2, você ainda precisa criar **API Token R2** separado (para S3-compatible access)

---

## 🎯 Resumo Rápido

**Token Principal (Account API Token)**:
- Workers Scripts Write
- Workers AI Write
- Workers R2 Storage Write
- Pages Write
- DNS Write (Zone)

**Token R2 Separado** (para S3-compatible):
- Criar em: R2 Dashboard → Manage R2 API Tokens
- Permissions: Object Read & Write

---

## ✅ Checklist

- [ ] Token criado com permissões corretas
- [ ] Account ID copiado
- [ ] Token testado e funcionando
- [ ] Configurado no sistema (`/settings` → Integrations)
