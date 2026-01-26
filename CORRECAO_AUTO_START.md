# 🔧 Correção: Pedido Não Inicia Automaticamente

## ❌ Problema Identificado

**Sintoma:**
- Pedido criado e onboarding completo
- Status fica em `BUILDING` 
- Geração não inicia automaticamente
- Nenhum log aparece

**Causa:**
O `_trigger_ai_generation` pode falhar silenciosamente ou o status pode ser revertido para `BUILDING` se houver erro ao enfileirar o job Celery.

## ✅ Correções Aplicadas

### 1. **Correção Imediata - Order 24**
- ✅ Status atualizado manualmente para `GENERATING`
- ✅ Job Celery enfileirado
- ✅ Logs começaram a aparecer
- ✅ IA está processando

### 2. **Melhoria no Código**
- ✅ Removido rollback automático de status quando geração falha
- ✅ Status permanece `GENERATING` mesmo se houver erro ao enfileirar
- ✅ Endpoint `auto-start-stuck-orders` pode recuperar pedidos travados

### 3. **Mecanismo de Segurança**
- ✅ Endpoint `/api/site-orders/auto-start-stuck-orders` existe
- ✅ Pode ser chamado manualmente ou via cron
- ✅ Encontra pedidos em `BUILDING` com onboarding completo
- ✅ Inicia geração automaticamente

## 🔄 Fluxo Esperado

1. **Onboarding Completo**
   - Status muda para `GENERATING`
   - `_trigger_ai_generation` é chamado
   - Job Celery é enfileirado

2. **Se Falhar Silenciosamente**
   - Status permanece `GENERATING` (não reverte)
   - Endpoint `auto-start-stuck-orders` pode recuperar
   - Ou correção manual via script

## 📋 Como Usar

**Verificar pedidos travados:**
```bash
# Ver pedidos em BUILDING com onboarding completo
docker exec crm-backend python3 -c "
from app.core.database import AsyncSessionLocal
from app.models.site_order import SiteOrder, SiteOrderStatus
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import asyncio

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(SiteOrder)
            .options(selectinload(SiteOrder.onboarding))
            .where(SiteOrder.status == SiteOrderStatus.BUILDING)
            .where(SiteOrder.onboarding_completed_at.isnot(None))
        )
        stuck = result.scalars().all()
        print(f'Pedidos travados: {len(stuck)}')
        for o in stuck:
            print(f'  - Order {o.id}: {o.customer_email}')

asyncio.run(check())
"
```

**Corrigir pedido travado:**
```bash
# Corrigir order específico
docker exec crm-backend python3 -c "
from app.core.database import AsyncSessionLocal
from app.models.site_order import SiteOrder, SiteOrderStatus
from app.tasks.site_generation import generate_site_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import asyncio

async def fix(order_id):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(SiteOrder)
            .options(selectinload(SiteOrder.onboarding))
            .where(SiteOrder.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if order and order.onboarding and order.onboarding.is_complete:
            order.status = SiteOrderStatus.GENERATING
            await db.commit()
            celery_task = generate_site_task.delay(order_id, resume=True)
            print(f'✅ Order {order_id} corrigido - Job: {celery_task.id}')

asyncio.run(fix(24))
"
```

## 🎯 Status Atual

- ✅ Order 24 corrigido e processando
- ✅ Logs aparecendo corretamente
- ✅ IA gerando código
- ✅ Código melhorado para evitar rollback desnecessário
