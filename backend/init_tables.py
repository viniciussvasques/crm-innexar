import asyncio
import sys
import os

# Add /app to sys.path to ensure imports work
sys.path.append("/app")

from app.core.database import Base, engine
# Import ALL models that need to be created to register them with Base
try:
    from app.models.site_order import SiteOrder, SiteOnboarding #, SiteCustomer
    from app.models.site_deliverable import SiteDeliverable
    from app.models.site_customer import SiteCustomer
except ImportError as e:
    print(f"Import Error: {e}")
    # Continue anyway, maybe partially works
    pass

async def init():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

if __name__ == "__main__":
    asyncio.run(init())
