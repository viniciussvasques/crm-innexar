
import asyncio
import sys
import os

sys.path.append("/app")
from app.core.database import AsyncSessionLocal
from app.models.ai_config import AIConfig, AITaskRouting
from app.models.site_order import SiteOrder
from app.models.site_deliverable import SiteDeliverable
from sqlalchemy import select

async def fix():
    async with AsyncSessionLocal() as db:
        # Find default config
        result = await db.execute(select(AIConfig).where(AIConfig.is_default == True))
        config = result.scalar_one_or_none()
        if not config:
            print("No default config found. Cannot add routing.")
            return

        task = "creative_writing"
        result = await db.execute(select(AITaskRouting).where(AITaskRouting.task_type == task))
        existing = result.scalar_one_or_none()
        
        if not existing:
            routing = AITaskRouting(
                task_type=task,
                primary_config_id=config.id,
                temperature=0.8
            )
            db.add(routing)
            await db.commit()
            print(f"Added routing for {task}")
        else:
            print(f"Routing for {task} already exists")

if __name__ == "__main__":
    asyncio.run(fix())
