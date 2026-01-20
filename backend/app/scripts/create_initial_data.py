"""
Script para criar dados iniciais e atualizar estrutura do banco
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.database import Base
from app.models.user import User, UserRole
from app.models.contact import Contact
from app.models.opportunity import Opportunity
from app.models.activity import Activity
from app.models.project import Project
from app.core.auth import get_password_hash
from app.core.config import settings

async def init_db():
    """Inicializa banco de dados e cria tabelas"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        # Verificar se já existe admin
        from sqlalchemy import select
        admin = await session.scalar(
            select(User).where(User.email == "admin@innexar.app")
        )
        
        if not admin:
            admin = User(
                email="admin@innexar.app",
                name="Administrador",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(admin)
            await session.commit()
            print("✅ Admin criado: admin@innexar.app / admin123")
        else:
            print("ℹ️  Admin já existe")
        
        # Criar usuário de planejamento de exemplo
        planejamento = await session.scalar(
            select(User).where(User.email == "planejamento@innexar.app")
        )
        
        if not planejamento:
            planejamento = User(
                email="planejamento@innexar.app",
                name="Equipe de Planejamento",
                password_hash=get_password_hash("planejamento123"),
                role=UserRole.PLANEJAMENTO,
                is_active=True
            )
            session.add(planejamento)
            await session.commit()
            print("✅ Planejamento criado: planejamento@innexar.app / planejamento123")
        else:
            print("ℹ️  Planejamento já existe")
        
        # Criar usuário de desenvolvimento de exemplo
        dev = await session.scalar(
            select(User).where(User.email == "dev@innexar.app")
        )
        
        if not dev:
            dev = User(
                email="dev@innexar.app",
                name="Equipe de Desenvolvimento",
                password_hash=get_password_hash("dev123"),
                role=UserRole.DEV,
                is_active=True
            )
            session.add(dev)
            await session.commit()
            print("✅ Dev criado: dev@innexar.app / dev123")
        else:
            print("ℹ️  Dev já existe")
    
    await engine.dispose()
    print("✅ Banco de dados inicializado com sucesso!")

if __name__ == "__main__":
    asyncio.run(init_db())

