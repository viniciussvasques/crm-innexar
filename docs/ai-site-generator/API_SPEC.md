# API Specification - AI Site Generator

## Base URL

```
Production: https://api.innexar.app/v1
Development: http://localhost:8000/v1
```

## Authentication

Todas as rotas requerem autenticação via JWT Bearer token.

```
Authorization: Bearer <token>
```

---

## Endpoints

### 1. Projects

#### POST /projects

Cria um novo projeto de site.

**Request:**
```json
{
  "customer_id": "uuid",
  "order_id": "uuid",  // opcional
  "name": "Dhv Group Website",
  "template_id": "landing"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "customer_id": "uuid",
  "name": "Dhv Group Website",
  "slug": "dhv-group-website",
  "template_id": "landing",
  "status": "pending",
  "created_at": "2026-01-23T10:00:00Z"
}
```

---

#### GET /projects/{id}

Retorna detalhes do projeto.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "customer_id": "uuid",
  "name": "Dhv Group Website",
  "slug": "dhv-group-website",
  "template_id": "landing",
  "status": "preview_ready",
  "repo_url": "https://github.com/innexar-clients/dhv-group-website",
  "preview_url": "https://dhv-group.preview.innexar.app",
  "subdomain": "dhv-group",
  "current_step": "deploy_preview",
  "progress_percent": 85,
  "created_at": "2026-01-23T10:00:00Z",
  "updated_at": "2026-01-23T11:30:00Z"
}
```

---

#### GET /projects/{id}/pipeline

Retorna status de todas as etapas do pipeline.

**Response:** `200 OK`
```json
{
  "project_id": "uuid",
  "steps": [
    {
      "step_key": "validate_onboarding",
      "status": "success",
      "started_at": "2026-01-23T10:05:00Z",
      "finished_at": "2026-01-23T10:05:30Z",
      "duration_seconds": 30
    },
    {
      "step_key": "generate_brief",
      "status": "success",
      "started_at": "2026-01-23T10:05:31Z",
      "finished_at": "2026-01-23T10:06:45Z",
      "duration_seconds": 74
    },
    {
      "step_key": "build_and_test",
      "status": "running",
      "started_at": "2026-01-23T11:25:00Z",
      "finished_at": null,
      "duration_seconds": null
    }
  ],
  "current_step": "build_and_test",
  "total_steps": 12,
  "completed_steps": 9
}
```

---

#### POST /projects/{id}/generate

Inicia o pipeline de geração.

**Request:** (body vazio)

**Response:** `202 Accepted`
```json
{
  "message": "Pipeline started",
  "project_id": "uuid",
  "job_id": "uuid",
  "estimated_duration_minutes": 15
}
```

---

### 2. Onboarding

#### POST /projects/{id}/onboarding

Submete dados de onboarding.

**Request:**
```json
{
  "business_name": "Dhv Group",
  "industry": "Serviços",
  "description": "Empresa de consultoria...",
  "target_audience": "PMEs",
  "services": ["Consultoria", "Treinamento"],
  "color_preference": "blue",
  "tone": "professional",
  "pages_needed": ["home", "about", "services", "contact"],
  "has_logo": true,
  "additional_info": "..."
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "is_valid": true,
  "validation_errors": [],
  "assets_upload_url": "https://upload.innexar.app/xyz"
}
```

---

#### POST /projects/{id}/onboarding/assets

Upload de assets (logo, imagens).

**Request:** `multipart/form-data`
- `file`: arquivo
- `type`: "logo" | "image"

**Response:** `200 OK`
```json
{
  "asset_id": "uuid",
  "type": "logo",
  "url": "https://assets.innexar.app/projects/xyz/logo.png",
  "original_name": "logo.png"
}
```

---

### 3. Artifacts

#### GET /projects/{id}/artifacts

Lista artefatos gerados.

**Response:** `200 OK`
```json
{
  "artifacts": [
    {
      "id": "uuid",
      "type": "brief",
      "version": 1,
      "download_url": "https://...",
      "created_at": "2026-01-23T10:10:00Z"
    },
    {
      "id": "uuid",
      "type": "sitemap",
      "version": 1,
      "inline_content": {...},
      "created_at": "2026-01-23T10:12:00Z"
    }
  ]
}
```

---

#### GET /projects/{id}/artifacts/{type}

Retorna artefato específico (última versão).

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "type": "content",
  "version": 2,
  "content": {
    "home": {
      "hero": {
        "headline": "Transformamos ideias...",
        "subheadline": "..."
      }
    }
  },
  "created_at": "2026-01-23T10:15:00Z"
}
```

