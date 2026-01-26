# 🤖 Sistema Automático de Detecção e Início de Pedidos Travados

## ✅ Implementação Completa

### 1. **Task Periódica Criada**
- ✅ Arquivo: `app/tasks/auto_start_stuck_orders.py`
- ✅ Task: `check_and_start_stuck_orders`
- ✅ Executa a cada **2 minutos** automaticamente

### 2. **Celery Beat Configurado**
- ✅ Schedule configurado no `celery_app.py`
- ✅ Novo serviço `celery-beat` no docker-compose
- ✅ Roda continuamente verificando pedidos travados

### 3. **Lógica Automática**
A task periódica:
1. Busca pedidos em `BUILDING` com onboarding completo
2. Verifica se têm onboarding válido
3. Atualiza status para `GENERATING`
4. Enfileira job Celery automaticamente
5. Loga todas as ações

## 🔄 Como Funciona

```
A cada 2 minutos:
  ↓
Celery Beat executa check_and_start_stuck_orders
  ↓
Busca pedidos BUILDING com onboarding_completed_at
  ↓
Para cada pedido travado:
  - Atualiza status → GENERATING
  - Enfileira job de geração
  - Loga ação
  ↓
Sistema continua automático
```

## 📋 Configuração

**Schedule:**
- Frequência: A cada 2 minutos (120 segundos)
- Task: `app.tasks.auto_start_stuck_orders.check_and_start_stuck_orders`

**Docker Compose:**
- Novo serviço: `celery-beat`
- Roda continuamente
- Usa mesma imagem do backend

## 🎯 Resultado

**Agora o sistema é 100% automático:**
- ✅ Detecta pedidos travados automaticamente
- ✅ Inicia geração automaticamente
- ✅ Não precisa intervenção manual
- ✅ Funciona 24/7

**Não é mais necessário:**
- ❌ Corrigir manualmente
- ❌ Chamar endpoint manualmente
- ❌ Verificar pedidos travados

**O sistema se auto-corrige a cada 2 minutos!**
