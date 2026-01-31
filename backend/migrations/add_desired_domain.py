"""
Migration: Add desired_domain column to site_onboardings table
Run: python -m migrations.add_desired_domain (from backend dir)
"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://crm_user:innexar@localhost:5432/innexarcrm")
if not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://").replace("postgresql+psycopg2://", "postgresql+asyncpg://")

async def run_migration():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'site_onboardings' AND column_name = 'desired_domain'
        """))
        if result.fetchone() is None:
            await conn.execute(text("ALTER TABLE site_onboardings ADD COLUMN desired_domain VARCHAR NULL"))
            print("✓ desired_domain added")
        else:
            print("✓ desired_domain already exists")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migration())
