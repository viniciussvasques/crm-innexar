"""
Migration: Add BRIEFING and PREVIEW status to site_order_status enum
Run this script to add the new status values for manual workflow.
"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://innexar:innexar123@localhost:5432/innexar_crm")

# Ensure asyncpg driver
if not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://")


async def run_migration():
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        # Check current enum values
        result = await conn.execute(text("""
            SELECT unnest(enum_range(NULL::siteorderstatus))::text as status
        """))
        existing_statuses = [row[0] for row in result.fetchall()]
        print(f"Current statuses: {existing_statuses}")

        # Add BRIEFING if it doesn't exist
        if "briefing" not in existing_statuses:
            print("Adding 'briefing' to siteorderstatus enum...")
            await conn.execute(text("""
                ALTER TYPE siteorderstatus ADD VALUE IF NOT EXISTS 'briefing'
            """))
            print("✓ Status 'briefing' added!")
        else:
            print("✓ Status 'briefing' already exists")

        # Add PREVIEW if it doesn't exist
        if "preview" not in existing_statuses:
            print("Adding 'preview' to siteorderstatus enum...")
            await conn.execute(text("""
                ALTER TYPE siteorderstatus ADD VALUE IF NOT EXISTS 'preview'
            """))
            print("✓ Status 'preview' added!")
        else:
            print("✓ Status 'preview' already exists")

    await engine.dispose()
    print("\n✓ Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_migration())
