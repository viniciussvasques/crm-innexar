# Modelo de Dados - AI Site Generator

## Diagrama ER

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    customer     │     │     order       │     │    project      │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id              │◄────│ customer_id     │     │ id              │
│ name            │     │ id              │◄────│ order_id        │
│ email           │     │ product_id      │     │ customer_id     │
│ ...             │     │ status          │     │ template_id     │
└─────────────────┘     │ ...             │     │ status          │
                        └─────────────────┘     │ subdomain       │
                                                │ preview_url     │
                                                │ repo_url        │
                                                └────────┬────────┘
                                                         │
        ┌────────────────────────────────────────────────┼────────────────────────────────────────────────┐
        │                                                │                                                │
        ▼                                                ▼                                                ▼
┌─────────────────┐                           ┌─────────────────┐                           ┌─────────────────┐
│ onboarding_     │                           │  pipeline_step  │                           │    site_spec    │
│ submission      │                           ├─────────────────┤                           ├─────────────────┤
├─────────────────┤                           │ id              │                           │ id              │
│ id              │                           │ project_id      │                           │ project_id      │
│ project_id      │                           │ step_key        │                           │ version         │
│ raw_data        │                           │ status          │                           │ spec_data       │
│ assets_refs     │                           │ started_at      │                           │ created_at      │
│ created_at      │                           │ finished_at     │                           └─────────────────┘
└─────────────────┘                           │ error_message   │
                                              │ logs_ref        │
                                              └─────────────────┘
                                                         │
        ┌────────────────────────────────────────────────┼────────────────────────────────────────────────┐
        │                                                │                                                │
        ▼                                                ▼                                                ▼
┌─────────────────┐                           ┌─────────────────┐                           ┌─────────────────┐
│    artifact     │                           │ revision_request│                           │ integration_    │
├─────────────────┤                           ├─────────────────┤                           │ config          │
│ id              │                           │ id              │                           ├─────────────────┤
│ project_id      │                           │ project_id      │                           │ id              │
│ type            │                           │ source          │                           │ integration_type│
│ ref             │                           │ message         │                           │ config_key      │
│ version         │                           │ status          │                           │ config_value    │
│ created_at      │                           │ diff_ref        │                           │ is_secret       │
└─────────────────┘                           │ created_at      │                           └─────────────────┘
                                              └─────────────────┘
```

---

## Tabelas Detalhadas

### 1. project

Representa um projeto de site sendo gerado.

```sql
CREATE TABLE project (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customer(id),
    order_id UUID REFERENCES order(id),
    
    -- Identificação
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    
    -- Template
    template_id VARCHAR(50) NOT NULL,  -- 'landing', 'saas', etc
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- pending, onboarding, generating, preview_ready, 
    -- in_review, approved, delivered, cancelled
    
    -- URLs e Repos
    repo_url VARCHAR(500),
    preview_url VARCHAR(500),
    subdomain VARCHAR(100),
    production_url VARCHAR(500),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    delivered_at TIMESTAMP
);

