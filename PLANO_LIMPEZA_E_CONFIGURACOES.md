# Plano de Limpeza e Configurações - Sistema Profissional

## 🗑️ 1. Código a Remover/Refatorar

### 1.1 Código Legado/Duplicado

#### ❌ Remover

1. **`backend/app/api/ai.py` - Função `_call_grok_api_legacy`**
   - **Localização**: Linha 111-131
   - **Motivo**: Função legada, não usada (já existe `_call_grok_api`)
   - **Ação**: Deletar função

2. **`backend/cleanup.sql`**
   - **Motivo**: Script temporário de teste
   - **Ação**: Mover para `scripts/` ou deletar se não for mais necessário

3. **`backend/clean_empty_generations.py`**
   - **Motivo**: Script de manutenção, não deve estar na raiz
   - **Ação**: Mover para `backend/scripts/maintenance/`

#### ⚠️ Refatorar

1. **`backend/app/api/ai.py` e `backend/app/services/ai_service.py`**
   - **Problema**: Lógica duplicada de chamadas de API
   - **Ação**: Consolidar em `ai_service.py`, `ai.py` apenas endpoints

2. **Página de Configurações Duplicada**
   - **Problema**: `settings/page.tsx` e `ai-config/page.tsx` têm sobreposição
   - **Ação**: Consolidar AI configs em `settings/page.tsx`, remover `ai-config/page.tsx` ou fazer redirect

3. **Logging Direto com asyncpg**
   - **Problema**: `_log_progress` usa asyncpg diretamente (bypass SQLAlchemy)
   - **Ação**: Criar serviço de logging dedicado ou usar SQLAlchemy corretamente

---

## ➕ 2. Configurações Faltantes

### 2.1 Cloudflare (Parcial - Completar)

#### ✅ O Que Já Existe

- ✅ Cloudflare AI config (em `ai-config`)
- ✅ Account ID suportado
- ✅ Base URL automática

#### ❌ O Que Falta

1. **Cloudflare Pages**
   - Configuração de deploy automático
   - Preview URLs
   - Webhook de deploy

2. **Cloudflare R2 (S3-compatible)**
   - Configuração de bucket
   - Access Key ID
   - Secret Access Key
   - Endpoint URL

3. **Cloudflare DNS**
   - API Token para gerenciar subdomínios
   - Zone ID

### 2.2 S3/R2 Storage (Não Existe)

#### ❌ Criar Do Zero

1. **Modelo de Dados**
   ```python
   # IntegrationConfig com type="cloudflare_r2" ou "s3"
   - bucket_name
   - access_key_id (secret)
   - secret_access_key (secret)
   - endpoint_url
   - region
   ```

2. **Backend API**
   - Endpoints para configurar S3/R2
   - Teste de conexão
   - Upload/download de arquivos

3. **Frontend UI**
   - Formulário de configuração
   - Teste de conexão
   - Lista de buckets/configs

### 2.3 GitHub Integration (Parcial)

#### ✅ O Que Já Existe

- ✅ Modelo `IntegrationConfig` com type="github"
- ✅ Campo para token

#### ❌ O Que Falta

1. **Configuração Completa**
   - GitHub App vs Personal Token
   - Organization/Repository selection
   - Webhook configuration
   - Branch management

2. **Funcionalidade**
   - Criar repositórios
   - Commitar mudanças
   - Gerenciar branches
   - PR creation

---

## 📋 3. Estrutura de Configurações Proposta

### 3.1 Aba "Integrations" (Expandir)

```
Integrations Tab:
├── GitHub
│   ├── Personal Token / GitHub App
│   ├── Organization
│   ├── Default Branch
│   └── Webhook Secret
│
├── Cloudflare
│   ├── AI (já existe)
│   ├── Pages
│   │   ├── Account ID
│   │   ├── API Token
│   │   └── Project Name Template
│   ├── R2 Storage
│   │   ├── Bucket Name
│   │   ├── Access Key ID
│   │   ├── Secret Access Key
│   │   ├── Endpoint URL
│   │   └── Region
│   └── DNS
│       ├── Zone ID
│       └── API Token
│
└── AWS S3 (Alternativa)
    ├── Access Key ID
    ├── Secret Access Key
    ├── Bucket Name
    ├── Region
    └── Endpoint URL
```

### 3.2 Aba "Deploy Servers" (Melhorar)

```
Deploy Servers Tab:
├── Cloudflare Pages (novo tipo)
│   ├── Account ID
│   ├── Project Name
│   └── API Token
│
├── Vercel (novo tipo)
│   ├── Team ID
│   ├── Project Name
│   └── API Token
│
└── SSH/VPS (já existe)
    └── (mantém como está)
```

---

## 🔧 4. Implementação

### 4.1 Backend - Modelos

#### Adicionar Campos em `IntegrationConfig`

```python
# Já existe, mas adicionar campos específicos:
- cloudflare_pages_project_template
- cloudflare_r2_bucket_name
- cloudflare_r2_endpoint_url
- github_organization
- github_default_branch
```

#### Criar Schema para S3/R2

