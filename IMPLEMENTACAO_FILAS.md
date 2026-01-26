# Implementação de Filas com RQ - Plano de Ação

## ✅ Situação Atual

- ❌ Usando `threading.Thread` + `asyncio.new_event_loop()` - frágil e propenso a erros
- ❌ Conflitos de sessão do banco de dados
- ❌ Sem retry automático
- ❌ Jobs perdidos se servidor reiniciar
- ✅ Redis já está rodando (`crm-redis`)

## 🎯 Solução: RQ (Redis Queue)

### Por que RQ?
- ✅ **Simples**: Menos código que Celery, mais direto
- ✅ **Robusto**: Retry automático, persistência no Redis
- ✅ **Fácil debug**: Interface web para ver filas
- ✅ **Sem conflitos**: Cada job em processo separado

## 📦 Passo 1: Adicionar Dependências

```bash
# Adicionar ao requirements.txt
rq==1.15.1
rq-dashboard==0.6.1
```

## 🔧 Passo 2: Criar Worker

```python
# backend/app/workers/site_generation_worker.py
from rq import Worker, Queue, Connection
from app.core.database import AsyncSessionLocal
from app.services.site_generator_service import SiteGeneratorService
import asyncio
import logging

logger = logging.getLogger(__name__)

def generate_site_job(order_id: int, resume: bool = True):
    """Job function que roda em processo separado"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        async def _generate():
            async with AsyncSessionLocal() as session:
                service = SiteGeneratorService(session)
                result = await service.generate_site(order_id, resume=resume)
                return result
        
        result = loop.run_until_complete(_generate())
        return result
    finally:
        loop.close()

# Para rodar o worker:
# rq worker --url redis://localhost:6379/0 site_generation
```

## 🔄 Passo 3: Substituir Threading por Enqueue

### Antes (atual):
```python
thread = threading.Thread(target=run_generation_sync, args=(order_id, True), daemon=True)
thread.start()
```

### Depois (com RQ):
```python
from redis import Redis
from rq import Queue

redis_conn = Redis.from_url('redis://localhost:6379/0')
queue = Queue('site_generation', connection=redis_conn)

job = queue.enqueue('app.workers.site_generation_worker.generate_site_job', order_id, resume=True)
```

## 🚀 Passo 4: Adicionar ao Docker

```yaml
# docker-compose.yml
services:
  crm-worker:
    build: ./backend
    command: rq worker --url redis://crm-redis:6379/0 site_generation
    depends_on:
      - crm-redis
      - crm-db
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

## 📊 Passo 5: Dashboard (Opcional)

```bash
# Rodar dashboard para monitorar filas
rq-dashboard --redis-url redis://localhost:6379/0
```

## ✅ Benefícios Imediatos

1. **Sem conflitos de sessão**: Cada job em processo separado
2. **Retry automático**: Configurável por job
3. **Persistência**: Jobs sobrevivem a reinicializações
4. **Monitoramento**: Ver status de todos os jobs
5. **Escalabilidade**: Fácil adicionar mais workers

## ⏱️ Tempo de Implementação

- Setup básico: 30 minutos
- Migração completa: 1-2 horas
- Testes: 30 minutos

**Total: ~2-3 horas para sistema robusto**
