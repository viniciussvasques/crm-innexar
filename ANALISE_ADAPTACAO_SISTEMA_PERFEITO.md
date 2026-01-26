# Análise: Adaptação ao Sistema "Perfeito"

## 📊 Comparação: Sistema Atual vs. Sistema Alvo

### 1. Arquitetura Atual vs. Alvo

#### ✅ O Que Já Temos

| Componente | Status Atual | Status Alvo | Gap |
|------------|--------------|-------------|-----|
| **Portal (Cliente)** | ✅ Parcial | ✅ Completo | Onboarding OK, falta chat + preview confiável |
| **CRM/Workspace** | ✅ Completo | ✅ Completo | Funcional, precisa melhorias |
| **Orchestrator API** | ✅ FastAPI | ✅ Python API | OK, precisa endpoints adicionais |
| **Workers (Fila)** | ✅ Celery | ✅ Workers | OK, precisa melhorias |
| **CI + Preview** | ❌ Não tem | ✅ Obrigatório | **GAP CRÍTICO** |
| **Observabilidade** | ⚠️ Básico | ✅ Completo | Logs OK, falta Sentry + tracing |
| **Storage** | ✅ Postgres | ✅ Postgres + S3/R2 | Postgres OK, falta S3/R2 |

#### 🔴 Gaps Críticos

1. **CI + Preview**: Não existe - preview atual é apenas API que serve arquivos
2. **Chat de Ajustes**: Não existe - apenas chat genérico
3. **Change Requests**: Não existe
4. **Revisions**: Existe campo mas não implementado
5. **Approvals**: Não existe
6. **Deployments**: Não existe
7. **GitHub Integration**: Não existe

---

## 2. Modelo de Dados: Comparação

### ✅ Tabelas Existentes

| Tabela Alvo | Tabela Atual | Status | Trabalho |
|-------------|--------------|--------|----------|
| `customers` | `site_customers` | ✅ Existe | Ajustar campos |
| `orders` | `site_orders` | ✅ Existe | Adicionar `sla_due_at` |
| `intakes` | `site_onboarding` | ✅ Existe | Renomear/adicionar `validated_at` |
| `pipeline_steps` | `site_generation_logs` | ⚠️ Parcial | **REFAZER** - precisa estrutura de steps |
| `jobs` | Celery tasks | ⚠️ Implícito | **CRIAR** tabela de jobs |
| `conversations` | `chat_threads` | ✅ Existe | Ajustar para order_id |
| `messages` | `chat_messages` | ✅ Existe | OK |
| `change_requests` | ❌ Não existe | ❌ | **CRIAR** |
| `revisions` | ❌ Não existe | ❌ | **CRIAR** |
| `approvals` | ❌ Não existe | ❌ | **CRIAR** |
| `deployments` | ❌ Não existe | ❌ | **CRIAR** |

### 📋 Trabalho de Modelo de Dados

**Estimativa**: 2-3 dias

1. Criar tabelas novas (change_requests, revisions, approvals, deployments)
2. Refatorar `pipeline_steps` (estrutura atual não é adequada)
3. Criar tabela `jobs` para rastreamento
4. Ajustar relacionamentos

---

## 3. Pipeline (State Machine): Comparação

### Pipeline Atual

```
PENDING_PAYMENT → PAID → ONBOARDING_PENDING → BUILDING → GENERATING → REVIEW → DELIVERED
```

### Pipeline Alvo

```
paid → intake_received → intake_validated → draft_generated → repo_prepared → 
preview_built → human_review_gate_1 → revision_round_1 → human_review_gate_2 → 
published → completed
```

### 🔴 Gaps

1. **State Machine Formal**: Não existe - apenas enum simples
2. **Etapas Detalhadas**: Pipeline atual é muito simples
3. **Idempotência**: Não garantida
4. **Retry por Etapa**: Não implementado
5. **Timeout + Cancelamento**: Não implementado
6. **SLA Tracking**: Não implementado

### 📋 Trabalho de Pipeline

**Estimativa**: 5-7 dias

