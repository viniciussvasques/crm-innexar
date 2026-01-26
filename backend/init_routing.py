import asyncio
from app.core.database import AsyncSessionLocal
from app.services.ai_service import AIService
from app.models.ai_config import AITaskRouting
from sqlalchemy import select

async def add_routing():
    async with AsyncSessionLocal() as db:
        # Check if exists
        result = await db.execute(select(AITaskRouting).where(AITaskRouting.task_type == 'creative_writing'))
        existing = result.scalar_one_or_none()
        
        if not existing:
            print("Creating routing for creative_writing...")
            routing = AITaskRouting(
                task_type='creative_writing', 
                primary_config_id=2,  # Config ID 2 (Cloudflare)
                temperature=0.7
            )
            db.add(routing)
            await db.commit()
            print("Done.")
        else:
            print("Routing for creative_writing already exists.")

if __name__ == "__main__":
    asyncio.run(add_routing())
