# 🧪 Teste do Fluxo Manual - Checklist

## ✅ Backend - Endpoints Criados

### 1. Status
- [x] `BRIEFING` adicionado ao enum
- [x] `PREVIEW` adicionado ao enum
- [x] Onboarding muda para `BRIEFING` (não `GENERATING`)

### 2. Endpoints
- [x] `PATCH /api/site-orders/{id}/preview-url` - Admin define preview URL
- [x] `POST /api/site-orders/{id}/feedback` - Cliente/Admin envia feedback
- [x] `POST /api/site-orders/{id}/approve` - Cliente aprova site
- [x] `GET /api/site-orders/{id}/feedbacks` - Lista feedbacks
- [x] `GET /api/site-orders/{id}/timeline` - Histórico de eventos

## ✅ Frontend CRM

### 1. Kanban
- [x] Colunas `briefing` e `preview` adicionadas
- [x] Status config atualizado

### 2. Modal de Detalhes
- [ ] Modal com tabs (PENDENTE - pode ser feito depois)

## ✅ Frontend Portal

### 1. Componentes Criados
- [x] `Modal.tsx` - Componente base
- [x] `PreviewModal.tsx` - Modal de preview com iframe
- [x] `RevisionModal.tsx` - Modal de revisão com upload

### 2. Página de Detalhes
- [x] Integração com modais
- [x] Botões contextuais baseados no status
- [x] Status config atualizado

### 3. Rotas de API
- [x] `/api/launch/customer/orders/[id]/approve`
- [x] `/api/launch/customer/orders/[id]/feedback`

## 🧪 Testes a Realizar

### 1. Fluxo Completo
1. [ ] Cliente completa onboarding → Status deve ser `BRIEFING`
2. [ ] Admin vê pedido em `BRIEFING` no Kanban
3. [ ] Admin muda status para `BUILDING` (manual)
4. [ ] Admin define `preview_url` → Status muda para `PREVIEW`
5. [ ] Cliente recebe email de preview disponível
6. [ ] Cliente acessa portal e vê botão "Review Website"
7. [ ] Cliente abre modal de preview
8. [ ] Cliente pode:
   - Aprovar → Status muda para `DELIVERED`
   - Solicitar revisão → Status muda para `REVIEW`
9. [ ] Se solicitar revisão, admin vê em `REVIEW`
10. [ ] Admin aplica ajustes e volta para `PREVIEW`
11. [ ] Processo repete até aprovação

### 2. Testes de Endpoints

#### Preview URL
```bash
curl -X PATCH http://localhost:8000/api/site-orders/1/preview-url \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"preview_url": "https://preview.example.com"}'
```

#### Feedback
```bash
curl -X POST http://localhost:8000/api/site-orders/1/feedback \
  -H "Authorization: Bearer <customer_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Change header color", "attachments": []}'
```

#### Approve
```bash
curl -X POST http://localhost:8000/api/site-orders/1/approve \
  -H "Authorization: Bearer <customer_token>" \
  -H "Content-Type: application/json" \
  -d '{"notes": ""}'
```

### 3. Testes de UI

#### Portal do Cliente
- [ ] Login funciona
- [ ] Dashboard mostra projetos
- [ ] Página de detalhes carrega corretamente
- [ ] Modal de preview abre quando status = `preview`
- [ ] Modal de revisão abre corretamente
- [ ] Botões contextuais aparecem baseados no status
- [ ] Upload de arquivos funciona (mockado por enquanto)

#### CRM
- [ ] Kanban mostra todas as colunas
- [ ] Cards aparecem nas colunas corretas
- [ ] Modal de detalhes abre
- [ ] Status pode ser atualizado manualmente

## 📝 Notas

- Upload de arquivos está mockado (apenas nomes de arquivos)
- Modal de briefing detalhado com tabs pode ser implementado depois
- Modal de add-ons pode ser implementado depois
- Dashboard do portal pode ser melhorado depois

## 🚀 Próximos Passos

1. Testar fluxo completo end-to-end
2. Implementar upload real de arquivos
3. Melhorar modal de detalhes no CRM
4. Adicionar modal de add-ons
5. Melhorar dashboard do portal