1. Implementar state machine (usar `transitions` ou similar)
2. Criar tabela `pipeline_steps` com estrutura adequada
3. Implementar retry por etapa
4. Implementar timeout + cancelamento
5. Dashboard de SLA

---

## 4. Preview: Gap Crítico

### Situação Atual

- ✅ Arquivos gerados em `/app/generated_sites/project_{id}/`
- ✅ API serve arquivos (`/api/projects/{id}/preview`)
- ❌ **Não há CI/CD**
- ❌ **Não há build determinístico**
- ❌ **Não há preview por branch/commit**
- ❌ **Não há logs de build**

### Situação Alvo

- ✅ Toda mudança gera branch/commit
- ✅ CI faz build e publica preview
- ✅ Preview URL + logs URL salvos
- ✅ Build reproduzível

### 📋 Trabalho de Preview

**Estimativa**: 7-10 dias

1. **GitHub Integration** (3-4 dias)
   - Criar repositórios
   - Commitar mudanças
   - Gerenciar branches

2. **CI/CD Setup** (2-3 dias)
   - Cloudflare Pages ou Vercel
   - Webhook de deploy
   - Build automático

3. **Preview Management** (2-3 dias)
   - Salvar preview_url + logs_url
   - Exibir no portal/CRM
   - Histórico de previews

---

## 5. Chat e Change Requests: Não Existe

### Situação Atual

- ✅ Chat genérico existe (`chat_threads`, `chat_messages`)
- ❌ **Não está vinculado a orders**
- ❌ **Não gera Change Requests**
- ❌ **Não tem triagem IA**
- ❌ **Não tem roteamento auto/humano**

### Situação Alvo

- ✅ Chat vinculado a order
- ✅ Mensagem → Change Request
- ✅ Triagem IA automática
- ✅ Roteamento auto/humano/misto

### 📋 Trabalho de Chat + CR

**Estimativa**: 10-12 dias

1. **Integração Chat + Orders** (2 dias)
   - Vincular chat a order
   - UI no portal

2. **Change Request System** (4-5 dias)
   - Modelo de dados
   - API endpoints
   - UI no CRM

3. **Triagem IA** (3-4 dias)
   - Análise de mensagem
   - Classificação (copy/layout/assets/etc)
   - Decisão auto/humano

4. **Roteamento** (1-2 dias)
   - Auto-safe: IA aplica
   - Humano: cria tarefa
   - Misto: IA propõe, humano valida

---

## 6. Política Auto vs. Humano: Não Existe

### Situação Atual

- ❌ **Tudo é manual**
- ❌ **Não há classificação de mudanças**
- ❌ **Não há gates de segurança**

### Situação Alvo

- ✅ Auto-safe: textos, CTAs, contatos, SEO simples
- ✅ Humano obrigatório: layout grande, integrações, temas sensíveis
- ✅ Misto: IA propõe, humano valida

### 📋 Trabalho de Política

**Estimativa**: 3-4 dias

1. Implementar regras de classificação
2. Implementar gates de segurança
3. UI para aprovação humana
4. Logs de decisões

---

## 7. UX Portal: Comparação

### ✅ O Que Temos

- ✅ Order Home (status + timeline)
- ✅ Onboarding (progressivo)
- ❌ Chat de ajustes (não vinculado)
- ❌ Aprovação (não existe)
- ❌ Entrega (básico)

### 🔴 O Que Falta

1. **Timeline com timestamps**: Parcial
2. **Notificações**: Não existe
3. **Histórico de revisões**: Não existe
4. **Preview links**: Não funcional
5. **Checklist de aprovação**: Não existe

### 📋 Trabalho de UX Portal

**Estimativa**: 5-7 dias

1. Melhorar timeline
2. Sistema de notificações
3. Histórico de revisões
4. Preview funcional
5. Checklist de aprovação

---

## 8. UX CRM: Comparação

### ✅ O Que Temos

- ✅ Fila de orders
- ✅ Detalhe da order
- ✅ Timeline + logs
- ❌ CRs pendentes (não existe)
- ❌ Inbox de CRs (não existe)
- ❌ Checklist de QA (não existe)
- ❌ Audit log (não existe)

