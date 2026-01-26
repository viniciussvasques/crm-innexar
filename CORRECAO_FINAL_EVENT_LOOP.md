# Correção Final: Event Loop Error no SQLAlchemy

## Problema Identificado

O erro "Future attached to a different loop" estava ocorrendo porque:

1. **Engine Global Reutilizado**: O `engine` do SQLAlchemy é criado uma vez no módulo `database.py` e reutilizado
2. **Novos Event Loops**: Cada `asyncio.run()` cria um novo event loop
3. **Conflito de Loops**: O engine (e suas conexões no pool) ficam associados ao primeiro loop, mas tentam ser usados em loops diferentes

## Solução Aplicada

### Criar Engine Isolado para Cada Execução Celery

**Arquivo**: `/opt/innexar-crm/backend/app/tasks/site_generation.py`

**Antes (PROBLEMA)**:
```python
from app.core.database import AsyncSessionLocal

async def _generate():
    async with AsyncSessionLocal() as session:  # Usa engine global
        # ...
```

**Depois (CORRETO)**:
```python
def _create_isolated_session():
    """Cria engine isolado para este event loop"""
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_reset_on_return='commit',
        pool_size=5,
        max_overflow=10
    )
    SessionLocal = async_sessionmaker(engine, ...)
    return SessionLocal, engine

async def _generate():
    SessionLocal, engine = _create_isolated_session()
    try:
        async with SessionLocal() as session:  # Usa engine isolado
            # ...
    finally:
        await engine.dispose()  # Limpa engine ao finalizar
```

## Benefícios

1. **Isolamento Completo**: Cada execução Celery tem seu próprio engine
2. **Sem Conflito de Loops**: Engine criado no mesmo loop que será usado
3. **Limpeza Automática**: `engine.dispose()` fecha todas as conexões ao finalizar

## Outras Melhorias Aplicadas

### 1. Logging Melhorado para JSON Malformado

Agora captura:
- Posição exata do erro no JSON
- Contexto ao redor do erro
- Tamanho total do conteúdo
- Stack trace completo

### 2. Tratamento de Erros Preservando Contexto

Todos os erros agora:
- São logados ANTES de transformar
- Preservam contexto com `from e`
- Incluem stack trace completo

## Teste

Após esta correção, o erro "Future attached to a different loop" deve estar resolvido.

Se ainda ocorrer, verificar:
1. Se há outras partes do código usando o engine global
2. Se há múltiplas execuções simultâneas causando conflito
3. Logs completos para identificar o ponto exato do erro
