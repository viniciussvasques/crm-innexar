# Correção: Loop Infinito de Retry e JSON Malformado

## Problemas Identificados

### 1. **Loop Infinito de Retry**
- **Causa**: Após gerar com sucesso, o sistema detecta arquivos existentes e entra no modo "resume"
- **Sintoma**: Sistema limpa arquivos recém-gerados e tenta gerar novamente indefinidamente
- **Impacto**: Múltiplas execuções simultâneas, desperdício de recursos, conflitos de event loop

### 2. **JSON Malformado da IA**
- **Causa**: IA não está escapando corretamente caracteres especiais no JSON
- **Sintomas**: 
  - `"content":Obsidian,` (sem aspas)
  - `Invalid \escape` (escape inválido)
  - `Unterminated string` (string truncada)
- **Impacto**: Falha na geração mesmo quando a IA retorna conteúdo

### 3. **Event Loop Error Persistente**
- **Causa**: Múltiplas execuções simultâneas causando conflitos
- **Sintoma**: "Future attached to different loop" mesmo com engine isolado

## Correções Aplicadas

### A) Verificação de Status Antes de Resume

**ANTES (PROBLEMA)**:
```python
if resume and stage_info["current_stage"] != "none":
    # Sempre limpa e recomeça se há arquivos
    if stage_info["current_stage"] in ["phase_2", "phase_3"]:
        shutil.rmtree(target_dir)  # Limpa mesmo se order está em REVIEW!
```

**DEPOIS (CORRETO)**:
```python
# Verifica status da order PRIMEIRO
if order.status in [SiteOrderStatus.REVIEW, SiteOrderStatus.COMPLETED]:
    return {"success": True, "skipped": True}  # Não regenera!

# Só limpa se order está em GENERATING (incompleto)
if order.status == SiteOrderStatus.GENERATING and stage_info["current_stage"] in ["phase_2", "phase_3"]:
    shutil.rmtree(target_dir)  # Limpa apenas se incompleto
elif order.status == SiteOrderStatus.REVIEW:
    return {"success": True, "skipped": True}  # Arquivos válidos, não limpa
```

### B) Prompt Melhorado para JSON Válido

**ANTES**:
```
OUTPUT FORMAT:
Return ONLY valid JSON with this structure:
{
  "files": [...]
}
Do not explain. Just JSON.
```

**DEPOIS**:
```
CRITICAL - OUTPUT FORMAT:
Return ONLY valid, complete JSON with this EXACT structure:
{
  "files": [...]
}

JSON VALIDATION RULES:
- ALL strings MUST be properly escaped (use \\ for backslashes, \" for quotes, \n for newlines)
- ALL strings MUST be enclosed in double quotes
- NO trailing commas
- NO unescaped newlines inside string values
- The JSON MUST be complete and valid - do not truncate it
- If content is long, ensure proper JSON escaping of all special characters

Example of proper escaping:
"content": "import React from 'react';\\n\\nexport default function Page() {{ return <div>Hello</div>; }}"

Do not explain. Return ONLY the JSON object, nothing else.
```

### C) Busca de Order Otimizada

- Order é buscada uma vez no início
- Reutilizada nas fases subsequentes
- Refresh apenas quando necessário

## Arquivos Modificados

1. `/opt/innexar-crm/backend/app/services/site_generator_service.py`
   - Adicionada verificação de status antes de resume
   - Melhorado prompt para garantir JSON válido
   - Otimizada busca de order (evita duplicação)

## Resultado Esperado

### Antes:
```
[SUCCESS]Site generation completed successfully!
[RESUME]Resuming generation from stage: phase_2 (found 16 existing files)
[CLEANUP]Removed incomplete files to restart generation
[PHASE_1_ERROR]Strategy phase failed: Future attached to different loop
[SUCCESS]Site generation completed successfully!
[RESUME]Resuming generation... (loop infinito)
```

### Depois:
```
[SUCCESS]Site generation completed successfully!
[SKIP]Order already in REVIEW status. Skipping generation.
```

## Próximos Passos

1. **Testar geração completa**: Verificar se não entra mais em loop infinito
2. **Verificar JSON da IA**: Se ainda houver problemas, os logs mostrarão posição exata do erro
3. **Monitorar event loop errors**: Se persistirem, verificar se há outras causas (múltiplas tasks simultâneas)

## Notas

- O problema do event loop pode persistir se houver múltiplas execuções simultâneas da mesma order
- Considerar adicionar lock/distributed lock para evitar execuções simultâneas
- O prompt melhorado deve reduzir significativamente erros de JSON malformado
