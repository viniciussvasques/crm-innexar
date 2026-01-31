import asyncio
import os
import sys
import logging

# Add backend to path
sys.path.append("/opt/innexar-crm/backend")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.site_order import SiteOrder, SiteOrderStatus, SiteOnboarding
from app.services.autonomous_dev_service import AutonomousDevService
from app.core.config import settings
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_autonomous_dev():
    # Database connection
    database_url = settings.DATABASE_URL
    if not database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        
    engine = create_async_engine(database_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # 1. Create Test Order (Order must exist before Onboarding due to FK)
        logger.info("🛠 Creating test order...")
        
        order = SiteOrder(
            status=SiteOrderStatus.GENERATING,
            base_price=399.0,
            stripe_payment_intent_id="pi_test_123",
            created_at=datetime.utcnow(),
            customer_name="Innexar Teste",
            customer_email="test@innexar.com",
            customer_phone="(11) 99999-9999",
            total_price=399.0,
            currency="BRL"
        )
        session.add(order)
        await session.flush()
        logger.info(f"✅ Created Order ID: {order.id}")

        onboarding = SiteOnboarding(
            order_id=order.id,
            business_name="Innexar AI Test",
            business_email="test@innexar.com",
            business_phone="(11) 99999-9999",
            niche="other",
            custom_niche="Consultoria de IA",
            primary_service="Automação Empresarial",
            primary_city="São Paulo",
            state="SP",
            tone="professional",
            primary_color="#10b981", # Emerald
            secondary_color="#0f172a", # Slate
            site_description="Somos especialistas em transformar empresas com Inteligência Artificial.",
            services=["Chatbots", "Automação de Vendas", "Análise de Dados"],
            completed_steps=7, # Integer, all steps done
            is_complete=True
        )
        session.add(onboarding)
        await session.commit()

        
        # 2. Run Autonomous Developer
        logger.info("🤖 Starting Autonomous Developer...")
        service = AutonomousDevService(session)
        
        try:
            result = await service.develop_site(order.id)
            logger.info("✨ Success!")
            logger.info(f"Result: {result}")
        except Exception as e:
            logger.error(f"❌ Failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_autonomous_dev())