```python
class S3ConfigCreate(BaseModel):
    provider: Literal["cloudflare_r2", "aws_s3"]
    bucket_name: str
    access_key_id: str
    secret_access_key: str
    endpoint_url: Optional[str] = None
    region: Optional[str] = None
```

### 4.2 Backend - API Endpoints

#### Adicionar em `site_generator_config.py`

```python
# Cloudflare Pages
@router.post("/config/cloudflare-pages")
async def configure_cloudflare_pages(...)

# Cloudflare R2 / S3
@router.post("/config/storage")
async def configure_storage(...)

# GitHub (melhorar)
@router.post("/config/github")
async def configure_github(...)

# Test endpoints
@router.post("/config/cloudflare-pages/test")
@router.post("/config/storage/test")
@router.post("/config/github/test")
```

### 4.3 Frontend - Página de Configurações

#### Expandir `renderIntegrationsTab()`

```typescript
const renderIntegrationsTab = () => (
  <div className="space-y-8">
    {/* GitHub Section */}
    <GitHubConfigSection />
    
    {/* Cloudflare Section */}
    <CloudflareConfigSection>
      <CloudflareAIConfig /> {/* Já existe, manter */}
      <CloudflarePagesConfig /> {/* NOVO */}
      <CloudflareR2Config /> {/* NOVO */}
      <CloudflareDNSConfig /> {/* NOVO */}
    </CloudflareConfigSection>
    
    {/* Storage Section */}
    <StorageConfigSection>
      <S3Config /> {/* NOVO */}
      <R2Config /> {/* NOVO */}
    </StorageConfigSection>
  </div>
)
```

---

## 📝 5. Checklist de Implementação

### Fase 1: Limpeza (1-2 dias)

- [ ] Remover `_call_grok_api_legacy`
- [ ] Mover `clean_empty_generations.py` para `scripts/`
- [ ] Mover `cleanup.sql` para `scripts/` ou deletar
- [ ] Consolidar lógica de AI em `ai_service.py`
- [ ] Refatorar `_log_progress` para usar serviço dedicado

### Fase 2: Cloudflare Completo (2-3 dias)

- [ ] Adicionar Cloudflare Pages config
- [ ] Adicionar Cloudflare R2 config
- [ ] Adicionar Cloudflare DNS config
- [ ] Criar endpoints de teste
- [ ] UI no frontend

### Fase 3: S3/R2 Storage (2-3 dias)

- [ ] Criar schema de S3/R2
- [ ] Criar endpoints de configuração
- [ ] Criar serviço de upload/download
- [ ] UI no frontend
- [ ] Teste de conexão

### Fase 4: GitHub Melhorado (1-2 dias)

- [ ] Adicionar campos faltantes
- [ ] Melhorar UI
- [ ] Adicionar teste de conexão
- [ ] Documentação

### Fase 5: Deploy Servers (1 dia)

- [ ] Adicionar tipo "cloudflare_pages"
- [ ] Adicionar tipo "vercel"
- [ ] UI para novos tipos

---

## 🎯 6. Prioridades

### Alta Prioridade

1. **Cloudflare R2** - Necessário para assets
2. **Cloudflare Pages** - Necessário para preview
3. **Limpeza de código legado** - Manter código limpo

### Média Prioridade

4. **GitHub melhorado** - Para CI/CD
5. **S3 alternativo** - Para quem não usa Cloudflare

### Baixa Prioridade

6. **Vercel** - Alternativa ao Cloudflare Pages
7. **Refatoração de logging** - Melhoria arquitetural

---

## 📊 7. Estimativa Total

- **Limpeza**: 1-2 dias
- **Cloudflare Completo**: 2-3 dias
- **S3/R2**: 2-3 dias
- **GitHub**: 1-2 dias
- **Deploy Servers**: 1 dia

**Total**: 7-11 dias (~1.5-2 semanas)

---

## 🚀 8. Próximos Passos

1. **Começar pela limpeza** (rápido, melhora código)
2. **Cloudflare R2** (crítico para assets)
3. **Cloudflare Pages** (crítico para preview)
4. **GitHub melhorado** (necessário para CI/CD)
5. **S3 alternativo** (opcional)

---

## 📄 9. Arquivos a Modificar

### Backend

- `backend/app/models/configuration.py` - Adicionar campos
- `backend/app/api/site_generator_config.py` - Adicionar endpoints
- `backend/app/services/config_service.py` - Adicionar lógica
- `backend/app/api/ai.py` - Remover legado
- `backend/app/services/ai_service.py` - Consolidar lógica

### Frontend

- `frontend/src/app/settings/page.tsx` - Expandir integrations tab
- `frontend/src/app/ai-config/page.tsx` - Avaliar se mantém ou remove

### Scripts

- `backend/clean_empty_generations.py` → `backend/scripts/maintenance/`
- `backend/cleanup.sql` → `backend/scripts/` ou deletar

---

## ✅ 10. Resultado Final

Após implementação:

✅ Código limpo (sem legado)
✅ Cloudflare completo (AI + Pages + R2 + DNS)
✅ S3/R2 configurável
✅ GitHub melhorado
✅ Deploy servers expandidos
✅ UI profissional e organizada
