#!/usr/bin/env python3
"""
Script para testar o pipeline completo de geração de sites
Cria uma order, completa onboarding e monitora a geração
"""
import asyncio
import httpx
import sys
import time
from datetime import datetime

# Configuração
import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@innexar.app")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # Ajustar conforme necessário

# Dados de teste
TEST_ORDER_DATA = {
    "customer_name": "Teste Cliente",
    "customer_email": f"teste-{int(time.time())}@example.com",
    "customer_phone": "+5511999999999",
    "stripe_session_id": f"test_session_{int(time.time())}",
    "stripe_customer_id": f"test_customer_{int(time.time())}",
    "total_price": 399.0,
    "addon_ids": []
}

TEST_ONBOARDING_DATA = {
    "business_name": "Pizzaria Bella Italia",
    "business_email": "contato@pizzariabella.com",
    "business_phone": "+5511988888888",
    "has_whatsapp": True,
    "business_address": "Rua das Flores, 123, São Paulo, SP",
    "niche": "restaurant",
    "custom_niche": None,
    "primary_city": "São Paulo",
    "state": "SP",
    "service_areas": ["São Paulo", "Guarulhos", "Osasco"],
    "services": ["Pizzas Artesanais", "Massas", "Bebidas", "Sobremesas"],
    "primary_service": "Pizzas Artesanais",
    "site_objective": "generate_leads",
    "site_description": "Pizzaria italiana tradicional com receitas autênticas e ingredientes frescos. Atendemos delivery e balcão.",
    "selected_pages": ["Home", "Sobre", "Cardápio", "Contato", "Depoimentos"],
    "total_pages": 5,
    "tone": "friendly",
    "primary_cta": "call",
    "cta_text": "Peça Agora",
    "primary_color": "#FF6B35",
    "secondary_color": "#004E89",
    "accent_color": "#FFA500",
    "reference_sites": [],
    "design_notes": "Design moderno e acolhedor, cores quentes que remetem à Itália",
    "business_hours": {
        "monday": "18:00-23:00",
        "tuesday": "18:00-23:00",
        "wednesday": "18:00-23:00",
        "thursday": "18:00-23:00",
        "friday": "18:00-00:00",
        "saturday": "18:00-00:00",
        "sunday": "18:00-22:00"
    },
    "social_facebook": "https://facebook.com/pizzariabella",
    "social_instagram": "https://instagram.com/pizzariabella",
    "social_linkedin": None,
    "social_youtube": None,
    "testimonials": [
        {
            "name": "João Silva",
            "text": "Melhor pizza da região! Sempre fresca e deliciosa.",
            "rating": 5
        },
        {
            "name": "Maria Santos",
            "text": "Atendimento excelente e entrega rápida.",
            "rating": 5
        }
    ],
    "google_reviews_link": "https://g.page/r/pizzariabella/review",
    "about_owner": "Família italiana com mais de 30 anos de experiência na arte da pizza.",
    "years_in_business": 15,
    "is_complete": True,
    "completed_steps": 7,
    "password": None
}


async def login_admin():
    """Faz login como admin e retorna token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_URL}/api/auth/login",
            data={
                "username": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
        )
        if response.status_code != 200:
            print(f"❌ Erro ao fazer login: {response.status_code} - {response.text}")
            return None
        data = response.json()
        return data.get("access_token")


async def create_order(token: str):
    """Cria uma order de teste"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(
            f"{BACKEND_URL}/api/site-orders/",
            json=TEST_ORDER_DATA,
            headers=headers
        )
        if response.status_code not in [200, 201]:
            print(f"❌ Erro ao criar order: {response.status_code} - {response.text}")
            return None
        order = response.json()
        print(f"✅ Order criada: ID {order.get('id')}, Status: {order.get('status')}")
        return order


async def update_order_status(token: str, order_id: int, status: str):
    """Atualiza status da order (simula pagamento)"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.patch(
            f"{BACKEND_URL}/api/site-orders/{order_id}/status",
            json={"status": status},
            headers=headers
        )
        if response.status_code != 200:
            print(f"❌ Erro ao atualizar status: {response.status_code} - {response.text}")
            return False
        print(f"✅ Status atualizado para: {status}")
        return True


async def submit_onboarding(token: str, order_identifier: str):
    """Submete onboarding completo"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(
            f"{BACKEND_URL}/api/site-orders/{order_identifier}/onboarding",
            json=TEST_ONBOARDING_DATA,
            headers=headers
        )
        if response.status_code not in [200, 201]:
            print(f"❌ Erro ao submeter onboarding: {response.status_code} - {response.text}")
            return False
        result = response.json()
        print(f"✅ Onboarding submetido: {result.get('message')}")
        return True


