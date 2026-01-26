import asyncio
import sys
import stripe
from app.services.stripe_service import StripeService
from app.core.database import AsyncSessionLocal
from app.models.system_config import SystemConfig
from sqlalchemy import select

# Mock keys for testing
TEST_SECRET_KEY = "sk_test_1234567890abcdef"
TEST_WEBHOOK_SECRET = "whsec_test_secret"

async def verify_config():
    print("Verifying Stripe Configuration Loading...")
    
    async with AsyncSessionLocal() as db:
        # 1. Ensure keys exist in DB (or insert/update them)
        print("Seting up test keys in DB...")
        
        # Helper to update/insert
        async def set_config(key, value, is_secret=True):
            result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
            config = result.scalar_one_or_none()
            if config:
                config.value = value
            else:
                config = SystemConfig(key=key, value=value, category="stripe", is_secret=is_secret)
                db.add(config)
        
        await set_config("stripe_secret_key", TEST_SECRET_KEY)
        await set_config("stripe_webhook_secret", TEST_WEBHOOK_SECRET)
        await set_config("stripe_enabled", "true", False)
        await db.commit()
        
        # 2. Test Service Loading
        print("Testing StripeService...")
        service = StripeService(db)
        # Force load
        await service._load_config()
        
        print(f"Loaded API Key: {service.api_key}")
        print(f"Global Stripe Key: {stripe.api_key}")
        
        if service.api_key == TEST_SECRET_KEY and stripe.api_key == TEST_SECRET_KEY:
             print("✅ Success: Stripe API Key loaded from DB and set globally!")
        else:
             print("❌ Failure: Stripe API Key mismatch.")
             
        if service.webhook_secret == TEST_WEBHOOK_SECRET:
             print("✅ Success: Webhook Secret loaded from DB!")
        else:
             print("❌ Failure: Webhook Secret mismatch.")

if __name__ == "__main__":
    asyncio.run(verify_config())