### 📋 Trabalho de UX CRM

**Estimativa**: 4-6 dias

1. Inbox de Change Requests
2. Checklist de QA
3. Audit log
4. Melhorias na fila

---

## 9. Observabilidade: Comparação

### Situação Atual

- ✅ Logs estruturados (básico)
- ❌ **Sentry**: Não configurado
- ❌ **Tracing**: Não existe
- ❌ **Painel de falhas**: Não existe

### 📋 Trabalho de Observabilidade

**Estimativa**: 3-4 dias

1. Configurar Sentry
2. Implementar OpenTelemetry
3. Painel de falhas por etapa
4. Melhorar logs (error_code, error_context, logs_url)

---

## 10. Segurança: Comparação

### Situação Atual

- ✅ RBAC básico
- ⚠️ **Build isolado**: Não (executa no worker)
- ⚠️ **Validação de uploads**: Parcial
- ⚠️ **Rate limit**: Não implementado

### 📋 Trabalho de Segurança

**Estimativa**: 2-3 dias

1. Isolar builds (CI/container)
2. Validação robusta de uploads
3. Rate limit no chat e endpoints

---

## 📊 Resumo: Estimativa de Trabalho

### Fase 1: MVP Robusto (Prioridade Alta)

| Item | Estimativa | Dependências |
|------|------------|--------------|
| **Pipeline + Steps** | 5-7 dias | - |
| **Fila de Jobs** | 2-3 dias | Pipeline |
| **Preview via CI** | 7-10 dias | GitHub Integration |
| **Portal Timeline + Preview** | 3-4 dias | Preview via CI |
| **CRM Retry + Logs** | 2-3 dias | Pipeline |
| **Modelo de Dados** | 2-3 dias | - |
| **TOTAL FASE 1** | **21-30 dias** | ~1 mês |

### Fase 2: Chat + CR

| Item | Estimativa | Dependências |
|------|------------|--------------|
| **Chat + Orders** | 2 dias | - |
| **Change Request System** | 4-5 dias | Modelo de Dados |
| **Triagem IA** | 3-4 dias | Chat |
| **Roteamento** | 1-2 dias | CR System |
| **TOTAL FASE 2** | **10-13 dias** | ~2 semanas |

### Fase 3: Automação Segura

| Item | Estimativa | Dependências |
|------|------------|--------------|
| **Política Auto/Humano** | 3-4 dias | CR System |
| **IA Aplica Auto-safe** | 4-5 dias | Política |
| **Gates Humanos** | 2-3 dias | Política |
| **Checklist** | 2 dias | Gates |
| **TOTAL FASE 3** | **11-14 dias** | ~2 semanas |

### Fase 4: Melhorias

| Item | Estimativa | Dependências |
|------|------------|--------------|
| **Observabilidade** | 3-4 dias | - |
| **Segurança** | 2-3 dias | - |
| **UX Melhorias** | 5-7 dias | - |
| **TOTAL FASE 4** | **10-14 dias** | ~2 semanas |

### 📈 TOTAL GERAL

**Estimativa Total**: **52-71 dias** (~2.5-3.5 meses)

**Com 1 desenvolvedor full-time**: ~3 meses
**Com 2 desenvolvedores**: ~1.5-2 meses

---

## 🎯 Recomendações de Implementação

### Prioridade 1: MVP Robusto (Fase 1)

**Por quê**: Base para tudo funcionar profissionalmente

**Inclui**:
- Pipeline formal com steps
- Preview via CI (crítico)
- Jobs rastreados
- Timeline funcional

**Tempo**: 1 mês

### Prioridade 2: Chat + CR (Fase 2)

**Por quê**: Diferencial competitivo

**Inclui**:
- Chat vinculado a orders
- Change Requests
- Triagem IA

**Tempo**: 2 semanas

### Prioridade 3: Automação (Fase 3)

**Por quê**: Escala e eficiência

**Inclui**:
- Auto-safe
- Gates humanos
- Checklist

**Tempo**: 2 semanas

### Prioridade 4: Polimento (Fase 4)

