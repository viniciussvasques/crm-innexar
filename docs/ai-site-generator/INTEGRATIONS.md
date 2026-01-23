# Integrações Externas - AI Site Generator

## Visão Geral das Integrações

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AI SITE GENERATOR                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│   │ GitHub  │  │Cloudflare│ │   AI    │  │ Storage │  │  Stripe │          │
│   │  API    │  │   API    │ │ Models  │  │   R2    │  │   API   │          │
│   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘          │
│        │            │            │            │            │               │
│        └────────────┴────────────┴────────────┴────────────┘               │
│                                  │                                          │
│                           ┌──────┴──────┐                                   │
│                           │  Integration │                                   │
│                           │   Manager    │                                   │
│                           └─────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. GitHub Integration

### Propósito
- Criar repositórios para projetos de clientes
- Gerenciar código e versionamento
- Aplicar patches gerados pela IA

### Configuração

```python
class GitHubConfig(BaseModel):
    access_token: str  # Personal Access Token ou GitHub App
    organization: str  # "innexar-clients"
    template_repos: dict[str, str]  # Mapeamento de templates
    webhook_secret: str  # Para receber eventos

# Exemplo
github_config = GitHubConfig(
    access_token="ghp_xxxxxxxxxxxxxxxxxxxx",
    organization="innexar-clients",
    template_repos={
        "landing": "innexar-clients/template-landing-page",
        "business": "innexar-clients/template-business",
        "saas": "innexar-clients/template-saas",
        "portfolio": "innexar-clients/template-portfolio"
    },
    webhook_secret="whsec_xxx"
)
```

### Endpoints Utilizados

| Endpoint | Método | Propósito |
|----------|--------|-----------|
| `/repos/{owner}/{repo}/generate` | POST | Criar repo de template |
| `/repos/{owner}/{repo}/contents/{path}` | PUT | Atualizar arquivo |
| `/repos/{owner}/{repo}/git/refs` | POST | Criar branch |
| `/repos/{owner}/{repo}/git/commits` | POST | Criar commit |
| `/repos/{owner}/{repo}` | GET | Info do repo |

### Operações

```python
class GitHubService:
    async def create_repo_from_template(
        self, 
        template_key: str, 
        project_slug: str
    ) -> str:
        """Cria novo repo a partir de template"""
        pass
    
    async def create_branch(
        self, 
        repo: str, 
        branch: str, 
        from_ref: str = "main"
    ) -> None:
        """Cria nova branch"""
        pass
    
    async def apply_patch(
        self, 
        repo: str, 
        branch: str, 
        patch: str
    ) -> str:
        """Aplica patch e retorna commit SHA"""
        pass
    
    async def get_file(
        self, 
        repo: str, 
        path: str, 
        ref: str = "main"
    ) -> str:
        """Obtém conteúdo de arquivo"""
        pass
```

### Rate Limits
- 5000 requests/hora (autenticado)
- Implementar retry com backoff exponencial

---

## 2. Cloudflare Integration

### Propósito
- Deploy de sites para preview
- Gerenciamento de DNS (subdomínios)
- Storage de assets (R2)

### Configuração

```python
class CloudflareConfig(BaseModel):
    api_token: str  # Token com permissões de Pages, DNS, R2
    account_id: str
    zone_id: str  # Para DNS
    pages_project: str  # Nome do projeto no Pages
    r2_bucket: str
    r2_access_key_id: str
    r2_secret_access_key: str
    preview_domain: str  # "preview.innexar.app"

# Exemplo
cloudflare_config = CloudflareConfig(
    api_token="xxxxxxxxxxxxxxxxxxxx",
    account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    zone_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    pages_project="innexar-sites",
    r2_bucket="innexar-assets",
    r2_access_key_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    r2_secret_access_key="xxxxxxxxxxxxxxxxxxxx",
    preview_domain="preview.innexar.app"
)
```

### Cloudflare Pages

#### Deploy Flow
1. Push para GitHub trigger build
2. Cloudflare Pages detecta e builda
3. Preview URL gerada: `{branch}.innexar-sites.pages.dev`

#### API Endpoints

| Endpoint | Método | Propósito |
|----------|--------|-----------|
| `/accounts/{id}/pages/projects` | GET | Listar projetos |
| `/accounts/{id}/pages/projects/{name}/deployments` | GET | Listar deploys |
| `/accounts/{id}/pages/projects/{name}/deployments/{id}` | GET | Status do deploy |

### Cloudflare DNS

#### Subdomínios Dinâmicos

```python
class CloudflareDNSService:
    async def create_subdomain(
        self, 
        subdomain: str,  # "cliente-abc"
        target: str  # CNAME target
    ) -> str:
        """Cria subdomain.preview.innexar.app"""
        record = {
            "type": "CNAME",
            "name": f"{subdomain}.preview",
            "content": target,
            "proxied": True
        }
        # POST /zones/{zone_id}/dns_records
        return record_id
    
    async def delete_subdomain(self, record_id: str) -> None:
        """Remove DNS record"""
        # DELETE /zones/{zone_id}/dns_records/{record_id}
        pass
```

### Cloudflare R2 (Storage)

#### Operações

```python
class CloudflareR2Service:
    async def upload_file(
        self, 
        key: str,  # "projects/{id}/assets/logo.png"
        content: bytes,
        content_type: str
    ) -> str:
        """Upload arquivo para R2"""
        return public_url
    
    async def get_file(self, key: str) -> bytes:
        """Download arquivo"""
        pass
    
    async def delete_file(self, key: str) -> None:
        """Remove arquivo"""
        pass
    
    async def list_files(self, prefix: str) -> list[str]:
        """Lista arquivos por prefixo"""
        pass
```

