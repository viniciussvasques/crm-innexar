# 📋 Análise Completa - Fluxo Manual de Onboarding

## ✅ O Que Já Existe

### Backend
- ✅ Modelo `SiteOrder` com status: `PENDING_PAYMENT`, `PAID`, `ONBOARDING_PENDING`, `BUILDING`, `GENERATING`, `REVIEW`, `DELIVERED`, `CANCELLED`
- ✅ Campo `preview_url` no modelo `SiteOrder` (linha 233)
- ✅ Modelo `SiteFeedback` para feedbacks/revisões
- ✅ Onboarding service que processa formulário
- ✅ Endpoint `PATCH /api/site-orders/{id}/status` para atualizar status
- ✅ Endpoint `POST /api/site-orders/{id}/build` para iniciar geração (atualmente automático)

### CRM Frontend (`/opt/innexar-crm/frontend`)
- ✅ Página `/site-orders` com Kanban e Table view
- ✅ Modal básico de detalhes do pedido
- ✅ Status config com cores e ícones
- ✅ Kanban mostra: `paid`, `building`, `generating`, `review`, `delivered`
- ✅ Componente `Modal` reutilizável
- ✅ Hook `useSiteOrders` para gerenciar estado

### Portal do Cliente (`/opt/innexar-website`)
- ✅ Dashboard `/portal` com lista de projetos
- ✅ Página de detalhes `/portal/projects/[id]`
- ✅ Timeline básica de progresso
- ✅ Layout com tema escuro
- ❌ **FALTA**: Modais de Preview, Revisão e Add-ons

## ❌ O Que Precisa Ser Implementado

### 1. Backend - Novos Status
- [ ] Adicionar `BRIEFING` ao enum `SiteOrderStatus`
- [ ] Adicionar `PREVIEW` ao enum `SiteOrderStatus`
- [ ] Atualizar `onboarding_service.py` para mudar status para `BRIEFING` (não `GENERATING`)

### 2. Backend - Novos Endpoints
- [ ] `PATCH /api/site-orders/{id}/preview-url` - Definir URL de preview
- [ ] `POST /api/site-orders/{id}/feedback` - Cliente solicita revisão
- [ ] `POST /api/site-orders/{id}/approve` - Cliente aprova site
- [ ] `GET /api/site-orders/{id}/timeline` - Histórico de eventos
- [ ] `GET /api/site-orders/{id}/feedbacks` - Lista de feedbacks

### 3. CRM Frontend - Melhorias
- [ ] Adicionar colunas `briefing` e `preview` no Kanban
- [ ] Criar modal de Briefing Detalhado com tabs:
  - Tab Briefing: Dados do onboarding formatados
  - Tab Timeline: Histórico de ações
  - Tab Feedbacks: Lista de revisões/comentários
  - Tab Arquivos: Uploads e deliverables
  - Tab Ações: Botões de status + campo preview_url
- [ ] Adicionar campo para definir `preview_url` no modal de detalhes
- [ ] Botão "Enviar para Preview" que muda status para `PREVIEW`

### 4. Portal do Cliente - Novos Modais
- [ ] **Modal de Preview** (`/portal/projects/[id]`):
  - iFrame ou link para staging
  - Botão "Aprovar Site"
  - Botão "Solicitar Revisão"
  - Mostrar quando status = `preview`
  
- [ ] **Modal de Revisão**:
  - Textarea para descrição dos ajustes
  - Upload de anexos (screenshots, referências)
  - Contador de revisões usadas/incluídas
  - Aviso quando revisões extras serão cobradas
  - Botão "Enviar Solicitação"
  
- [ ] **Modal de Add-ons**:
  - Lista de add-ons disponíveis
  - Preços
  - Checkout integrado (Stripe)
  - Botão "Adicionar ao Pedido"

### 5. Portal do Cliente - Dashboard
- [ ] Atualizar dashboard para mostrar ações baseadas no status:
  - `briefing`: "Briefing enviado, aguardando equipe"
  - `building`: "Site em construção"
  - `preview`: Botão "Revisar Site" que abre modal de preview
  - `review`: "Ajustes em andamento"
  - `delivered`: "Site online!"

## 🔄 Fluxo Manual Proposto

```
1. Cliente paga → Status: PAID
2. Cliente completa onboarding → Status: BRIEFING (equipe recebe)
3. Equipe revisa briefing → Status: BUILDING (equipe constrói manualmente)
4. Equipe define preview_url → Status: PREVIEW (cliente recebe notificação)
5. Cliente revisa no portal:
   - Se aprova → Status: DELIVERED
   - Se solicita revisão → Status: REVIEW (volta para equipe)
6. Equipe aplica ajustes → Status: PREVIEW (novamente)
7. Repete até aprovação ou limite de revisões
```

## 🎨 Tema Escuro

Ambos os frontends já usam tema escuro. Manter consistência:
- Background: `slate-950` / `slate-900`
- Cards: `white/5` com `backdrop-blur`
- Borders: `white/10`
- Accent: `blue-500` / `purple-500` gradient
- Success: `emerald-400`
- Warning: `amber-400`
- Error: `red-400`
