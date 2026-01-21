"""
Migration: Add custom_niche column to site_onboardings table
Run this script to add the new column for custom niche support
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
            WHERE table_name = 'site_onboardings' 
            AND column_name = 'custom_niche'
        """))
        
        if result.fetchone() is None:
            print("Adding custom_niche column...")
            await conn.execute(text("""
                ALTER TABLE site_onboardings 
                ADD COLUMN custom_niche VARCHAR NULL
            """))
            print("✓ Column custom_niche added successfully!")
        else:
            print("✓ Column custom_niche already exists")
        
        # Also ensure all other new columns exist
        columns_to_add = [
            ("site_objective", "VARCHAR NULL"),
            ("site_description", "TEXT NULL"),
            ("selected_pages", "JSON NULL"),
            ("total_pages", "INTEGER DEFAULT 5"),
            ("cta_text", "VARCHAR NULL"),
            ("accent_color", "VARCHAR NULL"),
            ("reference_sites", "JSON NULL"),
            ("design_notes", "TEXT NULL"),
            ("is_complete", "BOOLEAN DEFAULT FALSE"),
            ("completed_steps", "INTEGER DEFAULT 0"),
        ]
        
        for col_name, col_type in columns_to_add:
            result = await conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'site_onboardings' 
                AND column_name = '{col_name}'
            """))
            
            if result.fetchone() is None:
                print(f"Adding {col_name} column...")
                await conn.execute(text(f"""
                    ALTER TABLE site_onboardings 
                    ADD COLUMN {col_name} {col_type}
                """))
                print(f"✓ Column {col_name} added!")
            else:
                print(f"✓ Column {col_name} already exists")
    
    await engine.dispose()
    print("\n✓ Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_migration())
