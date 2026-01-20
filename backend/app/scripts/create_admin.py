import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.user import User, UserRole
from app.core.auth import get_password_hash

async def create_admin():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as db:
        # Verificar se já existe admin
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.role == UserRole.ADMIN))
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("✅ Admin já existe!")
            return
        
        # Criar admin padrão
        admin = User(
            email="admin@innexar.app",
            name="Administrador",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN
        )
        
        db.add(admin)
        await db.commit()
        print("✅ Admin criado com sucesso!")
        print("   Email: admin@innexar.app")
        print("   Senha: admin123")
        print("   ⚠️  ALTERE A SENHA APÓS O PRIMEIRO LOGIN!")

if __name__ == "__main__":
    asyncio.run(create_admin())

