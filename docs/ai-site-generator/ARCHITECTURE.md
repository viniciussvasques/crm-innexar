# Arquitetura Técnica - AI Site Generator

## 1. Visão de Componentes

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTE (Browser)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Checkout  │  │  Onboarding │  │   Portal    │  │   Preview   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                            GATEWAY / CDN                                    │
│                         (Cloudflare / Traefik)                              │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   Site Next   │           │   CRM API     │           │  Site Generator│
│   (Frontend)  │           │   (FastAPI)   │           │   API (FastAPI)│
└───────────────┘           └───────────────┘           └───────────────┘
                                      │                         │
                                      ▼                         ▼
                            ┌───────────────┐           ┌───────────────┐
                            │   PostgreSQL  │           │     Redis     │
                            │   (State)     │           │ (Queue+Cache) │
                            └───────────────┘           └───────────────┘
                                                                │
                                      ┌─────────────────────────┤
                                      ▼                         ▼
                            ┌───────────────┐           ┌───────────────┐
                            │    Workers    │           │  Build Runner │
                            │   (Celery)    │           │   (Isolated)  │
                            └───────────────┘           └───────────────┘
                                      │                         │
        ┌─────────────────────────────┼─────────────────────────┤
        ▼                             ▼                         ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   AI Service  │           │    GitHub     │           │  Cloudflare   │
│ (Claude/GPT)  │           │   (Repos)     │           │   (Deploy)    │
└───────────────┘           └───────────────┘           └───────────────┘
```

---

## 2. Detalhamento dos Componentes

### 2.1 API Principal (CRM + Site Generator)

**Responsabilidades:**
- Autenticação e autorização
- Gerenciamento de projetos
- Orquestração do pipeline
- Publicação de eventos para fila
- Exposição de endpoints REST

**Tecnologias:**
- FastAPI (Python 3.11+)
- SQLAlchemy + Alembic
- Pydantic para validação
- JWT para auth

**Endpoints principais:**
```
POST /api/v1/projects                    # Cria projeto após pagamento
POST /api/v1/projects/{id}/generate      # Inicia geração
GET  /api/v1/projects/{id}               # Status e URLs
GET  /api/v1/projects/{id}/pipeline      # Etapas do pipeline
POST /api/v1/projects/{id}/revisions     # Pedido de alteração
POST /api/v1/projects/{id}/approve       # Aprovação humana
```

---

### 2.2 Orquestrador de Jobs (Celery + Redis)

**Responsabilidades:**
- Executar etapas do pipeline de forma assíncrona
- Gerenciar retries e dead letter queue
- Logging estruturado
- Notificações de status

**Tasks do Pipeline:**
```python
# Etapa A - Ingestão
tasks.validate_onboarding(project_id)
tasks.download_assets(project_id)
tasks.create_site_spec(project_id)

# Etapa B - Documentação
tasks.generate_brief(project_id)
tasks.generate_sitemap(project_id)
tasks.generate_content(project_id)

# Etapa C - Projeto
tasks.provision_repository(project_id)
tasks.setup_project_structure(project_id)

# Etapa D - Geração
tasks.generate_layout_plan(project_id)
tasks.generate_code_patch(project_id)
tasks.apply_patch(project_id)
tasks.build_and_test(project_id)

# Etapa E - Deploy
tasks.deploy_preview(project_id)
tasks.provision_subdomain(project_id)

# Etapa F - Revisão
tasks.process_revision_request(project_id, revision_id)
tasks.generate_revision_patch(project_id, revision_id)
```

**Configuração de Retry:**
```python
@celery.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def generate_code_patch(self, project_id):
    ...
```

---

### 2.3 Build Runner (Isolado)

**Responsabilidades:**
- Executar operações Git (clone, commit, push)
- Executar npm install / build / test
- Produzir artefatos de build
- Ambiente sandboxed e seguro

**Implementação:**
- Container Docker por job
- Recursos limitados (CPU, RAM, tempo)
- Rede isolada (só acesso ao Git e npm registry)
- Limpeza automática após execução

**Estrutura:**
```yaml
# docker-compose.build-runner.yml
services:
  build-runner:
    image: innexar/build-runner:latest
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
    networks:
      - build-network
    volumes:
      - /tmp/builds:/builds
