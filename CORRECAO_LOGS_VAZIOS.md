# 🔧 Correção: Logs Vazios e Status Mudado Sem Geração

## ❌ Problema Identificado

**Sintoma:**
- Status mudou para `GENERATING`
- Mas **0 logs** no banco de dados
- Nenhum arquivo gerado
- Logs vazios no frontend

**Causa Raiz:**
O método `_log_progress` estava falhando com `InFailedSQLTransactionError` porque:
1. Mesmo usando um engine isolado, ainda havia conflitos de transação
2. O uso de `begin()` criava transações que podiam falhar e bloquear logs subsequentes
3. Erros em uma transação anterior impediam logs futuros

## ✅ Solução Aplicada

**Mudança no `_log_progress`:**
- Adicionado `isolation_level="AUTOCOMMIT"` no engine isolado
- Trocado `isolated_engine.begin()` por `isolated_engine.connect()`
- Cada INSERT agora é uma transação independente (AUTOCOMMIT)
- Não há mais dependência de transações anteriores

**Código Antes:**
```python
isolated_engine = create_async_engine(
    database_url,
    pool_pre_ping=True,
    pool_reset_on_return='commit',
    echo=False,
    pool_size=1,
    max_overflow=0
)

async with isolated_engine.begin() as connection:
    # Podia falhar com InFailedSQLTransactionError
```

**Código Depois:**
```python
isolated_engine = create_async_engine(
    database_url,
    pool_pre_ping=True,
    pool_reset_on_return='commit',
    echo=False,
    pool_size=1,
    max_overflow=0,
    isolation_level="AUTOCOMMIT"  # ✅ NOVO
)

async with isolated_engine.connect() as connection:
    # AUTOCOMMIT - cada INSERT é independente
```

## 🎯 Resultado Esperado

Agora os logs devem ser salvos corretamente:
- ✅ Cada log é uma transação independente
- ✅ Erros em um log não afetam logs futuros
- ✅ Logs aparecem no banco e no frontend
- ✅ Status `GENERATING` terá logs visíveis

## 📊 Verificação

**Verificar se logs estão sendo salvos:**
```bash
docker exec crm-backend python3 -c "
import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text('''
            SELECT order_id, step, message, created_at
            FROM site_generation_logs
            WHERE order_id = 23
            ORDER BY created_at DESC
            LIMIT 10
        '''))
        for log in result.fetchall():
            print(f'[{log.created_at}] [{log.step}]: {log.message}')

asyncio.run(check())
"
```

**Monitorar worker:**
```bash
docker logs -f crm-celery-worker | grep -E "\[23\]|Order 23|LOG ERROR"
```

## ⚠️ Observação

- Worker foi reiniciado para aplicar a correção
- Jobs na fila serão processados com a nova lógica
- Logs antigos que falharam não serão recuperados (mas novos funcionarão)
