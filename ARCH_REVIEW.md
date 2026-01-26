# Architecture Review

## Checklist
- [x] Separação correta (UI / domain / infra) - *Backend segue padrão Service/Repo. Frontend usa App Router.*
- [ ] Backend sem lógica no controller - *Violado: `site_orders.py` contém lógica CRUD direta.*
- [ ] Front sem lógica de negócio pesada - *Violado: `site-orders/page.tsx` (37KB) contém lógica de Timeline e State complexo.*
- [x] Integrações isoladas - *Services existem para Stripe, AI, Email.*
- [x] IA não executa comandos - *Backend orquestra, IA apenas gera conteúdo.*
- [x] Secrets fora do código - *Nenhum secret hardcoded encontrado.*

## Problemas Identificados

### Backend
- **Fat Controller**: `api/site_orders.py` implementa CRUD de Addons e Templates diretamente via `db.execute`, contornando repositórios.
- **Service Bypass**: Ligas de leitura simples (`get_onboarding`) feitas no controller.

### Frontend
- **Monolithic Page**: `src/app/site-orders/page.tsx` é excessivamente grande (37KB).
    - Mistura lógica de visualização (Kanban/Table) com lógica de negócia (Cálculo de Steps da Timeline).
    - Chamadas de API diretas no componente em vez de Custom Hooks ou Services.
- **State Management**: Estado complexo (`orders`, `stats`, `selectedOrder`, `logs`) gerenciado localmente sem Context/React Query.
