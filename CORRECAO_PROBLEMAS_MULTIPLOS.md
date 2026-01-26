# Correção: Múltiplos Problemas no Sistema

## Problemas Identificados

### 1. **Deliverables Não Aparecem no Frontend** ✅ CORRIGIDO
- **Causa**: Endpoint de listagem não carregava `deliverables` com `selectinload`
- **Solução**: Adicionado `selectinload(SiteOrder.deliverables)` no `GET /api/site-orders/`
- **Status**: ✅ Corrigido

### 2. **IDE Não Mostra Arquivos** ✅ CORRIGIDO
- **Causa**: Arquivos gerados no `celery-worker`, mas IDE busca no `backend` (sem volume compartilhado)
- **Solução**: Adicionado volume compartilhado `./data/generated_sites:/app/generated_sites` em ambos containers
- **Status**: ✅ Corrigido

### 3. **Preview Não Funciona** ⚠️ PENDENTE
- **Causa**: `preview.innexar.com/p/{id}` não está configurado
- **Solução Necessária**: 
  - Criar serviço/endpoint para servir sites gerados
  - Ou configurar nginx/traefik para servir arquivos estáticos
  - Ou implementar preview via API que serve os arquivos
- **Status**: ⚠️ Requer configuração de infraestrutura

### 4. **Loop Infinito de Retry** ✅ CORRIGIDO
- **Causa**: Sistema limpava arquivos mesmo quando order estava em `REVIEW`
- **Solução**: Verificação de status antes de limpar arquivos
- **Status**: ✅ Corrigido

### 5. **Event Loop Error** ✅ CORRIGIDO
- **Causa**: Engine global reutilizado entre diferentes event loops
- **Solução**: Engine isolado para cada execução Celery
- **Status**: ✅ Corrigido

## Correções Aplicadas

### A) Volume Compartilhado para Arquivos Gerados

**docker-compose.yml**:
```yaml
backend:
  volumes:
    - ./data/generated_sites:/app/generated_sites

celery-worker:
  volumes:
    - ./data/generated_sites:/app/generated_sites
```

**Benefícios**:
- Backend e Worker veem os mesmos arquivos
- IDE pode listar arquivos gerados pelo worker
- Arquivos persistem mesmo após restart dos containers

### B) Deliverables na Listagem

**site_orders.py**:
```python
query = select(SiteOrder).options(
    selectinload(SiteOrder.onboarding),
    selectinload(SiteOrder.addons).selectinload(SiteOrderAddon.addon),
    selectinload(SiteOrder.deliverables)  # ✅ Adicionado
)
```

### C) Verificação de Status Antes de Limpar

**site_generator_service.py**:
```python
# Verifica status PRIMEIRO
if order.status in [SiteOrderStatus.REVIEW, SiteOrderStatus.COMPLETED]:
    return {"success": True, "skipped": True}  # Não regenera!

# Só limpa se incompleto
if order.status == SiteOrderStatus.GENERATING and stage_info["current_stage"] in ["phase_2", "phase_3"]:
    shutil.rmtree(target_dir)  # Limpa apenas se incompleto
```

## Arquivos Modificados

1. `/opt/innexar-crm/docker-compose.yml`
   - Adicionado volume compartilhado em `backend` e `celery-worker`

2. `/opt/innexar-crm/backend/app/api/site_orders.py`
   - Adicionado `selectinload(SiteOrder.deliverables)` na listagem

3. `/opt/innexar-crm/backend/app/services/site_generator_service.py`
   - Verificação de status antes de limpar arquivos
   - Prompt melhorado para JSON válido

## Próximos Passos

### 1. Testar Deliverables
- Recarregar página de Site Orders
- Clicar em "Ver Detalhes" → "Ver Detalhes →" na Phase 1
- Deve aparecer o briefing

### 2. Testar IDE
- Abrir `/projects/24/ide`
- Deve mostrar arquivos gerados no Explorer
- Deve permitir editar arquivos

### 3. Preview (Pendente)
- **Opção A**: Criar endpoint `/api/projects/{id}/preview` que serve os arquivos
- **Opção B**: Configurar nginx/traefik para servir `./data/generated_sites` como estático
- **Opção C**: Implementar serviço separado para preview (mais complexo)

## Notas

- Volume compartilhado resolve problema de IDE
- Deliverables agora aparecem na listagem
- Loop infinito foi corrigido
- Preview requer configuração adicional de infraestrutura
