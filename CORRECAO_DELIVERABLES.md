# Correção: Deliverables Não Aparecem no Frontend

## Problema Identificado

**Sintoma**: "nenhum item da jornada funciona" - os detalhes das fases (briefing, sitemap, etc.) não aparecem no frontend, mesmo quando existem no banco de dados.

**Causa Raiz**: O endpoint de listagem de orders (`GET /api/site-orders/`) não estava carregando o relacionamento `deliverables` usando `selectinload`.

## Correção Aplicada

### Endpoint de Listagem

**ANTES (PROBLEMA)**:
```python
@router.get("/")
async def list_orders(...):
    query = select(SiteOrder).options(
        selectinload(SiteOrder.onboarding),
        selectinload(SiteOrder.addons)
    ).order_by(SiteOrder.created_at.desc())
    # ❌ Faltava selectinload(SiteOrder.deliverables)
```

**DEPOIS (CORRETO)**:
```python
@router.get("/")
async def list_orders(...):
    query = select(SiteOrder).options(
        selectinload(SiteOrder.onboarding),
        selectinload(SiteOrder.addons).selectinload(SiteOrderAddon.addon),
        selectinload(SiteOrder.deliverables)  # ✅ Adicionado
    ).order_by(SiteOrder.created_at.desc())
```

## Por Que Isso Resolve o Problema

1. **Frontend usa lista de orders**: O `selectedOrder` no frontend vem da lista de orders (`setSelectedOrder(order)`), não de uma busca individual
2. **Deliverables não carregados**: Sem `selectinload(SiteOrder.deliverables)`, o SQLAlchemy não carrega os deliverables na lista
3. **Frontend não encontra**: Quando o frontend tenta `selectedOrder.deliverables?.find(d => d.type === 'briefing')`, retorna `undefined` porque `deliverables` não foi carregado

## Verificação

O briefing existe no banco:
```sql
SELECT id, order_id, type, title, status FROM site_deliverables WHERE order_id = 24;
-- Resultado: id=6, type=BRIEFING, title="Strategic Executive Briefing", status=READY
```

Agora com a correção, o endpoint `/api/site-orders/` vai retornar os deliverables junto com cada order.

## Arquivos Modificados

1. `/opt/innexar-crm/backend/app/api/site_orders.py`
   - Adicionado `selectinload(SiteOrder.deliverables)` no endpoint de listagem

## Teste

Após esta correção:
1. Recarregue a página de Site Orders no frontend
2. Clique em "Ver Detalhes" em uma order que tenha briefing
3. Clique em "Ver Detalhes →" na Phase 1 (Strategic Briefing)
4. O briefing deve aparecer agora

## Notas Adicionais

- O endpoint individual `GET /api/site-orders/{order_id}` já estava carregando deliverables corretamente
- O problema era apenas na listagem, que é o que o frontend usa para popular a lista de orders
- Se ainda não funcionar, verificar se há problema de serialização do Pydantic (mas provavelmente não, pois o FastAPI serializa automaticamente relacionamentos carregados)
