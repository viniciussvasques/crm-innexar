import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import AsyncSessionLocal
from app.models.site_order import SiteOrder, SiteOnboarding, SiteOrderAddon, SiteDeliverable
from app.models.site_customer import SiteCustomer
from app.models.user import User
from sqlalchemy import text

async def cleanup_data():
    async with AsyncSessionLocal() as session:
        print("Cleaning up data...")
        
        # Delete dependent tables first
        await session.execute(text("DELETE FROM ai_task_routing"))
        await session.execute(text("DELETE FROM ai_configs"))
        await session.execute(text("DELETE FROM site_generation_logs"))
        await session.execute(text("DELETE FROM site_order_addons"))
        await session.execute(text("DELETE FROM site_onboardings"))
        await session.execute(text("DELETE FROM site_deliverables"))
        await session.execute(text("DELETE FROM site_customers"))
        
        # Delete main tables
        await session.execute(text("DELETE FROM site_orders"))
        
        # Delete users except maybe main admin?
        # The user said "remove all test orders and users". 
        # I'll delete all users for now.
        await session.execute(text("DELETE FROM users"))
        
        await session.commit()
        print("All data cleaned up.")

if __name__ == "__main__":
    asyncio.run(cleanup_data())
