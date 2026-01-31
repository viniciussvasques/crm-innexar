# ✅ Implementação do Fluxo Manual - Status

## Backend - ✅ Completo

### 1. Novos Status Adicionados
- ✅ `BRIEFING` - Após onboarding completo, aguardando equipe revisar
- ✅ `PREVIEW` - Preview disponível para cliente revisar

### 2. Onboarding Service Atualizado
- ✅ Mudou de `GENERATING` (automático) para `BRIEFING` (manual)
- ✅ Removida geração automática após onboarding
- ✅ Equipe recebe briefing e constrói manualmente

### 3. Novos Endpoints Criados
- ✅ `PATCH /api/site-orders/{id}/preview-url` - Define URL de preview e muda status para PREVIEW
- ✅ `POST /api/site-orders/{id}/feedback` - Cliente ou admin envia feedback/revisão
- ✅ `POST /api/site-orders/{id}/approve` - Cliente aprova o site
- ✅ `GET /api/site-orders/{id}/feedbacks` - Lista todos os feedbacks
- ✅ `GET /api/site-orders/{id}/timeline` - Histórico de eventos do pedido

### 4. Modelos Atualizados
- ✅ Relacionamento `feedbacks` adicionado ao `SiteOrder`
- ✅ Campo `preview_url` já existia no modelo

## Frontend CRM - ⚠️ Parcial

### 1. Kanban Atualizado
- ✅ Adicionadas colunas `briefing` e `preview`
- ✅ Status config atualizado com novos status

### 2. Modal de Detalhes
- ⚠️ **PENDENTE**: Criar modal com tabs:
  - Tab Briefing: Dados do onboarding formatados
  - Tab Timeline: Histórico de eventos
  - Tab Feedbacks: Lista de revisões/comentários
  - Tab Arquivos: Uploads e deliverables
  - Tab Ações: Botões de status + campo preview_url

## Frontend Portal - ❌ Pendente

### 1. Modais
- ❌ Modal de Preview (com iframe e botões Aprovar/Solicitar Revisão)
- ❌ Modal de Revisão (com textarea, upload e contador)
- ❌ Modal de Add-ons (com lista e checkout)

### 2. Dashboard
- ❌ Atualizar para mostrar ações baseadas no status
- ❌ Botões contextuais baseados no status atual

## Próximos Passos

1. **Completar Modal de Detalhes no CRM** com tabs
2. **Criar modais no Portal do Cliente**
3. **Atualizar dashboard do Portal** com ações contextuais
4. **Testar fluxo completo** end-to-end