-- Índices
CREATE INDEX idx_project_customer ON project(customer_id);
CREATE INDEX idx_project_status ON project(status);
CREATE INDEX idx_project_slug ON project(slug);
```

### 2. onboarding_submission

Dados coletados no onboarding do cliente.

```sql
CREATE TABLE onboarding_submission (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES project(id),
    
    -- Dados brutos do formulário
    raw_data JSONB NOT NULL,
    
    -- Referências a assets (logo, imagens)
    assets_refs JSONB DEFAULT '[]',
    -- [{"type": "logo", "url": "...", "original_name": "..."}]
    
    -- Validação
    is_valid BOOLEAN DEFAULT FALSE,
    validation_errors JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_onboarding_project ON onboarding_submission(project_id);
```

### 3. site_spec

Especificação do site gerada pela IA.

```sql
CREATE TABLE site_spec (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES project(id),
    
    -- Versão (para histórico)
    version INTEGER NOT NULL DEFAULT 1,
    
    -- Especificação completa
    spec_data JSONB NOT NULL,
    -- {
    --   "business": {...},
    --   "pages": [...],
    --   "design": {...},
    --   "seo": {...}
    -- }
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(project_id, version)
);

CREATE INDEX idx_site_spec_project ON site_spec(project_id);
```

### 4. pipeline_step

Cada etapa do pipeline de geração.

```sql
CREATE TYPE step_status AS ENUM (
    'queued', 'running', 'success', 'failed', 'skipped', 'manual'
);

CREATE TABLE pipeline_step (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES project(id),
    
    -- Identificação da etapa
    step_key VARCHAR(50) NOT NULL,
    -- 'validate_onboarding', 'generate_brief', 'build_and_test', etc
    
    step_order INTEGER NOT NULL,  -- Ordem de execução
    
    -- Status
    status step_status NOT NULL DEFAULT 'queued',
    
    -- Execução
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Erros
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    error_details JSONB,
    
    -- Logs (referência ao storage)
    logs_ref VARCHAR(500),
    
    -- Resultado (referência a artifacts)
    output_ref VARCHAR(500),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(project_id, step_key)
);

CREATE INDEX idx_pipeline_project ON pipeline_step(project_id);
CREATE INDEX idx_pipeline_status ON pipeline_step(status);
```

### 5. artifact

Artefatos gerados durante o pipeline.

```sql
CREATE TYPE artifact_type AS ENUM (
    'brief', 'sitemap', 'content', 'layout_plan',
    'code_patch', 'build_report', 'preview_screenshot'
);

CREATE TABLE artifact (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES project(id),
    
    -- Tipo
    type artifact_type NOT NULL,
    
    -- Versão (para histórico)
    version INTEGER NOT NULL DEFAULT 1,
    
    -- Referência ao storage
    storage_ref VARCHAR(500) NOT NULL,
    -- "projects/{project_id}/artifacts/brief_v1.md"
    
    -- Conteúdo inline (para JSONs pequenos)
    inline_content JSONB,
    
    -- Metadata
    file_size INTEGER,
    mime_type VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(project_id, type, version)
);

CREATE INDEX idx_artifact_project ON artifact(project_id);
CREATE INDEX idx_artifact_type ON artifact(type);
```

### 6. revision_request

Solicitações de revisão do cliente ou humano.

```sql
CREATE TYPE revision_source AS ENUM ('client', 'human', 'ai');
CREATE TYPE revision_status AS ENUM (
    'pending', 'processing', 'applied', 'rejected'
);

CREATE TABLE revision_request (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES project(id),
    
    -- Origem
    source revision_source NOT NULL,
    requested_by UUID,  -- user_id se humano
    
    -- Conteúdo
    message TEXT NOT NULL,
    affected_pages JSONB,  -- ['home', 'about']
    
    -- Processamento
    status revision_status NOT NULL DEFAULT 'pending',
    diff_ref VARCHAR(500),  -- Patch gerado
    
    -- Resultado
    applied_at TIMESTAMP,
    applied_commit VARCHAR(100),
    rejection_reason TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_revision_project ON revision_request(project_id);
CREATE INDEX idx_revision_status ON revision_request(status);
```

### 7. integration_config

Configurações de integrações externas.

```sql
CREATE TABLE integration_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Tipo de integração
    integration_type VARCHAR(50) NOT NULL,
    -- 'github', 'cloudflare', 'ai_content', 'ai_code', 'storage'
    
    -- Chave e valor
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT NOT NULL,  -- Encrypted if is_secret
    
    -- Flags
    is_secret BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    description TEXT,
    last_tested_at TIMESTAMP,
    last_test_success BOOLEAN,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(integration_type, config_key)
);

CREATE INDEX idx_integration_type ON integration_config(integration_type);
```

### 8. template_registry

Catálogo de templates disponíveis.

```sql
CREATE TABLE template_registry (
    id VARCHAR(50) PRIMARY KEY,  -- 'landing', 'saas', etc
    
    -- Descrição
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Repositório
    repo_url VARCHAR(500) NOT NULL,
    default_branch VARCHAR(50) DEFAULT 'main',
    
    -- Configuração
    config JSONB NOT NULL,
    -- {
    --   "pages": ["home", "about", "contact"],
    --   "editable_files": [...],
    --   "sections": {...}
    -- }
    
    -- Preview
    thumbnail_url VARCHAR(500),
    preview_url VARCHAR(500),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## Relações

| De | Para | Tipo | Descrição |
|----|------|------|-----------|
| project | customer | N:1 | Projeto pertence a um cliente |
| project | order | N:1 | Projeto originado de uma order |
| onboarding_submission | project | 1:1 | Um onboarding por projeto |
| site_spec | project | N:1 | Múltiplas versões do spec |
| pipeline_step | project | N:1 | Múltiplas etapas por projeto |
| artifact | project | N:1 | Múltiplos artefatos por projeto |
| revision_request | project | N:1 | Múltiplas revisões por projeto |

---

## Migrations (Alembic)

### Criar migration inicial

```bash
alembic revision --autogenerate -m "add_site_generator_tables"
```

### Estrutura de migrations

```
alembic/
├── versions/
│   ├── 001_initial.py
│   ├── 002_add_customers.py
│   └── 003_add_site_generator_tables.py  # NOVA
└── env.py
```

---

*Última atualização: Janeiro 2026*
