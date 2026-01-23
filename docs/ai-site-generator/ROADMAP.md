# Roadmap - AI Site Generator

## Visão Geral do Timeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ROADMAP AI SITE GENERATOR                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Fase 1        Fase 2        Fase 3        Fase 4        Fase 5        Fase 6
│  ━━━━━━        ━━━━━━        ━━━━━━        ━━━━━━        ━━━━━━        ━━━━━━
│  Config &      Pipeline      Conteúdo      Código        Deploy        Revisão
│  Integr.       Básico        IA            IA            Preview       & Polish
│                                                                              │
│  [2 sem]       [2 sem]       [2 sem]       [3 sem]       [1 sem]       [2 sem]
│                                                                              │
│  Jan W4        Fev W2        Fev W4        Mar W3        Mar W4        Abr W2
│  ─────         ─────         ─────         ─────         ─────         ─────
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Fase 1: Configurações e Integrações
**Duração:** 2 semanas
**Período:** Semana 4 de Janeiro - Semana 1 de Fevereiro

### Objetivos
- Criar infraestrutura de configurações
- Implementar página de integrações no CRM
- Configurar todas as APIs externas

### Tarefas

#### Backend
- [ ] Criar tabela `integration_config` no PostgreSQL
- [ ] Criar modelo Pydantic para cada integração
- [ ] Implementar endpoints CRUD para configs
- [ ] Implementar endpoint de teste para cada integração
- [ ] Criar service layer para cada integração (GitHub, Cloudflare, AI)
- [ ] Implementar encryption para secrets

#### Frontend (CRM)
- [ ] Criar página Settings > Integrations
- [ ] Componente de card para cada integração
- [ ] Modais de edição com formulários
- [ ] Indicadores de status (connected/error)
- [ ] Botão de teste com feedback
- [ ] Exibição de logs de teste

#### Integrações a Configurar
- [ ] GitHub (Personal Access Token, org, templates)
- [ ] Cloudflare (API token, account, zone, R2)
- [ ] AI Models (providers, keys, models por tarefa)
- [ ] Storage R2 (bucket, credentials)

### Entregáveis
- Página de integrações funcional
- Todas as APIs testáveis
- Secrets criptografados no banco

### Dependências
- Acesso às APIs (tokens, keys)
- Definição de templates base no GitHub

---

## Fase 2: Pipeline Básico
**Duração:** 2 semanas
**Período:** Semana 2 - Semana 3 de Fevereiro

### Objetivos
- Implementar sistema de filas
- Criar estrutura de pipeline
- Implementar etapas A (Ingestão)

### Tarefas

#### Infraestrutura
- [ ] Configurar Redis para filas
- [ ] Configurar Celery workers
- [ ] Criar tabelas: `project`, `pipeline_step`, `artifact`
- [ ] Implementar logging estruturado
- [ ] Configurar retry policies

#### Backend
- [ ] Endpoint `POST /projects` (criar projeto)
- [ ] Endpoint `POST /projects/{id}/generate` (iniciar pipeline)
- [ ] Endpoint `GET /projects/{id}/pipeline` (status)
- [ ] Task: `validate_onboarding`
- [ ] Task: `download_assets`
- [ ] Task: `create_site_spec`
- [ ] Notificações via webhook

#### Frontend (CRM + Portal)
- [ ] Visualização de pipeline no projeto
- [ ] Status em tempo real (polling ou websocket)
- [ ] Logs de cada etapa
- [ ] Botões de ação (pausar, retry)

### Entregáveis
- Pipeline executando etapa A
- Dashboard de monitoramento
- Assets salvos no R2

---

## Fase 3: Geração de Conteúdo (IA)
**Duração:** 2 semanas
**Período:** Semana 4 de Fevereiro - Semana 1 de Março

### Objetivos
- Implementar geração de documentação via IA
- Criar artefatos de conteúdo

### Tarefas

#### AI Service
- [ ] Criar módulo `ai_service.py`
- [ ] Implementar prompt templates
- [ ] Implementar JSON schema validation
- [ ] Rate limiting e retry

#### Backend Tasks
- [ ] Task: `generate_brief`
- [ ] Task: `generate_sitemap`
- [ ] Task: `generate_content`
- [ ] Armazenar artefatos no R2/DB

