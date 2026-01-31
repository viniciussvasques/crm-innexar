---
description: Fluxo Manual de Construção de Sites - Pipeline Completo
---

# 🚀 Fluxo Manual de Construção de Sites Innexar

## Visão Geral do Pipeline

```
CLIENTE                           EQUIPE INNEXAR                    CLIENTE (PORTAL)
   │                                    │                                │
   ▼                                    │                                │
┌──────────┐                            │                                │
│  PAGA    │ ──────────────────────────▶│                                │
│ (Stripe) │                            │                                │
└──────────┘                            │                                │
   │                                    │                                │
   ▼                                    │                                │
┌──────────┐                            │                                │
│ONBOARDING│ ──────────────────────────▶│                                │
│ (Form)   │                     ┌──────┴──────┐                         │
└──────────┘                     │  CRM ADMIN  │                         │
                                 │  (Kanban)   │                         │
                                 └──────┬──────┘                         │
                                        │                                │
                                        ▼                                │
                              ┌─────────────────┐                        │
                              │ 1. BRIEFING     │ ────────────────────────▶ Visualiza Briefing
                              │ (Modal Detalhes)│                        │
                              └────────┬────────┘                        │
                                       │                                 │
                                       ▼                                 │
                              ┌─────────────────┐                        │
                              │ 2. BUILDING     │ ────────────────────────▶ Status: Em Construção
                              │ (Dev trabalha)  │                        │
                              └────────┬────────┘                        │
                                       │                                 │
                                       ▼                                 │
                              ┌─────────────────┐                        │
                              │ 3. PREVIEW      │ ────────────────────────▶ Link de Preview
                              │ (Staging URL)   │                        │  + Modal de Feedback
                              └────────┬────────┘                        │
                                       │                                 │
                                       ▼                                 │
                              ┌─────────────────┐                        │
                              │ 4. REVISÕES     │◄────────────────────────  Solicita Ajustes
                              │ (Max N incluso) │                        │  (Modal de Revisão)
                              └────────┬────────┘                        │
                                       │                                 │
                                       ▼                                 │
                              ┌─────────────────┐                        │
                              │ 5. DELIVERED    │ ────────────────────────▶ Site Aprovado!
                              │ (Produção)      │                        │  URL Final
                              └─────────────────┘                        │
```

## Status do Pedido (Pipeline)

| Status | Descrição | Ação Admin | Visão Cliente |
|--------|-----------|------------|---------------|
| `paid` | Pagamento confirmado | Aguardando onboarding | "Pagamento confirmado" |
| `onboarding_pending` | Aguardando formulário | Lembrar cliente | "Complete seu formulário" |
| `briefing` | Onboarding completo | Revisar briefing | "Briefing enviado" |
| `building` | Em desenvolvimento | Construindo site | "Em construção" |
| `preview` | Preview disponível | Aguardando feedback | "Revise seu site" |
| `revision` | Cliente solicitou ajustes | Aplicar revisões | "Ajustes em andamento" |
| `delivered` | Entregue e aprovado | Monitorar | "Site online!" |
| `cancelled` | Cancelado | - | "Cancelado" |

## Componentes a Implementar

### 1. CRM Admin Panel (`/opt/innexar-crm/frontend`)

#### 1.1 Kanban Board Atualizado
- [x] Colunas: Paid → Briefing → Building → Preview → Revision → Delivered
- [ ] Drag-and-drop entre colunas
- [ ] Cards com informações resumidas
- [ ] Indicador de tempo no status

#### 1.2 Modal de Detalhes do Pedido
- [ ] **Tab Briefing**: Dados do onboarding formatados
- [ ] **Tab Timeline**: Histórico de ações
- [ ] **Tab Feedbacks**: Lista de revisões/comentários
- [ ] **Tab Arquivos**: Uploads e deliverables
- [ ] **Tab Ações**: Botões de status + URL fields

#### 1.3 Modal de Briefing Expandido
- [ ] Visualização completa dos dados do onboarding
- [ ] Cores, fontes, referências visuais
- [ ] Serviços, diferenciais, CTAs
- [ ] Botão "Copiar para Clipboard"

#### 1.4 Notificações
- [x] Email para equipe quando onboarding completo
- [ ] Email para cliente quando status muda
- [ ] Dashboard de notificações

### 2. Portal do Cliente (`/opt/innexar-website`)

#### 2.1 Dashboard Principal
- [ ] Card de status com progresso visual
- [ ] Timeline de etapas
- [ ] Informações do briefing enviado
- [ ] CTA baseado no status atual

#### 2.2 Modal de Preview
- [ ] iFrame ou link para staging
- [ ] Botão "Aprovar"
- [ ] Botão "Solicitar Revisão"

#### 2.3 Modal de Revisão
- [ ] Textarea para descrição
- [ ] Upload de anexos (screenshots, referências)
- [ ] Contador de revisões usadas/incluídas
- [ ] Aviso quando revisões extras serão cobradas

#### 2.4 Modal de Add-ons
- [ ] Lista de add-ons disponíveis
- [ ] Preços
- [ ] Checkout integrado (Stripe)

### 3. Backend Adjustments (`/opt/innexar-crm/backend`)

#### 3.1 Novos Status
- [x] `briefing` - Após onboarding
- [x] `preview` - Site em staging
- [x] `revision` - Cliente solicitou ajustes

#### 3.2 Endpoints
- [x] `POST /{order_id}/feedback` - Solicitar revisão
- [x] `POST /{order_id}/approve` - Aprovar site
- [ ] `PATCH /{order_id}/preview-url` - Definir URL de preview
- [ ] `GET /{order_id}/timeline` - Histórico de eventos
- [ ] `POST /{order_id}/addons` - Adicionar extras

#### 3.3 Emails Automáticos
- [x] Confirmação de pagamento
- [x] Notificação para equipe (onboarding)
- [ ] Status atualizado para cliente
- [ ] Preview disponível
- [ ] Site entregue

## Tema Escuro

Ambos os frontends já usam tema escuro. Garantir consistência:

- Background: `slate-950` / `slate-900`
- Cards: `white/5` com `backdrop-blur`
- Borders: `white/10`
- Accent: `blue-500` / `purple-500` gradient
- Success: `emerald-400`
- Warning: `amber-400`
- Error: `red-400`

## Implementação - Ordem de Prioridade

### Fase 1: Pipeline Básico ✅
1. [x] Status enum atualizado
2. [x] Kanban com todos os status
3. [x] Email para equipe
4. [x] Endpoint de feedback

### Fase 2: Portal do Cliente
1. [ ] Dashboard com status visual
2. [ ] Modal de preview
3. [ ] Modal de revisão
4. [ ] Contador de revisões

### Fase 3: CRM Enhancements
1. [ ] Modal de briefing detalhado
2. [ ] Timeline de eventos
3. [ ] Campo de preview URL
4. [ ] Arrastar cards no Kanban

### Fase 4: Comunicação
1. [ ] Emails de status
2. [ ] Notificações in-app
3. [ ] Sistema de mensagens
