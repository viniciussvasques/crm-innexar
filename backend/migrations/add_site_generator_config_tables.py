"""
Migration: Add Site Generator Configuration Tables
Tables: integration_configs, deploy_servers, ai_task_routing
"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Load env variables from .env file in parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# Get database URL from environment or use default (updated from .env)
# Fallback to .env values if os.getenv fails to load
DB_USER = os.getenv("DB_USER", "crm_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "InnexarCRM2026!")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "innexarcrm")

DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Ensure asyncpg driver
if not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

async def run_migration():
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        print("Starting migration for Site Generator Configuration tables...")
        
        # 1. integration_configs
        print("Checking integration_configs table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS integration_configs (
                id SERIAL PRIMARY KEY,
                integration_type VARCHAR(50) NOT NULL,
                key VARCHAR(100) NOT NULL,
                value TEXT NOT NULL,
                is_secret BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                description TEXT,
                last_tested_at TIMESTAMP,
                last_test_success BOOLEAN,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(integration_type, key)
            );
        """))
        print("✓ Table integration_configs ready")
        
        # 2. deploy_servers
        print("Checking deploy_servers table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS deploy_servers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                server_type VARCHAR(50) DEFAULT 'ssh',
                host VARCHAR(255),
                port INTEGER DEFAULT 22,
                username VARCHAR(100),
                password_encrypted TEXT,
                ssh_key_encrypted TEXT,
                deploy_path VARCHAR(500),
                is_default BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                disk_total_gb INTEGER,
                disk_used_gb INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))
        print("✓ Table deploy_servers ready")
        
        # 3. ai_task_routing
        print("Checking ai_task_routing table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_task_routing (
                id SERIAL PRIMARY KEY,
                task_type VARCHAR(50) NOT NULL UNIQUE,
                primary_config_id INTEGER NOT NULL REFERENCES ai_configs(id),
                fallback_config_id INTEGER REFERENCES ai_configs(id),
                temperature FLOAT DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 4000,
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))
        print("✓ Table ai_task_routing ready")
        
        # 4. Check if ai_configs exists (it should, but just in case we don't create it here as it's existing)
        # However, we might want to ensure indices if needed.
        
    await engine.dispose()
    print("\n✓ Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_migration())
