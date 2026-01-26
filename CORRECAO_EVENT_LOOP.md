# Correção: Event Loop e Logging de Erros

## Problemas Identificados

### 1. **"Future attached to a different loop"**
- **Causa**: Uso de `loop.run_until_complete()` com gerenciamento manual de event loop em tarefas Celery
- **Impacto**: Erros de concorrência ao executar código async dentro de workers Celery

### 2. **ValueError sem mensagem**
- **Causa**: Exceções sendo capturadas mas não logadas corretamente
- **Impacto**: Impossibilidade de debugar erros da IA (mensagens vazias nos logs)

## Correções Aplicadas

### A) Event Loop no Celery (`site_generation.py`)

**Antes (ERRADO)**:
```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    result = loop.run_until_complete(_generate())
finally:
    loop.close()
```

**Depois (CORRETO)**:
```python
async def _generate():
    # ... código async ...
    
# Use asyncio.run() - cria e gerencia o loop automaticamente
result = asyncio.run(_generate())
```

**Benefícios**:
- `asyncio.run()` cria um novo event loop isolado
- Gerencia o ciclo de vida do loop automaticamente
- Evita conflitos de event loop entre threads/processos

### B) Logging de Erros Melhorado

**Antes (ERRADO)**:
```python
except Exception as e:
    error_msg = str(e)  # Pode ser vazio!
    logger.error(f"Error: {error_msg}")  # Sem stack trace
```

**Depois (CORRETO)**:
```python
import traceback

except Exception as e:
    # logger.exception() inclui stack trace completo automaticamente
    logger.exception("AI call failed: %r", e)
    
    # Captura detalhes completos para DB
    error_details = {
        "error_type": type(e).__name__,
        "error_message": str(e) or repr(e),
        "traceback": traceback.format_exc()
    }
```

**Benefícios**:
- `logger.exception()` registra stack trace completo
- Sempre captura mensagem de erro (usa `repr()` como fallback)
- Detalhes HTTP (status code, response) quando disponível

### C) Verificação de Pool Celery

**Status**: ✅ **Correto**
- Pool padrão (prefork) está sendo usado
- Não usa `-P gevent` ou `-P eventlet` (que causariam problemas com asyncio)

### D) Clientes HTTP Async

**Status**: ✅ **Já estava correto**
- Todos os `httpx.AsyncClient` usam `async with` (context manager)
- Não há reuso global de clientes

## Arquivos Modificados

1. `/opt/innexar-crm/backend/app/tasks/site_generation.py`
   - Substituído `loop.run_until_complete()` por `asyncio.run()`
   - Melhorado logging com `logger.exception()`

2. `/opt/innexar-crm/backend/app/services/site_generator_service.py`
   - Adicionado `import traceback`
   - Substituído `logger.error(..., exc_info=True)` por `logger.exception()`
   - Melhorada captura de detalhes de erro (HTTP status, response text, etc.)

3. `/opt/innexar-crm/backend/app/services/ai_service.py`
   - Melhorado logging de erros HTTP com `logger.exception()`
   - Adicionado `from e` nos `raise ValueError()` para preservar contexto

## Testes Recomendados

1. **Teste de Geração de Site**:
   - Criar uma nova order
   - Verificar logs do Celery worker
   - Confirmar que não há erros de "Future attached to different loop"
   - Verificar que erros têm mensagens detalhadas

2. **Teste de Erro de IA**:
   - Simular erro de API (timeout, 401, etc.)
   - Verificar que logs contêm:
     - Stack trace completo
     - Mensagem de erro clara
     - Detalhes HTTP (se aplicável)

## Próximos Passos

- Monitorar logs após deploy
- Verificar se erros de event loop foram resolvidos
- Confirmar que mensagens de erro são sempre informativas
