# Guia de Configuração - Cloudflare

## 📋 Passo a Passo

### 1. Cloudflare Base (Obrigatório)

#### 1.1 Obter Account ID

1. Acesse: https://dash.cloudflare.com/
2. Faça login na sua conta
3. Selecione o domínio (ou qualquer domínio)
4. Na barra lateral direita, você verá **"Account ID"**
5. Copie o Account ID (formato: `8d9e1234567890abcdef`)

#### 1.2 Criar API Token

**Opção A: Usar Template (Recomendado)**

1. Acesse: https://dash.cloudflare.com/profile/api-tokens
2. Clique em **"Create Token"**
3. Selecione o template **"Editar Cloudflare Workers"** → **"Usar modelo"**
4. O template já adiciona automaticamente:
   - ✅ **Workers Scripts** → **Write**
   - ✅ **Workers R2 Storage** → **Write**
   - ✅ **Workers KV Storage** → **Write**
   - ✅ **Account Settings** → **Read**
5. **ADICIONE MANUALMENTE** (clique em "+ Adicionar mais"):
   - ✅ **Account** → **Pages** → **Write** (para Cloudflare Pages)
   - ✅ **Account** → **Workers AI** → **Write** (para Workers AI, se necessário)
   - ✅ **Zone** → **DNS** → **Write** (para gerenciar DNS)
   - ✅ **Zone** → **Zone** → **Read** (opcional, mas útil)

**Opção B: Token Customizado (Manual)**

1. Acesse: https://dash.cloudflare.com/profile/api-tokens
2. Clique em **"Create Token"**
3. Selecione **"Create Custom Token"**
4. Configure as permissões:

   **Account Permissions** (Account →):
   - ✅ **Workers Scripts** → **Write** (para Workers)
   - ✅ **Workers AI** → **Write** (para Workers AI)
   - ✅ **Workers R2 Storage** → **Write** (para R2)
   - ✅ **Pages** → **Write** (para Cloudflare Pages)
   - ✅ **Account Settings** → **Read** (opcional, mas útil)

   **Zone Permissions** (Zone →):
   - ✅ **DNS** → **Write** (para gerenciar DNS)
   - ✅ **Zone** → **Read** (para ler informações da zone)

5. **Account Resources**: Selecione sua conta
6. **Zone Resources**: Selecione "Include - All zones" ou zonas específicas
7. Clique em **"Continue to summary"**
8. Revise e clique em **"Create Token"**
9. **COPIE O TOKEN** (só aparece uma vez!)

#### 1.3 Configurar no Sistema

1. Vá para `/settings` → Aba **"Integrations"**
2. Na seção **"Cloudflare Base Configuration"**:
   - Cole o **Account ID** no campo "Account ID"
   - Cole o **API Token** no campo "API Token"
3. Clique em **"Save All Integrations"**

---

### 2. Cloudflare Pages (Para Preview Automático)

#### 2.1 Obter Informações

**Account ID**: Use o mesmo do passo 1.1

**Project Template**: 
- Padrão: `site-{order_id}`
- Isso criará projetos como: `site-24`, `site-25`, etc.

#### 2.2 Configurar no Sistema

1. Na seção **"Cloudflare Pages"**:
   - Deixe o **Project Name Template** como `site-{order_id}` (ou customize)
2. Clique em **"Save All Integrations"**

**Nota**: O API Token do Cloudflare Base já cobre Pages, não precisa de token separado.

---

### 3. Cloudflare R2 Storage (Para Assets)

#### 3.1 Criar Bucket R2

1. Acesse: https://dash.cloudflare.com/
2. No menu lateral, clique em **"R2"**
3. Clique em **"Create bucket"**
4. Escolha um nome (ex: `innexar-assets`)
5. Escolha a localização
6. Clique em **"Create bucket"**

#### 3.2 Criar API Token R2

