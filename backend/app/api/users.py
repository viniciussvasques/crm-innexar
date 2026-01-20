from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserCreate, UserUpdate
from app.api.dependencies import get_current_user, get_user_role_str

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

@router.get("/", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Apenas admin pode listar usuários
    role_str = get_user_role_str(current_user)
    if role_str.lower() != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserResponse.model_validate(user) for user in users]

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Apenas admin pode criar usuários
    role_str = get_user_role_str(current_user)
    if role_str.lower() != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Verificar se email já existe
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    from app.core.auth import get_password_hash
    
    # Garantir que o role seja o valor do enum (string), não o nome
    role_value = user_data.role
    if isinstance(role_value, UserRole):
        # Se já for enum, usar o valor (string)
        role_value_str = role_value.value
    elif isinstance(role_value, str):
        # Se for string, validar e usar diretamente (já está em minúsculas)
        role_value_str = role_value.lower()
        if role_value_str not in [r.value for r in UserRole]:
            raise HTTPException(status_code=400, detail=f"Role inválido: {role_value}")
    else:
        raise HTTPException(status_code=400, detail=f"Role inválido: {role_value}")
    
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        role=role_value_str  # Usar string diretamente
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)

