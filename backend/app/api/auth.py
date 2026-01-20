from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.auth import verify_password, get_password_hash, create_access_token
from app.models.user import User
from app.api.dependencies import get_user_role_str, require_admin
from app.schemas.user import UserLogin, Token, UserResponse, UserCreate
from datetime import timedelta
from app.core.config import settings

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    # Buscar usuário
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    
    # Criar token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": get_user_role_str(user)}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate, 
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)  # Only admins can register new users
):
    """
    Create a new user. ADMIN ONLY.
    Requires valid admin authentication token.
    """
    # Verificar se email já existe
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Criar usuário
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)

