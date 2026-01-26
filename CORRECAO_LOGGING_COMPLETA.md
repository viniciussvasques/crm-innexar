# Correção Completa: Event Loop e Logging de Erros

## Problemas Identificados

### 1. **"Future attached to a different loop" na Strategy**
- **Causa**: Erro de event loop ao executar código async em Celery
- **Sintoma**: Strategy falha mas depois "volta" (continua execução)

### 2. **ValueError sem mensagem útil**
- **Causa**: Erros sendo transformados em `ValueError` sem preservar a mensagem original
- **Sintoma**: Logs mostram `"error_type": "ValueError"` com `"traceback": "AI generation failed: "` (vazio)

### 3. **Detalhes do briefing indisponíveis**
- **Causa**: Possível problema de serialização ou acesso no frontend

## Correções Aplicadas

### A) Logging Melhorado - Captura do Erro REAL

**ANTES (ERRADO)**:
```python
except Exception as ai_error:
    logger.exception(f"Error: %r", ai_error)  # Pode não capturar tudo
    error_msg = str(ai_error)  # Pode ser vazio!
    raise ValueError(f"AI generation failed: {error_msg}")  # Perde contexto
```

**DEPOIS (CORRETO)**:
```python
except Exception as ai_error:
    # CRITICAL: Log the REAL error FIRST before transforming it
    logger.error(f"[{order_id}] ❌ AI call failed: %r", ai_error)
    logger.error(f"[{order_id}] ❌ AI call traceback:\n%s", traceback.format_exc())
    
    # Build error message from ORIGINAL exception
    error_msg = str(ai_error) if str(ai_error) else repr(ai_error)
    
    # Always use !r to ensure we have a message
    raise ValueError(f"AI generation failed: {error_msg!r}") from ai_error
```

### B) Logging em Todos os Pontos Críticos

1. **`ai_service.py` - `_call_cloudflare`**:
   - Loga erro REAL antes de transformar
   - Captura `httpx.ReadTimeout`, `httpx.HTTPStatusError`, e exceções gerais
   - Preserva contexto com `from e`

2. **`site_generator_service.py` - AI Generation**:
   - Loga erro REAL antes de transformar
   - Captura detalhes HTTP (status code, response text)
   - Usa `repr()` como fallback se `str()` estiver vazio

3. **`site_generator_service.py` - Strategy Phase**:
   - Loga erro REAL antes de transformar
   - Captura stack trace completo
   - Preserva contexto com `from e`

### C) Event Loop - Já Corrigido

- Usando `asyncio.run()` em vez de `loop.run_until_complete()`
- Sem clientes async globais
- Pool Celery correto (prefork)

## Arquivos Modificados

1. `/opt/innexar-crm/backend/app/services/ai_service.py`
   - Adicionado `import traceback`
   - Melhorado logging em `_call_cloudflare` para capturar erro REAL antes de transformar

2. `/opt/innexar-crm/backend/app/services/site_generator_service.py`
   - Melhorado logging em `generate_site` (AI generation)
   - Melhorado logging em `generate_strategy_brief` (Strategy phase)
   - Sempre usa `repr()` como fallback para mensagens vazias
   - Preserva contexto com `from e` em todos os `raise`

3. `/opt/innexar-crm/backend/app/tasks/site_generation.py`
   - Já estava usando `asyncio.run()` (correto)

## Como os Logs Agora Funcionam

### Antes:
```
[AI_ERROR]AI call failed:
[ERROR]Fatal error: AI generation failed:
{
  "traceback": "AI generation failed: ",
  "error_type": "ValueError"
}
```

### Depois:
```
[ERROR] ❌ AI call failed: Cloudflare API error 401: Unauthorized
[ERROR] ❌ AI call traceback:
Traceback (most recent call last):
  File "...", line X, in _call_cloudflare
    resp.raise_for_status()
  File "...", line Y, in raise_for_status
    raise HTTPStatusError(...)
httpx.HTTPStatusError: 401 Unauthorized

[AI_ERROR]AI call failed: Cloudflare API error 401: Unauthorized
{
  "error_type": "HTTPStatusError",
  "error_message": "Cloudflare API error 401: Unauthorized",
  "error_repr": "HTTPStatusError(...)",
  "traceback": "...",
  "status_code": 401,
  "response_text": "..."
}
```

## Próximos Passos para Diagnóstico

Com o logging melhorado, quando você rodar uma nova geração, os logs vão mostrar:

1. **Erro REAL** (não transformado)
2. **Stack trace completo** do ponto exato onde falhou
3. **Detalhes HTTP** (se aplicável): status code, response text
4. **Contexto preservado** com `from e`

Isso vai permitir identificar:
- Se é problema de autenticação (401)
- Se é timeout (ReadTimeout)
- Se é problema de parsing (JSON decode error)
- Se é problema de event loop (ainda presente)

## Teste Recomendado

1. **Rodar com concurrency 1** (temporariamente):
   ```bash
   docker compose exec celery-worker celery -A app.celery_app worker --loglevel=info --concurrency=1
   ```

2. **Desativar Strategy** (se já existe briefing) e rodar só coding

3. **Verificar logs** com `logger.exception()` - agora vai mostrar stack completo

4. **Compartilhar stack trace completo** para diagnóstico final

## Sobre o Briefing Indisponível

O endpoint `/api/site-orders/{order_id}` já carrega `deliverables` com `selectinload`. 

Verificar:
- Se o frontend está acessando `order.deliverables` corretamente
- Se há problema de serialização do modelo `SiteDeliverable`
- Se o briefing foi realmente criado (verificar no banco)

Para verificar no banco:
```sql
SELECT * FROM site_deliverables WHERE order_id = X AND type = 'briefing';
```
