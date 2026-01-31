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
    print(f"Connecting to database...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Columns to add to site_onboardings
        columns_to_add = [
            ("has_existing_domain", "BOOLEAN DEFAULT FALSE"),
            ("existing_domain", "VARCHAR NULL"),
            ("domain_to_purchase", "VARCHAR NULL"),
            ("domain_purchased", "BOOLEAN DEFAULT FALSE"),
            ("domain_purchase_status", "VARCHAR NULL"),
        ]
        
        for col_name, col_type in columns_to_add:
            print(f"Checking {col_name}...")
            result = await conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'site_onboardings' 
                AND column_name = '{col_name}'
            """))
            
            if result.fetchone() is None:
                print(f"Adding {col_name} column...")
                try:
                    await conn.execute(text(f"""
                        ALTER TABLE site_onboardings 
                        ADD COLUMN {col_name} {col_type}
                    """))
                    print(f"✓ Column {col_name} added!")
                except Exception as e:
                    print(f"❌ Failed to add {col_name}: {e}")
            else:
                print(f"✓ Column {col_name} already exists")
    
    await engine.dispose()
    print("\n✓ Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_migration())