---

### 4. Revisions

#### POST /projects/{id}/revisions

Solicita alteração no projeto.

**Request:**
```json
{
  "message": "Quero mudar a cor principal para verde",
  "affected_pages": ["home", "about"],
  "source": "client"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "status": "pending",
  "message": "Quero mudar a cor principal para verde",
  "created_at": "2026-01-23T12:00:00Z",
  "estimated_completion": "2026-01-23T12:15:00Z"
}
```

---

#### GET /projects/{id}/revisions

Lista todas as revisões.

**Response:** `200 OK`
```json
{
  "revisions": [
    {
      "id": "uuid",
      "source": "client",
      "status": "applied",
      "message": "Mudar headline da home",
      "created_at": "2026-01-23T11:30:00Z",
      "applied_at": "2026-01-23T11:45:00Z"
    }
  ]
}
```

---

#### POST /projects/{id}/approve

Aprova projeto para entrega.

**Request:**
```json
{
  "approved_by": "user_id",
  "notes": "Tudo ok, pode entregar"
}
```

**Response:** `200 OK`
```json
{
  "project_id": "uuid",
  "status": "approved",
  "approved_at": "2026-01-23T14:00:00Z",
  "approved_by": "user_id"
}
```

---

### 5. Integrations (Admin)

#### GET /integrations

Lista configurações de integrações.

**Response:** `200 OK`
```json
{
  "integrations": [
    {
      "type": "github",
      "status": "connected",
      "last_tested_at": "2026-01-23T08:00:00Z",
      "config": {
        "organization": "innexar-clients",
        "templates_count": 4
      }
    },
    {
      "type": "cloudflare",
      "status": "connected",
      "last_tested_at": "2026-01-23T08:00:00Z"
    }
  ]
}
```

---

#### PUT /integrations/{type}

Atualiza configuração de integração.

**Request:**
```json
{
  "access_token": "ghp_xxx...",
  "organization": "innexar-clients",
  "template_repos": {
    "landing": "innexar-clients/template-landing"
  }
}
```

**Response:** `200 OK`
```json
{
  "type": "github",
  "status": "connected",
  "updated_at": "2026-01-23T09:00:00Z"
}
```

---

#### POST /integrations/{type}/test

Testa conexão com integração.

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Conectado. 4 repositórios encontrados.",
  "tested_at": "2026-01-23T09:05:00Z"
}
```

---

### 6. Templates (Admin)

#### GET /templates

Lista templates disponíveis.

**Response:** `200 OK`
```json
{
  "templates": [
    {
      "id": "landing",
      "name": "Landing Page",
      "description": "Página única com seções configuráveis",
      "pages": ["home"],
      "thumbnail_url": "https://...",
      "is_active": true
    }
  ]
}
```

---

## Error Responses

### Formato Padrão

```json
{
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Projeto não encontrado",
    "field": null,
    "details": {}
  }
}
```

### Códigos de Erro

| Código | HTTP | Descrição |
|--------|------|-----------|
| `VALIDATION_ERROR` | 400 | Dados inválidos |
| `UNAUTHORIZED` | 401 | Não autenticado |
| `FORBIDDEN` | 403 | Sem permissão |
| `PROJECT_NOT_FOUND` | 404 | Projeto não existe |
| `INTEGRATION_ERROR` | 502 | Erro em serviço externo |
| `PIPELINE_FAILED` | 500 | Erro no pipeline |

---

## Webhooks (Outgoing)

O sistema envia webhooks para eventos importantes:

### Eventos

| Evento | Descrição |
|--------|-----------|
| `project.created` | Projeto criado |
| `project.generating` | Pipeline iniciado |
| `project.preview_ready` | Preview disponível |
| `project.revision_requested` | Cliente pediu alteração |
| `project.approved` | Projeto aprovado |
| `project.delivered` | Entrega concluída |
| `pipeline.step_completed` | Etapa concluída |
| `pipeline.step_failed` | Etapa falhou |

### Payload

```json
{
  "event": "project.preview_ready",
  "project_id": "uuid",
  "timestamp": "2026-01-23T11:30:00Z",
  "data": {
    "preview_url": "https://...",
    "subdomain": "dhv-group"
  }
}
```

---

*Última atualização: Janeiro 2026*
