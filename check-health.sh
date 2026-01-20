#!/bin/bash

echo "🔍 Verificando saúde do sistema Innexar CRM..."
echo ""

# Verificar containers
echo "📦 Containers Docker:"
docker ps --filter "name=crm-" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "Docker não disponível"
echo ""

# Verificar memória
echo "💾 Memória do Sistema:"
free -h | grep -E "Mem|Swap"
echo ""

# Verificar backend
echo "🔧 Backend (últimas 5 linhas de log):"
docker logs crm-backend --tail 5 2>&1 | tail -5
echo ""

# Verificar frontend
echo "🎨 Frontend (últimas 5 linhas de log):"
docker logs crm-frontend --tail 5 2>&1 | tail -5
echo ""

echo "✅ Verificação completa!"
echo ""
echo "Para ver logs completos:"
echo "  docker logs crm-backend"
echo "  docker logs crm-frontend"
echo ""
echo "Para reiniciar:"
echo "  docker-compose restart"

