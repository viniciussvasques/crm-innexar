#!/bin/bash

# Script para configurar DNS do Cloudflare para autodescobrimento de email
# Domínios: imap.innexar.app (993) e smtp.innexar.app (587)

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configurações
ZONE_NAME="innexar.app"

# Obter token do Traefik ou variável de ambiente
CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN:-$(docker exec traefik printenv CF_DNS_API_TOKEN 2>/dev/null | grep -v "^$" | head -1)}"

if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo -e "${RED}❌ Erro: CF_DNS_API_TOKEN não encontrado${NC}"
    echo "Configure a variável de ambiente:"
    echo "export CLOUDFLARE_API_TOKEN='seu-token'"
    echo "Ou configure no docker-compose.yml do Traefik"
    exit 1
fi

echo -e "${GREEN}✅ Token do Cloudflare encontrado${NC}"

# Obter Zone ID
echo -e "${YELLOW}📡 Obtendo Zone ID para $ZONE_NAME...${NC}"
ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$ZONE_NAME" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" | jq -r '.result[0].id')

if [ "$ZONE_ID" == "null" ] || [ -z "$ZONE_ID" ]; then
    echo -e "${RED}❌ Erro: Não foi possível obter Zone ID${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Zone ID: $ZONE_ID${NC}"

# Função para criar/atualizar registro A
create_or_update_a_record() {
    local name=$1
    local ip=$2
    local proxied=$3
    
    echo ""
    echo -e "${YELLOW}📌 Configurando $name...${NC}"
    
    # Verificar se o registro já existe
    EXISTING_RECORD=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=A&name=$name" \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        -H "Content-Type: application/json" | jq -r '.result[0].id')
    
    if [ "$EXISTING_RECORD" != "null" ] && [ -n "$EXISTING_RECORD" ]; then
        echo "  Atualizando registro existente..."
        RESPONSE=$(curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$EXISTING_RECORD" \
            -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
            -H "Content-Type: application/json" \
            --data "{\"type\":\"A\",\"name\":\"$name\",\"content\":\"$ip\",\"ttl\":3600,\"proxied\":$proxied}")
    else
        echo "  Criando novo registro..."
        RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
            -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
            -H "Content-Type: application/json" \
            --data "{\"type\":\"A\",\"name\":\"$name\",\"content\":\"$ip\",\"ttl\":3600,\"proxied\":$proxied}")
    fi
    
    SUCCESS=$(echo $RESPONSE | jq -r '.success')
    if [ "$SUCCESS" == "true" ]; then
        echo -e "  ${GREEN}✅ $name configurado${NC}"
    else
        echo -e "  ${RED}❌ Erro ao configurar $name${NC}"
        echo $RESPONSE | jq -r '.errors'
    fi
}

# Função para criar/atualizar registro SRV
create_or_update_srv_record() {
    local service=$1
    local protocol=$2
    local priority=$3
    local weight=$4
    local port=$5
    local target=$6
    
    local name="_${service}._${protocol}.innexar.app"
    
    echo ""
    echo -e "${YELLOW}📌 Configurando SRV $name...${NC}"
    
    # Verificar se o registro já existe
    EXISTING_RECORD=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=SRV&name=$name" \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        -H "Content-Type: application/json" | jq -r '.result[0].id')
    
    local data_content="${priority} ${weight} ${port} ${target}"
    
    if [ "$EXISTING_RECORD" != "null" ] && [ -n "$EXISTING_RECORD" ]; then
        echo "  Atualizando registro SRV existente..."
        RESPONSE=$(curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$EXISTING_RECORD" \
            -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
            -H "Content-Type: application/json" \
            --data "{\"type\":\"SRV\",\"name\":\"$name\",\"data\":{\"service\":\"$service\",\"proto\":\"$protocol\",\"name\":\"innexar.app\",\"priority\":$priority,\"weight\":$weight,\"port\":$port,\"target\":\"$target\"},\"ttl\":3600}")
    else
        echo "  Criando novo registro SRV..."
        RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
            -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
            -H "Content-Type: application/json" \
            --data "{\"type\":\"SRV\",\"name\":\"$name\",\"data\":{\"service\":\"$service\",\"proto\":\"$protocol\",\"name\":\"innexar.app\",\"priority\":$priority,\"weight\":$weight,\"port\":$port,\"target\":\"$target\"},\"ttl\":3600}")
    fi
    
    SUCCESS=$(echo $RESPONSE | jq -r '.success')
    if [ "$SUCCESS" == "true" ]; then
        echo -e "  ${GREEN}✅ $name configurado${NC}"
    else
        echo -e "  ${RED}❌ Erro ao configurar $name${NC}"
        echo $RESPONSE | jq -r '.errors'
    fi
}

# Obter IP do servidor (IP real, não do Cloudflare)
echo -e "${YELLOW}🔍 Obtendo IP do servidor...${NC}"
SERVER_IP=$(curl -4 -s ifconfig.me || curl -4 -s icanhazip.com || curl -4 -s ipinfo.io/ip)
if [ -z "$SERVER_IP" ]; then
    echo -e "${RED}❌ Não foi possível obter IP do servidor automaticamente${NC}"
    echo "Por favor, informe o IP do servidor:"
    read SERVER_IP
fi

echo -e "${GREEN}✅ IP do servidor: $SERVER_IP${NC}"

# Configurar registros A para IMAP e SMTP
create_or_update_a_record "imap.innexar.app" "$SERVER_IP" "false"
create_or_update_a_record "smtp.innexar.app" "$SERVER_IP" "false"

# Configurar registros SRV para autodescobrimento
# IMAP (porta 993 - SSL/TLS)
create_or_update_srv_record "imaps" "tcp" 10 5 993 "imap.innexar.app"

# IMAP (porta 143 - STARTTLS) - opcional
create_or_update_srv_record "imap" "tcp" 10 5 143 "imap.innexar.app"

# SMTP Submission (porta 587 - STARTTLS)
create_or_update_srv_record "submission" "tcp" 10 5 587 "smtp.innexar.app"

# SMTP (porta 25) - opcional
create_or_update_srv_record "smtp" "tcp" 10 5 25 "smtp.innexar.app"

echo ""
echo -e "${GREEN}✅ Configuração DNS de email concluída!${NC}"
echo ""
echo "Registros configurados:"
echo "  - imap.innexar.app → $SERVER_IP (porta 993)"
echo "  - smtp.innexar.app → $SERVER_IP (porta 587)"
echo "  - SRV _imaps._tcp.innexar.app → imap.innexar.app:993"
echo "  - SRV _submission._tcp.innexar.app → smtp.innexar.app:587"
echo ""
echo "Aguarde alguns minutos para a propagação DNS..."

