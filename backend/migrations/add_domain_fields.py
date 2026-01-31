"""
Migration: Add domain purchase fields to site_onboardings table
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine


async def run_migration():
    """Add domain purchase related fields"""
    async with engine.begin() as conn:
        # Add new domain fields
        await conn.execute(text("""
            ALTER TABLE site_onboardings 
            ADD COLUMN IF NOT EXISTS has_existing_domain BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS existing_domain VARCHAR NULL,
            ADD COLUMN IF NOT EXISTS domain_to_purchase VARCHAR NULL,
            ADD COLUMN IF NOT EXISTS domain_purchased BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS domain_purchase_status VARCHAR NULL
        """))
        print("✅ Added domain purchase fields to site_onboardings")


if __name__ == "__main__":
    asyncio.run(run_migration())
