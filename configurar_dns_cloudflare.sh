#!/bin/bash

# Cores para melhor visualização
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔧 Configurando DNS do CRM Innexar no Cloudflare..."

# Obter token do Traefik
CF_DNS_API_TOKEN=$(docker exec traefik printenv CF_DNS_API_TOKEN 2>/dev/null | grep -v "^$" | head -1)

if [ -z "$CF_DNS_API_TOKEN" ]; then
    echo -e "${RED}❌ Erro: CF_DNS_API_TOKEN não encontrado no Traefik${NC}"
    echo "Configure no docker-compose.yml do Traefik ou no arquivo .env do Traefik."
    exit 1
fi

echo -e "${GREEN}✅ Token do Cloudflare encontrado${NC}"

# Obter IP IPv4 do servidor
SERVER_IP=$(curl -4 -s ifconfig.me || curl -4 -s icanhazip.com || curl -4 -s ipinfo.io/ip)

if [ -z "$SERVER_IP" ]; then
    echo -e "${RED}❌ Erro: Não foi possível obter o IP do servidor.${NC}"
    exit 1
fi

# Domínio principal
DOMAIN="innexar.app"

# Subdomínios do CRM
CRM_FRONTEND="sales.innexar.app"
CRM_API="api.sales.innexar.app"

echo ""
echo "📋 Configurações a serem aplicadas:"
echo "  - $CRM_FRONTEND → $SERVER_IP (com proxy)"
echo "  - $CRM_API → $SERVER_IP (com proxy)"
echo ""

# Função para obter Zone ID
get_zone_id() {
    local domain=$1
    curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$domain" \
        -H "Authorization: Bearer $CF_DNS_API_TOKEN" \
        -H "Content-Type: application/json" | \
        jq -r '.result[0].id'
}

# Função para criar/atualizar registro DNS
update_dns_record() {
    local zone_id=$1
    local type=$2
    local name=$3
    local content=$4
    local proxied=$5 # true/false

    local record_id=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$zone_id/dns_records?type=$type&name=$name" \
        -H "Authorization: Bearer $CF_DNS_API_TOKEN" \
        -H "Content-Type: application/json" | \
        jq -r '.result[0].id')

    if [ "$record_id" != "null" ] && [ -n "$record_id" ]; then
        echo -e "  ${YELLOW}📝 Atualizando registro existente:${NC} $name"
        curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$zone_id/dns_records/$record_id" \
            -H "Authorization: Bearer $CF_DNS_API_TOKEN" \
            -H "Content-Type: application/json" \
            --data "{\"type\":\"$type\",\"name\":\"$name\",\"content\":\"$content\",\"proxied\":$proxied}" > /dev/null
        echo -e "     ${GREEN}✅ Atualizado com sucesso${NC}"
    else
        echo -e "  ${GREEN}➕ Criando novo registro:${NC} $name"
        curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$zone_id/dns_records" \
            -H "Authorization: Bearer $CF_DNS_API_TOKEN" \
            -H "Content-Type: application/json" \
            --data "{\"type\":\"$type\",\"name\":\"$name\",\"content\":\"$content\",\"proxied\":$proxied}" > /dev/null
        echo -e "     ${GREEN}✅ Criado com sucesso${NC}"
    fi
}

echo "🌐 Configurando $DOMAIN..."
ZONE_ID=$(get_zone_id $DOMAIN)

if [ -z "$ZONE_ID" ] || [ "$ZONE_ID" == "null" ]; then
    echo -e "${RED}❌ Erro: Domínio $DOMAIN não encontrado no Cloudflare${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Zone ID: $ZONE_ID${NC}"

    echo ""
    echo "📌 Configurando $CRM_FRONTEND..."
    update_dns_record "$ZONE_ID" "A" "sales" "$SERVER_IP" "true" # Com proxy Cloudflare

    echo ""
    echo "📌 Configurando $CRM_API..."
    update_dns_record "$ZONE_ID" "A" "api.sales" "$SERVER_IP" "false" # SEM proxy Cloudflare (SSL no Traefik)

    echo ""
    echo -e "${GREEN}✅ Configuração concluída!${NC}"
    echo ""
    echo "⏳ Aguarde alguns minutos para propagação DNS e geração do certificado SSL"
    echo "🔍 Verifique com:"
    echo "   dig A $CRM_FRONTEND"
    echo "   dig A $CRM_API"
    echo ""
    echo "🌐 URLs do CRM:"
    echo "   - https://$CRM_FRONTEND (frontend)"
    echo "   - https://$CRM_API (API)"
    echo ""
    echo "📝 Para verificar certificados SSL:"
    echo "   docker logs traefik | grep -i certificate"
fi

