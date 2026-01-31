"""
Migration: Create site_order_messages table
Run this script to create the messages table for team-client communication.
"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://crm_user:senha_forte_aqui@postgres:5432/innexarcrm")

# Ensure asyncpg driver
if not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://")


async def run_migration():
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        # Check if table exists
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'site_order_messages'
            )
        """))
        table_exists = result.scalar()
        
        if not table_exists:
            print("Creating site_order_messages table...")
            await conn.execute(text("""
                CREATE TABLE site_order_messages (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER NOT NULL,
                    sender_type VARCHAR NOT NULL,
                    sender_id INTEGER,
                    sender_name VARCHAR,
                    message TEXT,
                    message_type VARCHAR DEFAULT 'message',
                    files JSON,
                    links JSON,
                    is_read BOOLEAN DEFAULT FALSE,
                    is_important BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_order FOREIGN KEY (order_id) REFERENCES site_orders(id) ON DELETE CASCADE
                )
            """))
            
            # Create indexes
            await conn.execute(text("""
                CREATE INDEX idx_site_order_messages_order_id ON site_order_messages(order_id)
            """))
            await conn.execute(text("""
                CREATE INDEX idx_site_order_messages_created_at ON site_order_messages(created_at)
            """))
            
            print("✓ Table site_order_messages created successfully!")
        else:
            print("✓ Table site_order_messages already exists")

    await engine.dispose()
    print("\n✓ Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_migration())
