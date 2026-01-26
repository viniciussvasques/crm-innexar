# Solução Profissional: Celery + Redis

## ✅ Por que Celery é a Solução Profissional

1. **Padrão da Indústria**: Usado por Instagram, Pinterest, Mozilla
2. **Performance**: 3-4x mais rápido que RQ
3. **Confiabilidade**: Retry automático, dead letter queue, monitoramento
4. **Escalabilidade**: Múltiplos workers, filas separadas
5. **Documentação**: Excelente documentação e comunidade

## 🔴 Problema Atual: Threads Daemon

- Threads podem morrer silenciosamente
- Sem logs quando falham
- Sem retry automático
- Conflitos de sessão do banco

## 🎯 Solução: Celery Workers

### Arquitetura

```
FastAPI → Enqueue Job → Redis → Celery Worker → SiteGeneratorService
```

### Benefícios Imediatos

1. ✅ **Jobs persistem no Redis** - não se perdem se servidor reiniciar
2. ✅ **Retry automático** - configuração simples
3. ✅ **Monitoramento** - Flower dashboard para ver todos os jobs
4. ✅ **Sem conflitos** - cada worker em processo separado
5. ✅ **Logs centralizados** - fácil debugar

## 📦 Implementação

### 1. Adicionar Celery

```bash
# requirements.txt
celery[redis]==5.3.4
flower==2.0.1  # Dashboard opcional
```

### 2. Criar Task

```python
# app/tasks/site_generation.py
from celery import shared_task
from app.core.database import AsyncSessionLocal
from app.services.site_generator_service import SiteGeneratorService
import asyncio

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_site_task(self, order_id: int, resume: bool = True):
    """Task Celery para gerar site"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        async def _generate():
            async with AsyncSessionLocal() as session:
                service = SiteGeneratorService(session)
                return await service.generate_site(order_id, resume=resume)
        
        result = loop.run_until_complete(_generate())
        return result
    except Exception as exc:
        # Retry automático
        raise self.retry(exc=exc)
    finally:
        loop.close()
```

### 3. Substituir Threading

```python
# Antes (threading):
thread = threading.Thread(target=run_generation_sync, args=(order_id, True), daemon=True)
thread.start()

# Depois (Celery):
from app.tasks.site_generation import generate_site_task
generate_site_task.delay(order_id, resume=True)
```

### 4. Rodar Worker

```bash
# docker-compose.yml
celery-worker:
  command: celery -A app.celery worker --loglevel=info --concurrency=2
```

## ⏱️ Tempo de Implementação

- Setup Celery: 30 min
- Migrar código: 1h
- Testes: 30 min
- **Total: ~2 horas**

## 🚀 Resultado

- Sistema profissional e robusto
- IA vai gerar sites corretamente
- Fácil monitorar e debugar
- Escalável para produção
