#!/usr/bin/env python3
"""
Script interno para testar o pipeline completo
Executa diretamente no backend sem precisar de API
"""
import asyncio
import sys
import os
import time
from datetime import datetime

# Adicionar o diretório app ao path
sys.path.insert(0, '/app')

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.site_order import SiteOrder, SiteOrderStatus, SiteOnboarding, SiteNiche, SiteTone, SiteCTA
from app.services.onboarding_service import OnboardingService
from app.services.site_generator_service import SiteGeneratorService
from fastapi import BackgroundTasks

# Dados de teste
TEST_ORDER_DATA = {
    "customer_name": "Teste Cliente Pipeline",
    "customer_email": f"teste-pipeline-{int(time.time())}@example.com",
    "customer_phone": "+5511999999999",
    "stripe_session_id": f"test_session_{int(time.time())}",
    "stripe_customer_id": f"test_customer_{int(time.time())}",
    "total_price": 399.0,
}

TEST_ONBOARDING_DATA = {
    "business_name": "Pizzaria Bella Italia",
    "business_email": "contato@pizzariabella.com",
    "business_phone": "+5511988888888",
    "has_whatsapp": True,
    "business_address": "Rua das Flores, 123, São Paulo, SP",
    "niche": SiteNiche.RESTAURANT,
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
    "tone": SiteTone.FRIENDLY,
    "primary_cta": SiteCTA.CALL,
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


async def create_test_order(db: AsyncSession):
    """Cria uma order de teste"""
    order = SiteOrder(
        customer_name=TEST_ORDER_DATA["customer_name"],
        customer_email=TEST_ORDER_DATA["customer_email"],
        customer_phone=TEST_ORDER_DATA["customer_phone"],
        stripe_session_id=TEST_ORDER_DATA["stripe_session_id"],
        stripe_customer_id=TEST_ORDER_DATA["stripe_customer_id"],
        total_price=TEST_ORDER_DATA["total_price"],
        status=SiteOrderStatus.PAID,  # Simular pagamento
        paid_at=datetime.utcnow()
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def submit_onboarding(db: AsyncSession, order_id: int):
    """Submete onboarding"""
    from app.api.site_orders import SiteOnboardingCreate
    
    onboarding_data = SiteOnboardingCreate(**TEST_ONBOARDING_DATA)
    service = OnboardingService(db, BackgroundTasks())
    return await service.process_onboarding(str(order_id), onboarding_data)


async def monitor_generation(db: AsyncSession, order_id: int, max_wait: int = 600):
    """Monitora o processo de geração"""
    print(f"\n🔍 Monitorando geração da order {order_id}...")
    start_time = time.time()
    
    from sqlalchemy import select
    from app.repositories.order_repository import OrderRepository
    
    repo = OrderRepository(db)
    
    while time.time() - start_time < max_wait:
        order = await repo.get_by_id(order_id)
        if not order:
            print("❌ Não foi possível obter status da order")
            break
        
        status = order.status.value if hasattr(order.status, 'value') else str(order.status)
        elapsed = int(time.time() - start_time)
        print(f"⏱️  Status: {status} (tempo: {elapsed}s)")
        
        # Obter logs recentes
        logs = await repo.get_logs(order_id)
        if logs:
            recent_logs = logs[-5:]
            for log in recent_logs:
                step = log.get("step", "")
                message = log.get("message", "")
                log_status = log.get("status", "")
                emoji = "✅" if log_status == "success" else "❌" if log_status == "error" else "ℹ️"
                print(f"   {emoji} [{step}] {message}")
        
        # Verificar se completou
        if status in ["REVIEW", "review", "COMPLETED", "completed"]:
            print(f"\n✅ Geração concluída! Status final: {status}")
            print(f"📄 Site URL: {order.site_url or 'N/A'}")
            print(f"📝 Admin Notes: {order.admin_notes or 'N/A'}")
            return True
        
        if status in ["ERROR", "error"]:
            print(f"\n❌ Geração falhou! Status: {status}")
            return False
        
        await asyncio.sleep(10)
    
    print(f"\n⏱️  Timeout após {max_wait} segundos")
    return False


async def main():
    """Função principal"""
    print("🚀 Iniciando teste do pipeline completo (modo interno)...\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Criar order
            print("1️⃣ Criando order de teste...")
            order = await create_test_order(db)
            order_id = order.id
            print(f"✅ Order criada: ID {order_id}, Status: {order.status.value}\n")
            
            # 2. Submeter onboarding
            print("2️⃣ Submetendo onboarding completo...")
            result = await submit_onboarding(db, order_id)
            print(f"✅ Onboarding submetido: {result.get('message', 'OK')}\n")
            
            # 3. Aguardar processamento
            print("3️⃣ Aguardando processamento inicial...")
            await asyncio.sleep(5)
            
            # 4. Verificar status
            from app.repositories.order_repository import OrderRepository
            repo = OrderRepository(db)
            order = await repo.get_by_id(order_id)
            if order:
                print(f"📊 Status após onboarding: {order.status.value}\n")
            
            # 5. Monitorar geração
            print("4️⃣ Iniciando monitoramento da geração...")
            success = await monitor_generation(db, order_id, max_wait=600)
            
            # 6. Resultado final
            print("\n" + "="*60)
            if success:
                print("✅ TESTE CONCLUÍDO COM SUCESSO!")
                order = await repo.get_by_id(order_id)
                if order:
                    print(f"\n📋 Resumo Final:")
                    print(f"   Order ID: {order_id}")
                    print(f"   Status: {order.status.value}")
                    print(f"   Site URL: {order.site_url or 'N/A'}")
                    print(f"   Repository URL: {order.repository_url or 'N/A'}")
                    print(f"   Admin Notes: {order.admin_notes or 'N/A'}")
            else:
                print("❌ TESTE FALHOU OU TIMEOUT")
                order = await repo.get_by_id(order_id)
                if order:
                    print(f"\n📋 Status Final:")
                    print(f"   Order ID: {order_id}")
                    print(f"   Status: {order.status.value}")
                    print(f"   Admin Notes: {order.admin_notes or 'N/A'}")
            print("="*60)
            
        except Exception as e:
            print(f"\n\n❌ Erro fatal: {e}")
            import traceback
            traceback.print_exc()
            raise


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
