# ✅ Implementação Celery Completa

## O que foi implementado:

### 1. ✅ Dependências
- Adicionado `celery[redis]==5.3.4` ao `requirements.txt`
- Adicionado `flower==2.0.1` (dashboard opcional)

### 2. ✅ Configuração Celery
- Criado `app/celery_app.py` com configuração completa
- Redis URL configurado: `redis://redis:6379/0`
- Timeout: 10 minutos (hard), 9 minutos (soft)
- Retry automático: 3 tentativas com backoff exponencial

### 3. ✅ Task Celery
- Criado `app/tasks/site_generation.py`
- Task: `generate_site_task(order_id, resume=True)`
- Retry automático em caso de falha
- Logs detalhados

### 4. ✅ Substituição de Threading
- ✅ `trigger_build` - Agora usa Celery
- ✅ `reset_generation` - Agora usa Celery
- ✅ `reset_empty_generations` - Agora usa Celery
- ✅ `onboarding_service._trigger_ai_generation` - Agora usa Celery

### 5. ✅ Docker Compose
- Adicionado serviço `celery-worker`
- Concorrência: 2 workers
- Memória: 2GB limit, 1GB reservado
- Queue: `site_generation`

## 🚀 Como usar:

### 1. Rebuild e restart:
```bash
cd /opt/innexar-crm
docker-compose build backend celery-worker
docker-compose up -d celery-worker
```

### 2. Verificar logs do worker:
```bash
docker logs -f crm-celery-worker
```

### 3. Monitorar filas (opcional):
```bash
# Instalar flower localmente ou adicionar ao docker-compose
pip install flower
celery -A app.celery_app flower --port=5555
# Acessar: http://localhost:5555
```

## ✅ Benefícios:

1. **Jobs persistem no Redis** - não se perdem se servidor reiniciar
2. **Retry automático** - 3 tentativas com backoff
3. **Sem conflitos de sessão** - cada job em processo separado
4. **Logs centralizados** - fácil debugar
5. **Escalável** - fácil adicionar mais workers

## 🔍 Verificar se está funcionando:

```bash
# Ver jobs na fila
docker exec crm-redis redis-cli LLEN rq:queue:site_generation

# Ver logs do worker
docker logs crm-celery-worker | grep -i "celery\|task\|generation"
```
