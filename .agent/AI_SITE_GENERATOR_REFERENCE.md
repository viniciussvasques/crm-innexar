# AI Site Generator - System Reference & Change Log

> **IMPORTANTE**: Este documento deve ser lido antes de qualquer trabalho no sistema AI Site Generator.

---

## 📋 Overview do Sistema

O **AI Site Generator** é um sistema para criação automatizada de websites usando IA. Consiste em dois projetos:

| Projeto | Path | Função |
|---------|------|--------|
| **CRM Backend** | `innexar-crm/backend` | API FastAPI - gerencia orders, onboarding, geração |
| **CRM Frontend** | `innexar-crm/frontend` | Dashboard admin Next.js |
| **Site de Vendas** | `site-innexar` | Landing page + checkout Stripe |

---

## 🔄 Fluxo Completo do Cliente

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. COMPRA                                                        │
├─────────────────────────────────────────────────────────────────┤
│ Cliente → site-innexar (Landing) → Checkout Stripe → Pagamento │
│                                                                  │
│ Stripe envia webhook → site-innexar/api/launch/webhook          │
│ Webhook chama → CRM/api/site-orders (POST) → Cria Order        │
│ Webhook chama → CRM/api/emails/send-payment-confirmation        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. ONBOARDING                                                   │
├─────────────────────────────────────────────────────────────────┤
│ Cliente recebe email com link → innexar.com/onboarding/{id}     │
│ Preenche formulário (7 steps) → POST /site-orders/{id}/onboarding │
│ Sistema cria conta via create_customer_account()                │
│ Status muda para BUILDING                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. GERAÇÃO (Atual: Manual | Planejado: Automático)             │
├─────────────────────────────────────────────────────────────────┤
│ Admin clica "Build" → POST /site-orders/{id}/build              │
│ SiteGeneratorService.generate_site(order_id)                   │
│ - Monta prompt com dados do onboarding                          │
│ - Chama IA (task_type="coding")                                 │
│ - Salva arquivos em generated_sites/{order_id}/                 │
│ - Status muda para REVIEW                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura de Arquivos Chave

### Backend (FastAPI)
```
backend/app/
├── api/
│   ├── site_orders.py      # CRUD orders, onboarding, /build
│   ├── site_customers.py   # create_customer_account()
│   ├── ai_config.py        # Configurações de IA, /router-rules
│   ├── emails.py           # send-payment-confirmation
│   └── webhooks.py         # Webhooks de contato (NÃO Stripe)
├── services/
│   └── site_generator_service.py  # Geração via IA
└── models/
    └── site_order.py       # SiteOrder, SiteOnboarding, etc
```

### Frontend Next.js (Proxy API Routes)
```
frontend/src/app/api/
├── site-orders/
│   ├── route.ts           # GET/POST /site-orders
│   ├── [id]/route.ts      # GET/PUT/PATCH /{id}
│   ├── [id]/status/route.ts   # PATCH /{id}/status ✅ CRIADO
│   └── [id]/build/route.ts    # POST /{id}/build ✅ CRIADO
├── ai-config/
│   ├── router-rules/route.ts  # GET/POST ✅ CRIADO
│   └── [id]/route.ts      # PUT/DELETE (cuidado: dynamic route)
```

### Site de Vendas
```
site-innexar/src/app/api/
└── launch/webhook/route.ts  # Stripe webhook handler ✅
```

---

## 🔧 Problemas Conhecidos e Soluções

### Route Shadowing (405 Method Not Allowed)
**Problema**: Next.js `[id]/route.ts` captura paths como `router-rules` como IDs
**Solução**: Criar rotas explícitas (ex: `router-rules/route.ts`) que têm precedência

### Deploy não atualiza
**Problema**: Container rodando código antigo
**Solução**: Verificar com `docker exec {container} grep "string" /app/...`

---

## 📝 Change Log

### 2026-01-23

#### Correção 405 em /routing (agora /router-rules)
- **Problema**: GET/POST `/api/ai-config/routing` retornava 405
- **Causa raiz**: Next.js `[id]/route.ts` capturava `routing` como ID
- **Correção**:
  1. Backend: Renomeado `/routing` → `/router-rules` em `ai_config.py`
  2. Frontend: Criado `router-rules/route.ts` com GET/POST handlers
  3. Atualizado `settings/page.tsx` para usar novo endpoint
- **Commits**: `ae625e8`, `3fb6cce`, `371058f`

#### Correção 404 em /site-orders/{id}/build e /status
- **Problema**: Endpoints não existiam
- **Correção**:
  1. Backend: Adicionado `POST /{order_id}/build` em `site_orders.py`
  2. Frontend: Criado `[id]/build/route.ts` e `[id]/status/route.ts`
- **Commit**: `506ecb3`

#### Auditoria de Fluxo
- Confirmado: Stripe webhook existe em `site-innexar`
- Gap identificado: IA não ativa automaticamente após onboarding
- **Pendente**: Implementar auto-trigger de IA

#### Auto-Trigger IA após Onboarding
- **Problema**: Admin precisava clicar manualmente em "Build"
- **Correção**: Adicionado `background_tasks.add_task(service.generate_site, order.id)` em `submit_onboarding()`
- **Arquivo**: `backend/app/api/site_orders.py` linhas 485-487
- **Commit**: (pendente)

---

## 🖥️ Visual IDE

### Componentes Existentes
| Arquivo | Função |
|---------|-------|
| `VisualEditor/index.tsx` | Componente principal com sidebar, editor, preview |
| `VisualEditor/FileTree.tsx` | Navegação de arquivos |
| `VisualEditor/CodeEditor.tsx` | Editor Monaco |
| `app/projects/[id]/ide/page.tsx` | Página `/projects/{id}/ide` |

### Backend de Arquivos
- **Endpoint**: `GET/POST /api/projects/{project_id}/files`
- **Diretório**: `generated_sites/project_{project_id}/`

### ✅ Problema Resolvido
- **Generator agora salva em**: `generated_sites/project_{order.id}/`
- **IDE busca em**: `generated_sites/project_{project_id}/`
- **Commit**: (pendente)

---

## 🚧 Pendências

- [x] ~~Auto-trigger IA após onboarding~~ ✅ IMPLEMENTADO
- [ ] Notificação por email quando site pronto para review
- [ ] Visual IDE para edição de código gerado

---

## 🔑 Variáveis de Ambiente Importantes

| Variável | Uso |
|----------|-----|
| `CRM_API_URL` | URL do backend CRM (usado pelo site-innexar) |
| `STRIPE_SECRET_KEY` | Chave secreta do Stripe |
| `STRIPE_WEBHOOK_SECRET` | Secret para validar webhooks |
| `BACKEND_URL` | URL do backend (usado pelo frontend Next.js) |

---

*Última atualização: 2026-01-23*