#### Conteúdo a Gerar
- [ ] Brief (Markdown)
- [ ] Sitemap (JSON)
- [ ] Content por página (JSON)
- [ ] Checklist de pendências

#### Prompts
- [ ] Prompt para análise de onboarding
- [ ] Prompt para geração de copy
- [ ] Prompt para estrutura de páginas
- [ ] Prompt para CTAs e headlines

### Entregáveis
- Documentação gerada automaticamente
- Artefatos visualizáveis no painel
- Validação de qualidade

---

## Fase 4: Geração de Código (IA)
**Duração:** 3 semanas
**Período:** Semana 2 - Semana 4 de Março

### Objetivos
- Implementar geração de código via IA
- Criar sistema de patches
- Implementar build runner

### Tarefas

#### Template Base
- [ ] Criar template Next.js base
- [ ] Definir estrutura de pastas
- [ ] Definir allowlist de arquivos
- [ ] Criar componentes base

#### AI Service
- [ ] Prompt para layout plan
- [ ] Prompt para geração de patches
- [ ] Validação de diffs
- [ ] Correção automática de erros

#### Build Runner
- [ ] Criar container Docker para builds
- [ ] Implementar git operations
- [ ] Implementar patch application
- [ ] Implementar npm build
- [ ] Implementar testes básicos

#### Backend Tasks
- [ ] Task: `provision_repository`
- [ ] Task: `generate_layout_plan`
- [ ] Task: `generate_code_patch`
- [ ] Task: `apply_patch`
- [ ] Task: `build_and_test`

### Entregáveis
- Código gerado automaticamente
- Build passando
- Repositório criado no GitHub

---

## Fase 5: Deploy e Preview
**Duração:** 1 semana
**Período:** Semana 4 de Março

### Objetivos
- Implementar deploy automático
- Criar subdomínios dinâmicos
- Notificar cliente

### Tarefas

#### Cloudflare Integration
- [ ] Deploy para Cloudflare Pages
- [ ] Criar DNS records dinâmicamente
- [ ] Configurar SSL automático

#### Backend Tasks
- [ ] Task: `deploy_preview`
- [ ] Task: `provision_subdomain`
- [ ] Notificação para cliente
- [ ] Notificação para workspace

#### Frontend
- [ ] Botão "Ver Preview" no portal
- [ ] Link acessível no painel
- [ ] Status de deploy

### Entregáveis
- Preview funcionando
- Subdomínio configurado
- Cliente notificado

---

## Fase 6: Revisão e Polish
**Duração:** 2 semanas
**Período:** Semana 1 - Semana 2 de Abril

### Objetivos
- Implementar ciclo de revisão
- Implementar aprovação
- Polir UX

### Tarefas

#### Backend
- [ ] Criar tabela `revision_request`
- [ ] Endpoint para solicitar alterações
- [ ] Endpoint para aprovar
- [ ] Task: `process_revision`
- [ ] Task: `generate_revision_patch`

#### Frontend (Portal)
- [ ] Formulário de solicitação de alterações
- [ ] Histórico de revisões
- [ ] Botão de aprovação
- [ ] Download de artefatos

#### Workspace Integration
- [ ] Criar tickets para revisões
- [ ] Notificações de aprovação
- [ ] Handoff checklist

### Entregáveis
- Ciclo de revisão completo
- Aprovação funcionando
- Entrega final

---

## Milestones

| Milestone | Data | Descrição |
|-----------|------|-----------|
| M1 | Fim de Jan | Integrações configuradas |
| M2 | Fim de Fev | Pipeline básico + conteúdo |
| M3 | Meados Mar | Código gerado automaticamente |
| M4 | Fim de Mar | Preview deployado |
| M5 | Meados Abr | Sistema completo em produção |

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| IA gera código com bugs | Alta | Alto | Build obrigatório, retry, fallback humano |
| Rate limit de APIs | Média | Médio | Caching, queue throttling |
| Custos de IA elevados | Média | Médio | Monitoramento, limites por projeto |
| Templates muito complexos | Baixa | Alto | Começar simples, iterar |

---

## Métricas de Sucesso

| Métrica | Meta Fase 1 | Meta Final |
|---------|-------------|------------|
| Tempo por projeto | - | < 2 horas |
| Taxa de sucesso | > 70% | > 90% |
| Revisões por projeto | - | < 3 |
| Custo de IA por projeto | - | < $5 |

---

*Última atualização: Janeiro 2026*
