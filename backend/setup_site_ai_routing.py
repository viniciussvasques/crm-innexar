import asyncio
from app.core.database import AsyncSessionLocal
from app.models.ai_config import AIConfig, AITaskRouting
from sqlalchemy import select

async def setup_routing():
    async with AsyncSessionLocal() as db:
        # Get first available AI config
        result = await db.execute(select(AIConfig).limit(1))
        config = result.scalar_one_or_none()
        
        if not config:
            print("ERROR: No AI configs found. Please create an AI config first.")
            return
        
        print(f"Using AI Config ID: {config.id} ({config.provider} - {config.model_name})")
        
        # Setup site_sitemap routing
        result = await db.execute(
            select(AITaskRouting).where(AITaskRouting.task_type == 'site_sitemap')
        )
        existing_sitemap = result.scalar_one_or_none()
        
        if not existing_sitemap:
            routing_sitemap = AITaskRouting(
                task_type='site_sitemap',
                primary_config_id=config.id,
                temperature=0.7
            )
            db.add(routing_sitemap)
            print("Created routing for 'site_sitemap'")
        else:
            print("Routing for 'site_sitemap' already exists")
        
        # Setup site_home_copy routing
        result = await db.execute(
            select(AITaskRouting).where(AITaskRouting.task_type == 'site_home_copy')
        )
        existing_home = result.scalar_one_or_none()
        
        if not existing_home:
            routing_home = AITaskRouting(
                task_type='site_home_copy',
                primary_config_id=config.id,
                temperature=0.7
            )
            db.add(routing_home)
            print("Created routing for 'site_home_copy'")
        else:
            print("Routing for 'site_home_copy' already exists")
        
        await db.commit()
        print("\nDone!")

if __name__ == "__main__":
    asyncio.run(setup_routing())
