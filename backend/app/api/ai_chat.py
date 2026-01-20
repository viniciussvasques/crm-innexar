"""
API para gerenciar histórico de chat com IA
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.user import User
from app.models.ai_chat import AIChatMessage
from app.api.dependencies import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/ai/chat", tags=["ai-chat"])

class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    message_metadata: Optional[dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna histórico de chat do usuário"""
    result = await db.execute(
        select(AIChatMessage)
        .where(AIChatMessage.user_id == current_user.id)
        .order_by(desc(AIChatMessage.created_at))
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()
    
    return [
        ChatMessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            message_metadata=m.message_metadata,
            created_at=m.created_at
        )
        for m in reversed(messages)  # Reverter para ordem cronológica
    ]

@router.delete("/history")
async def clear_chat_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Limpa histórico de chat do usuário"""
    result = await db.execute(
        select(AIChatMessage).where(AIChatMessage.user_id == current_user.id)
    )
    messages = result.scalars().all()
    
    for message in messages:
        await db.delete(message)
    
    await db.commit()
    
    return {"message": "Histórico limpo com sucesso"}

