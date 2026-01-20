#!/bin/bash

# Script para testar todos os endpoints da API
# Requer: curl, jq (opcional)

BASE_URL="${1:-http://localhost:8000}"
API_URL="${BASE_URL}/api"

echo "🧪 Testando Endpoints da API Innexar CRM"
echo "=========================================="
echo "Base URL: ${BASE_URL}"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para testar endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local token=$4
    local description=$5
    
    echo -n "Testando ${method} ${endpoint}... "
    
    if [ -z "$token" ]; then
        response=$(curl -s -w "\n%{http_code}" -X ${method} \
            -H "Content-Type: application/json" \
            ${data:+-d "$data"} \
            "${API_URL}${endpoint}")
    else
        response=$(curl -s -w "\n%{http_code}" -X ${method} \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ${token}" \
            ${data:+-d "$data"} \
            "${API_URL}${endpoint}")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ OK (${http_code})${NC}"
        if [ ! -z "$description" ]; then
            echo "  → $description"
        fi
        return 0
    elif [ "$http_code" -eq 401 ] || [ "$http_code" -eq 403 ]; then
        echo -e "${YELLOW}⚠ Auth Required (${http_code})${NC}"
        return 1
    else
        echo -e "${RED}✗ FAIL (${http_code})${NC}"
        echo "  Response: $body" | head -c 200
        echo ""
        return 1
    fi
}

# 1. Teste de Health Check
echo "1️⃣  Health Check"
test_endpoint "GET" "/" "" "" "Verifica se API está rodando"
echo ""

# 2. Teste de Login
echo "2️⃣  Autenticação"
echo -n "Login (admin@innexar.app)... "
login_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@innexar.app","password":"admin123"}' \
    "${API_URL}/auth/login")

http_code=$(echo "$login_response" | grep -o '"access_token"' > /dev/null && echo "200" || echo "401")

if [ "$http_code" = "200" ]; then
    TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}✓ OK${NC}"
    echo "  Token obtido: ${TOKEN:0:20}..."
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Response: $login_response"
    echo ""
    echo "⚠️  Não foi possível obter token. Testando endpoints públicos apenas..."
    TOKEN=""
fi
echo ""

# 3. Teste de Usuários (requer admin)
if [ ! -z "$TOKEN" ]; then
    echo "3️⃣  Usuários"
    test_endpoint "GET" "/users/me" "" "$TOKEN" "Obter usuário atual"
    test_endpoint "GET" "/users/" "" "$TOKEN" "Listar usuários (admin)"
    echo ""
fi

# 4. Teste de Contatos
if [ ! -z "$TOKEN" ]; then
    echo "4️⃣  Contatos"
    test_endpoint "GET" "/contacts/" "" "$TOKEN" "Listar contatos"
    echo ""
fi

# 5. Teste de Oportunidades
if [ ! -z "$TOKEN" ]; then
    echo "5️⃣  Oportunidades"
    test_endpoint "GET" "/opportunities/" "" "$TOKEN" "Listar oportunidades"
    echo ""
fi

# 6. Teste de Projetos
if [ ! -z "$TOKEN" ]; then
    echo "6️⃣  Projetos"
    test_endpoint "GET" "/projects" "" "$TOKEN" "Listar projetos"
    echo ""
fi

# 7. Teste de Atividades
if [ ! -z "$TOKEN" ]; then
    echo "7️⃣  Atividades"
    test_endpoint "GET" "/activities/" "" "$TOKEN" "Listar atividades"
    echo ""
fi

# 8. Teste de Dashboard
if [ ! -z "$TOKEN" ]; then
    echo "8️⃣  Dashboard"
    test_endpoint "GET" "/dashboard/admin" "" "$TOKEN" "Dashboard admin"
    test_endpoint "GET" "/dashboard/vendedor" "" "$TOKEN" "Dashboard vendedor"
    echo ""
fi

# 9. Teste de Comissões
if [ ! -z "$TOKEN" ]; then
    echo "9️⃣  Comissões"
    test_endpoint "GET" "/commissions/" "" "$TOKEN" "Listar comissões"
    echo ""
fi

# 10. Teste de Metas
if [ ! -z "$TOKEN" ]; then
    echo "🔟 Metas"
    test_endpoint "GET" "/goals/" "" "$TOKEN" "Listar metas"
    echo ""
fi

# 11. Teste de Notificações
if [ ! -z "$TOKEN" ]; then
    echo "1️⃣1️⃣  Notificações"
    test_endpoint "GET" "/notifications/" "" "$TOKEN" "Listar notificações"
    echo ""
fi

# 12. Teste de Templates
if [ ! -z "$TOKEN" ]; then
    echo "1️⃣2️⃣  Templates"
    test_endpoint "GET" "/templates/" "" "$TOKEN" "Listar templates"
    echo ""
fi

# 13. Teste de Quote Requests
if [ ! -z "$TOKEN" ]; then
    echo "1️⃣3️⃣  Quote Requests"
    test_endpoint "GET" "/quote-requests/" "" "$TOKEN" "Listar solicitações de orçamento"
    echo ""
fi

# 14. Teste de AI (se token disponível)
if [ ! -z "$TOKEN" ]; then
    echo "1️⃣4️⃣  IA"
    test_endpoint "POST" "/ai/chat" '{"prompt":"teste","max_tokens":100}' "$TOKEN" "Chat com IA"
    echo ""
fi

echo "=========================================="
echo "✅ Testes concluídos!"
echo ""
echo "Para testar com outro servidor:"
echo "  ./test_endpoints.sh http://api.sales.innexar.app"

