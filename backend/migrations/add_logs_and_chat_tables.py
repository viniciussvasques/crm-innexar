"""
Migration: Add Site Generation Logs and Chat tables
"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

DB_USER = os.getenv("DB_USER", "crm_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "InnexarCRM2026!")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "innexarcrm")

DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

if not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

async def run_migration():
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        print("Creating tables for Realtime Monitoring and Chat...")
        
        # 1. Site Generation Logs
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS site_generation_logs (
                id SERIAL PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES site_orders(id),
                step VARCHAR(100) NOT NULL,
                message TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'info', -- info, success, error, warning
                details JSON,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_site_generation_logs_order_id ON site_generation_logs(order_id);"))
        print("✓ Table site_generation_logs created")
        
        # 2. Chat Threads (Context for AI Chat in IDE)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_threads (
                id SERIAL PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES site_orders(id),
                title VARCHAR(200),
                is_archived BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chat_threads_order_id ON chat_threads(order_id);"))
        print("✓ Table chat_threads created")

        # 3. Chat Messages
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                thread_id INTEGER NOT NULL REFERENCES chat_threads(id),
                role VARCHAR(20) NOT NULL, -- user, assistant, system
                content TEXT NOT NULL,
                context_files JSON, -- List of files relevant to this message
                tokens_used INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chat_messages_thread_id ON chat_messages(thread_id);"))
        print("✓ Table chat_messages created")
        
    await engine.dispose()
    print("\n✓ Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_migration())
