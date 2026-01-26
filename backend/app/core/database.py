from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Garantir que a URL usa asyncpg
database_url = settings.DATABASE_URL
if not database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

engine = create_async_engine(
    database_url,
    echo=True,
    future=True,
    pool_pre_ping=True,  # Verify connections before using
    pool_reset_on_return='commit'  # Reset connections on return to pool
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