---

## 3. AI Models Integration

### Propósito
- Geração de conteúdo textual
- Geração de código
- Análise de requisitos

### Configuração

```python
class AIModelConfig(BaseModel):
    provider: str  # "anthropic", "openai", "google"
    model: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7

class AIConfig(BaseModel):
    content_generation: AIModelConfig
    code_generation: AIModelConfig
    analysis: AIModelConfig

# Exemplo
ai_config = AIConfig(
    content_generation=AIModelConfig(
        provider="anthropic",
        model="claude-3-5-sonnet-20241022",
        api_key="sk-ant-xxxxx",
        max_tokens=4000,
        temperature=0.7
    ),
    code_generation=AIModelConfig(
        provider="anthropic",
        model="claude-3-5-sonnet-20241022",
        api_key="sk-ant-xxxxx",
        max_tokens=8000,
        temperature=0.3  # Mais determinístico
    ),
    analysis=AIModelConfig(
        provider="openai",
        model="gpt-4o",
        api_key="sk-xxxxx",
        max_tokens=4000
    )
)
```

### Diferenças para Helena (IA do CRM)

| Aspecto | Helena (CRM) | Site Generator |
|---------|--------------|----------------|
| Propósito | Chat, CRM ops | Gerar sites |
| Contexto | Dados do CRM | Template + onboarding |
| Output | Texto, JSON | Diffs, código |
| Model | Configurável | Específico por tarefa |
| Prompt | Conversacional | Estruturado |

### AI Service

```python
class AIService:
    def __init__(self, config: AIConfig):
        self.config = config
    
    async def generate_content(
        self,
        task_type: str,  # "brief", "sitemap", "content"
        context: dict
    ) -> AIOutput:
        """Gera conteúdo usando modelo apropriado"""
        model_config = self.config.content_generation
        prompt = self._build_prompt(task_type, context)
        response = await self._call_model(model_config, prompt)
        return self._parse_response(response, task_type)
    
    async def generate_code(
        self,
        task_type: str,  # "layout_plan", "patch"
        context: dict
    ) -> AIOutput:
        """Gera código usando modelo apropriado"""
        model_config = self.config.code_generation
        # ...
    
    async def analyze(
        self,
        task_type: str,  # "onboarding", "review"
        data: dict
    ) -> AIOutput:
        """Analisa dados"""
        model_config = self.config.analysis
        # ...
```

### Prompts Templates

Os prompts são armazenados separadamente e versionados:

```
prompts/
├── content/
│   ├── brief.md
│   ├── sitemap.md
│   └── page_content.md
├── code/
│   ├── layout_plan.md
│   └── generate_patch.md
└── analysis/
    ├── onboarding_analysis.md
    └── review_request.md
```

---

## 4. Stripe Integration (Existente)

### Propósito
- Processar pagamentos
- Webhook para criar projetos após pagamento

### Conexão com Site Generator

```python
# Webhook handler existente
@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    event = stripe.Webhook.construct_event(...)
    
    if event.type == "checkout.session.completed":
        session = event.data.object
        
        # Criar order (existente)
        order = await create_order(session)
        
        # NOVO: Se for produto de site, criar projeto
        if is_site_product(session):
            project = await create_site_project(
                customer_id=order.customer_id,
                order_id=order.id,
                template=session.metadata.get("template")
            )
```

---

## 5. Tabela de Configurações no Banco

```sql
CREATE TABLE integration_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_type VARCHAR(50) NOT NULL,  -- 'github', 'cloudflare', 'ai', 'storage'
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT NOT NULL,  -- Encrypted
    is_secret BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(integration_type, config_key)
);

-- Índices
CREATE INDEX idx_integration_config_type ON integration_config(integration_type);
```

### Encryption

```python
from cryptography.fernet import Fernet

class ConfigService:
    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key)
    
    def encrypt_value(self, value: str) -> str:
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted: str) -> str:
        return self.cipher.decrypt(encrypted.encode()).decode()
    
    async def get_config(
        self, 
        integration_type: str
    ) -> dict:
        rows = await db.fetch_all(
            "SELECT * FROM integration_config WHERE integration_type = :type",
            {"type": integration_type}
        )
        config = {}
        for row in rows:
            value = row.config_value
            if row.is_secret:
                value = self.decrypt_value(value)
            config[row.config_key] = value
        return config
```

---

## 6. Testes de Integração

### Endpoints de Teste

```python
@router.post("/integrations/{type}/test")
async def test_integration(type: str):
    """Testa conexão com integração"""
    if type == "github":
        return await github_service.test_connection()
    elif type == "cloudflare":
        return await cloudflare_service.test_connection()
    elif type == "ai":
        return await ai_service.test_models()
    elif type == "storage":
        return await storage_service.test_connection()
```

### Implementação de Teste

```python
class GitHubService:
    async def test_connection(self) -> TestResult:
        try:
            # Tenta listar repos da org
            response = await self.client.get(
                f"/orgs/{self.config.organization}/repos"
            )
            if response.status_code == 200:
                repos = response.json()
                return TestResult(
                    success=True,
                    message=f"Conectado. {len(repos)} repositórios encontrados."
                )
            else:
                return TestResult(
                    success=False,
                    message=f"Erro {response.status_code}: {response.text}"
                )
        except Exception as e:
            return TestResult(success=False, message=str(e))
```

---

## 7. Próximos Passos

1. [ ] Criar tabela `integration_config`
2. [ ] Implementar endpoints CRUD
3. [ ] Criar serviços para cada integração
4. [ ] Implementar testes de conexão
5. [ ] Criar UI no CRM

---

*Última atualização: Janeiro 2026*