async def get_order_status(token: str, order_id: int):
    """Obtém status atual da order"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(
            f"{BACKEND_URL}/api/site-orders/{order_id}",
            headers=headers
        )
        if response.status_code != 200:
            return None
        return response.json()


async def get_generation_logs(token: str, order_id: int):
    """Obtém logs de geração"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(
            f"{BACKEND_URL}/api/site-orders/{order_id}/logs",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        return []


async def monitor_generation(token: str, order_id: int, max_wait: int = 300):
    """Monitora o processo de geração"""
    print(f"\n🔍 Monitorando geração da order {order_id}...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        order = await get_order_status(token, order_id)
        if not order:
            print("❌ Não foi possível obter status da order")
            break
        
        status = order.get("status")
        print(f"⏱️  Status atual: {status} (tempo: {int(time.time() - start_time)}s)")
        
        # Obter logs recentes
        logs = await get_generation_logs(token, order_id)
        if logs:
            recent_logs = logs[-5:]  # Últimos 5 logs
            for log in recent_logs:
                step = log.get("step", "")
                message = log.get("message", "")
                log_status = log.get("status", "")
                emoji = "✅" if log_status == "success" else "❌" if log_status == "error" else "ℹ️"
                print(f"   {emoji} [{step}] {message}")
        
        # Verificar se completou
        if status in ["REVIEW", "COMPLETED"]:
            print(f"\n✅ Geração concluída! Status final: {status}")
            print(f"📄 Site URL: {order.get('site_url', 'N/A')}")
            print(f"📝 Admin Notes: {order.get('admin_notes', 'N/A')}")
            return True
        
        if status == "ERROR":
            print(f"\n❌ Geração falhou! Status: {status}")
            return False
        
        await asyncio.sleep(10)  # Aguardar 10 segundos antes de verificar novamente
    
    print(f"\n⏱️  Timeout após {max_wait} segundos")
    return False


async def main():
    """Função principal"""
    print("🚀 Iniciando teste do pipeline completo...\n")
    
    # 1. Login
    print("1️⃣ Fazendo login como admin...")
    token = await login_admin()
    if not token:
        print("❌ Falha no login. Abortando.")
        return
    print("✅ Login realizado com sucesso\n")
    
    # 2. Criar order
    print("2️⃣ Criando order de teste...")
    order = await create_order(token)
    if not order:
        print("❌ Falha ao criar order. Abortando.")
        return
    order_id = order.get("id")
    order_identifier = order.get("stripe_session_id") or str(order_id)
    print()
    
    # 3. Simular pagamento (atualizar status para PAID)
    print("3️⃣ Simulando pagamento...")
    await update_order_status(token, order_id, "PAID")
    print()
    
    # 4. Submeter onboarding
    print("4️⃣ Submetendo onboarding completo...")
    await submit_onboarding(token, order_identifier)
    print()
    
    # 5. Aguardar um pouco para o sistema processar
    print("5️⃣ Aguardando processamento inicial...")
    await asyncio.sleep(5)
    
    # 6. Verificar status inicial
    order = await get_order_status(token, order_id)
    if order:
        print(f"📊 Status após onboarding: {order.get('status')}")
        print()
    
    # 7. Monitorar geração
    print("6️⃣ Iniciando monitoramento da geração...")
    success = await monitor_generation(token, order_id, max_wait=600)  # 10 minutos
    
    # 8. Resultado final
    print("\n" + "="*60)
    if success:
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        order = await get_order_status(token, order_id)
        if order:
            print(f"\n📋 Resumo Final:")
            print(f"   Order ID: {order_id}")
            print(f"   Status: {order.get('status')}")
            print(f"   Site URL: {order.get('site_url', 'N/A')}")
            print(f"   Repository URL: {order.get('repository_url', 'N/A')}")
            print(f"   Admin Notes: {order.get('admin_notes', 'N/A')}")
    else:
        print("❌ TESTE FALHOU OU TIMEOUT")
        print(f"\n📋 Status Final:")
        order = await get_order_status(token, order_id)
        if order:
            print(f"   Order ID: {order_id}")
            print(f"   Status: {order.get('status')}")
            print(f"   Admin Notes: {order.get('admin_notes', 'N/A')}")
    print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