```

---

### 2.4 AI Service (Camada de IA)

**Responsabilidades:**
- Transformar onboarding em site_spec
- Gerar documentação e conteúdo
- Produzir patches de código
- Validar saída com JSON schemas

**Princípio Fundamental:**
> A IA não executa ações. Ela apenas retorna artefatos estruturados (JSON, Markdown, diffs). Quem executa é o backend/runner.

**Modelos por Tarefa:**
```python
AI_MODELS = {
    "content_generation": {
        "provider": "anthropic",
        "model": "claude-3-5-sonnet",
        "purpose": "Copy, headlines, CTAs"
    },
    "code_generation": {
        "provider": "anthropic", 
        "model": "claude-3-5-sonnet",
        "purpose": "Patches, diffs, código"
    },
    "analysis": {
        "provider": "openai",
        "model": "gpt-4o",
        "purpose": "Análise de requisitos"
    }
}
```

**Output Estruturado:**
```python
class AIOutput(BaseModel):
    success: bool
    artifact_type: str  # "brief", "content", "layout", "patch"
    content: dict | str
    validation_errors: list[str] = []
    tokens_used: int
```

---

### 2.5 Storage (Cloudflare R2)

**Responsabilidades:**
- Armazenar assets do cliente (logo, imagens)
- Armazenar artefatos gerados (PDFs, ZIPs)
- Servir assets para o site gerado

**Estrutura de Pastas:**
```
innexar-site-generator/
├── projects/
│   └── {project_id}/
│       ├── assets/
│       │   ├── logo.png
│       │   └── images/
│       ├── artifacts/
│       │   ├── brief.md
│       │   ├── sitemap.json
│       │   └── content.json
│       └── builds/
│           ├── build-001.zip
│           └── build-002.zip
└── templates/
    ├── landing-page/
    ├── saas-platform/
    └── portfolio/
```

---

### 2.6 GitHub Integration

**Responsabilidades:**
- Criar repositórios a partir de templates
- Commitar alterações
- Gerenciar branches (main, preview, feature)
- Trigger de CI/CD

**Fluxo:**
```
1. Template repo clonado
2. Branch "preview-{project_id}" criado
3. Patches aplicados via commits
4. Push trigger deploy no Cloudflare Pages
```

---

### 2.7 Cloudflare Integration

**Cloudflare Pages:**
- Deploy automático via Git
- Preview URLs por branch
- SSL automático

**Cloudflare DNS:**
- Subdomínios dinâmicos: `{slug}.innexar.app`
- CNAME apontando para Pages

**Cloudflare R2:**
- Storage de assets
- CDN integrado

---

## 3. Fluxo de Dados

### 3.1 Checkout → Projeto
```
1. Cliente paga (Stripe webhook)
2. API cria registro `customer` + `order`
3. Cliente direciona para onboarding
```

### 3.2 Onboarding → Pipeline
```
1. Cliente submete formulário
2. API cria `onboarding_submission`
3. API cria `project` com status "queued"
4. API enfileira job `generate_site(project_id)`
```

### 3.3 Pipeline de Geração
```
validate_onboarding
    ├── SUCCESS → download_assets
    └── FAIL → notify_human

download_assets
    └── SUCCESS → create_site_spec

create_site_spec
    └── SUCCESS → generate_brief

generate_brief
    └── SUCCESS → generate_content

generate_content
    └── SUCCESS → provision_repository

provision_repository
    └── SUCCESS → generate_layout_plan

generate_layout_plan
    └── SUCCESS → generate_code_patch

generate_code_patch
    ├── SUCCESS → build_and_test
    └── FAIL (retry 3x) → notify_human

build_and_test
    ├── SUCCESS → deploy_preview
    └── FAIL → generate_fix_patch → build_and_test (max 3x)

deploy_preview
    └── SUCCESS → provision_subdomain

provision_subdomain
    └── SUCCESS → notify_client + notify_workspace
```

---

## 4. Segurança

### 4.1 Isolamento de Build
- Cada build em container separado
- Sem acesso à rede principal
- Timeout de 10 minutos
- Recursos limitados

### 4.2 Validação de Inputs
- Schema validation em todo JSON
- Sanitização de strings
- Allowlist de arquivos editáveis

### 4.3 Secrets Management
- Variáveis de ambiente
- Vault/secrets manager para produção
- Rotação de API keys

### 4.4 Rate Limiting
- Limite de projetos por hora
- Limite de chamadas à IA
- Proteção contra abuse

---

## 5. Monitoramento

### 5.1 Logs
- Estruturados (JSON)
- Centralizados (Loki/ELK)
- Retenção: 30 dias

### 5.2 Métricas
- Tempo por etapa do pipeline
- Taxa de sucesso/falha
- Uso de tokens IA
- Custo por projeto

### 5.3 Alertas
- Pipeline travado > 30min
- Taxa de erro > 10%
- Falha em múltiplos projetos
- Quota de IA próxima do limite

---

*Última atualização: Janeiro 2026*