**Por quê**: Profissionalismo

**Inclui**:
- Observabilidade
- Segurança
- UX refinada

**Tempo**: 2 semanas

---

## 🔧 Decisões Técnicas Necessárias

### 1. State Machine

**Opção A**: Biblioteca `transitions` (Python)
- ✅ Fácil de usar
- ✅ Suporta callbacks
- ⚠️ Dependência adicional

**Opção B**: Implementação própria
- ✅ Sem dependências
- ❌ Mais trabalho

**Recomendação**: `transitions`

### 2. CI/CD Provider

**Opção A**: Cloudflare Pages
- ✅ Integração fácil
- ✅ Preview automático
- ✅ Grátis para começar

**Opção B**: Vercel
- ✅ Integração fácil
- ✅ Preview automático
- ⚠️ Limites no plano grátis

**Opção C**: GitHub Actions + Self-hosted
- ✅ Controle total
- ❌ Mais complexo

**Recomendação**: Cloudflare Pages (já usa Cloudflare)

### 3. Storage de Assets

**Opção A**: Cloudflare R2
- ✅ Integração com Cloudflare
- ✅ CDN integrado
- ✅ Compatível com S3

**Opção B**: AWS S3
- ✅ Padrão da indústria
- ⚠️ Mais caro

**Recomendação**: Cloudflare R2

### 4. Observabilidade

**Opção A**: Sentry (erros) + OpenTelemetry (tracing)
- ✅ Padrão da indústria
- ✅ Fácil integração

**Opção B**: Rollbar + Datadog
- ⚠️ Mais caro

**Recomendação**: Sentry + OpenTelemetry

---

## 📝 Checklist de Implementação

### Fase 1: MVP Robusto

- [ ] Criar tabelas: `pipeline_steps`, `jobs`, `revisions`, `approvals`, `deployments`
- [ ] Implementar state machine
- [ ] GitHub Integration (criar repos, commits, branches)
- [ ] CI/CD Setup (Cloudflare Pages)
- [ ] Preview Management (salvar URLs, exibir)
- [ ] Jobs tracking (tabela + UI)
- [ ] Timeline melhorada (com timestamps)
- [ ] Retry por etapa
- [ ] Timeout + cancelamento

### Fase 2: Chat + CR

- [ ] Vincular chat a orders
- [ ] Criar tabela `change_requests`
- [ ] API de Change Requests
- [ ] UI de CR no CRM
- [ ] Triagem IA (análise de mensagem)
- [ ] Classificação de CR (tipo, escopo)
- [ ] Roteamento auto/humano/misto

### Fase 3: Automação

- [ ] Regras de classificação (auto-safe vs. humano)
- [ ] Gates de segurança
- [ ] IA aplica mudanças auto-safe
- [ ] UI de aprovação humana
- [ ] Checklist de QA
- [ ] Logs de decisões

### Fase 4: Polimento

- [ ] Configurar Sentry
- [ ] Implementar OpenTelemetry
- [ ] Painel de falhas
- [ ] Sistema de notificações
- [ ] Audit log
- [ ] Rate limiting
- [ ] Validação robusta de uploads

---

## 💡 Conclusão

### Situação Atual

✅ **Base sólida**: FastAPI, Celery, Postgres, Frontend
⚠️ **Falta estrutura profissional**: Pipeline formal, CI/CD, CR system

### Trabalho Necessário

**Estimativa**: 2.5-3.5 meses (1 dev) ou 1.5-2 meses (2 devs)

**Prioridade**:
1. **Fase 1 (MVP)**: Crítico - 1 mês
2. **Fase 2 (Chat+CR)**: Importante - 2 semanas
3. **Fase 3 (Automação)**: Diferencial - 2 semanas
4. **Fase 4 (Polimento)**: Profissionalismo - 2 semanas

### Recomendação

**Começar pela Fase 1 (MVP Robusto)**:
- Pipeline formal
- Preview via CI
- Jobs rastreados

Isso já transforma o sistema em algo profissional e funcional. As outras fases podem ser implementadas incrementalmente.