1. Ainda na página R2, clique em **"Manage R2 API Tokens"**
2. Clique em **"Create API token"**
3. Escolha:
   - **Permissions**: Object Read & Write
   - **TTL**: Sem expiração (ou conforme necessário)
4. Clique em **"Create API Token"**
5. **COPIE**:
   - **Access Key ID**
   - **Secret Access Key**

#### 3.3 Obter Endpoint URL

1. Na página do bucket, procure por **"S3 API"** ou **"Endpoint"**
2. O endpoint geralmente é: `https://{account_id}.r2.cloudflarestorage.com`
3. Ou use o formato: `https://{account_id}.r2.cloudflarestorage.com`

**Alternativa**: Se não encontrar, use:
```
https://{seu_account_id}.r2.cloudflarestorage.com
```

#### 3.4 Configurar no Sistema

1. Na seção **"Cloudflare R2 Storage"**:
   - **Bucket Name**: Nome do bucket criado (ex: `innexar-assets`)
   - **Endpoint URL**: `https://{account_id}.r2.cloudflarestorage.com` (substitua `{account_id}`)
   - **Access Key ID**: Cole o Access Key ID
   - **Secret Access Key**: Cole o Secret Access Key
2. Clique em **"Save All Integrations"**

---

### 4. Cloudflare DNS (Para Subdomínios)

#### 4.1 Obter Zone ID

1. Acesse: https://dash.cloudflare.com/
2. Selecione o domínio (ex: `innexar.com`)
3. Na barra lateral direita, você verá **"Zone ID"**
4. Copie o Zone ID (formato: `1234567890abcdef1234567890abcdef`)

#### 4.2 Configurar no Sistema

1. Na seção **"Cloudflare DNS"**:
   - Cole o **Zone ID** no campo "Zone ID"
2. Clique em **"Save All Integrations"**

**Nota**: O API Token do Cloudflare Base já cobre DNS, não precisa de token separado.

---

## ✅ Checklist de Configuração

### Obrigatório
- [ ] Cloudflare Base: Account ID ✅
- [ ] Cloudflare Base: API Token ✅

### Recomendado (Para Funcionalidade Completa)
- [ ] Cloudflare Pages: Project Template
- [ ] Cloudflare R2: Bucket + Credentials
- [ ] Cloudflare DNS: Zone ID

### Opcional
- [ ] AWS S3 (se não usar R2)

---

## 🔍 Verificar Configuração

### Testar Conexões

1. Na página de Settings, cada seção tem um botão **"Test"**
2. Clique em cada botão para verificar:
   - ✅ GitHub: Test Connection
   - ✅ Cloudflare Pages: Test
   - ✅ Cloudflare R2: Test
   - ✅ Cloudflare DNS: Test

### Se os Testes Falharem

**Cloudflare Base**:
- Verifique se Account ID está correto
- Verifique se API Token tem permissões corretas
- Verifique se Token não expirou

**Cloudflare R2**:
- Verifique se bucket existe
- Verifique se Access Key ID e Secret estão corretos
- Verifique se Endpoint URL está no formato correto

**Cloudflare DNS**:
- Verifique se Zone ID está correto
- Verifique se API Token tem permissão de DNS

---

## 📝 Exemplo de Configuração Completa

### Cloudflare Base
```
Account ID: 8d9e1234567890abcdef
API Token: [seu_token_aqui]
```

### Cloudflare Pages
```
Project Template: site-{order_id}
```

### Cloudflare R2
```
Bucket Name: innexar-assets
Endpoint URL: https://8d9e1234567890abcdef.r2.cloudflarestorage.com
Access Key ID: [seu_access_key]
Secret Access Key: [seu_secret_key]
```

### Cloudflare DNS
```
Zone ID: 1234567890abcdef1234567890abcdef
```

---

## 🚀 Próximo Passo

Após configurar tudo:
1. Teste cada conexão
2. Salve todas as configurações
3. Sistema estará pronto para usar Cloudflare no pipeline!
