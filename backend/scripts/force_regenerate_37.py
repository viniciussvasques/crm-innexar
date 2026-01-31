import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import AsyncSessionLocal
from app.services.autonomous_dev_service import AutonomousDevService

async def regenerate_37():
    async with AsyncSessionLocal() as session:
        service = AutonomousDevService(session)
        print("Starting regeneration for Order 37...")
        await service.develop_site(37)
        print("Regeneration triggered.")

if __name__ == "__main__":
    asyncio.run(regenerate_37())
