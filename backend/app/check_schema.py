
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_schema():
    print("Checking database schema...")
    async with engine.connect() as conn:
        # Check if site_contracts table exists
        result = await conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'site_contracts');"))
        exists = result.scalar()
        if exists:
            print("✓ Table 'site_contracts' exists")
            # Check columns
            columns_result = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'site_contracts';"))
            columns = columns_result.all()
            print("Columns in 'site_contracts':")
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
        else:
            print("✗ Table 'site_contracts' does NOT exist")

if __name__ == "__main__":
    asyncio.run(check_schema())
