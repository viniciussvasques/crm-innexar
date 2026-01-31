"""
Migration: Add preferred_locale column to site_customers table
Run this script to add the new column used to store the customer's preferred locale.
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
        # Check if column exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'site_customers' 
              AND column_name = 'preferred_locale'
        """))

        if result.fetchone() is None:
            print("Adding preferred_locale column to site_customers...")
            await conn.execute(text("""
                ALTER TABLE site_customers 
                ADD COLUMN preferred_locale VARCHAR NULL
            """))
            # Default existing rows to 'en'
            await conn.execute(text("""
                UPDATE site_customers 
                SET preferred_locale = 'en' 
                WHERE preferred_locale IS NULL
            """))
            print("✓ Column preferred_locale added successfully!")
        else:
            print("✓ Column preferred_locale already exists")

    await engine.dispose()
    print("\n✓ Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_migration())

