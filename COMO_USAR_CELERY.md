# 🚀 Como Usar o Sistema Celery Implementado

## ✅ Implementação Completa!

Todas as gerações de sites agora usam **Celery** em vez de threads. Isso resolve:
- ✅ Conflitos de sessão do banco
- ✅ Jobs perdidos ao reiniciar servidor
- ✅ Falta de retry automático
- ✅ Dificuldade de debug

## 📋 Próximos Passos:

### 1. Rebuild e Iniciar Worker

```bash
cd /opt/innexar-crm

# Rebuild backend (instala Celery)
docker-compose build backend celery-worker

# Iniciar worker Celery
docker-compose up -d celery-worker

# Verificar se está rodando
docker ps | grep celery-worker
```

### 2. Verificar Logs

```bash
# Logs do worker
docker logs -f crm-celery-worker

# Deve ver algo como:
# [INFO/MainProcess] celery@hostname ready.
# [INFO/MainProcess] Connected to redis://redis:6379/0
```

### 3. Testar Geração

1. Acesse o dashboard: `https://sales.innexar.app/site-orders`
2. Clique em "Gerar Site" em um pedido
3. Verifique os logs do worker:
   ```bash
   docker logs -f crm-celery-worker | grep -i "generation\|task"
   ```

### 4. Monitorar Fila (Opcional)

```bash
# Ver quantos jobs estão na fila
docker exec crm-redis redis-cli LLEN rq:queue:site_generation

# Ver todos os jobs
docker exec crm-redis redis-cli KEYS "rq:*"
```

## 🔍 Troubleshooting

### Worker não inicia:
```bash
# Verificar erros
docker logs crm-celery-worker

# Verificar se Redis está acessível
docker exec crm-celery-worker ping -c 1 redis
```

### Jobs não são processados:
```bash
# Verificar se worker está conectado
docker logs crm-celery-worker | grep "ready"

# Verificar fila
docker exec crm-redis redis-cli LLEN rq:queue:site_generation
```

### Erro de importação:
```bash
# Rebuild backend
docker-compose build backend celery-worker
docker-compose restart celery-worker
```

## 📊 Monitoramento Avançado (Opcional)

Para adicionar Flower (dashboard web):

```yaml
# Adicionar ao docker-compose.yml
celery-flower:
  build: ./backend
  command: celery -A app.celery_app flower --port=5555
  ports:
    - "5555:5555"
  environment:
    REDIS_URL: redis://redis:6379/0
  networks:
    - fixelo_fixelo-network
```

Acessar: `http://localhost:5555`

## ✅ Status Atual

- ✅ Celery configurado
- ✅ Task criada
- ✅ Threading substituído por Celery
- ✅ Worker adicionado ao docker-compose
- ⏳ **Próximo**: Rebuild e testar!
