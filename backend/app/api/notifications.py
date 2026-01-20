from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.core.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.api.dependencies import get_current_user, get_user_role_str
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter(prefix="/notifications", tags=["notifications"])

class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str = "info"  # info, success, warning, error
    recipient_id: int
    related_entity_type: str = None  # opportunity, project, activity, etc.
    related_entity_id: int = None

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    recipient_id: int
    is_read: bool
    created_at: datetime
    related_entity_type: str = None
    related_entity_id: int = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Busca notificações do usuário atual"""
    query = select(Notification).where(Notification.recipient_id == current_user.id)

    if unread_only:
        query = query.where(Notification.is_read == False)

    query = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    notifications = result.scalars().all()

    return notifications

@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marca notificação como lida"""
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.recipient_id == current_user.id
            )
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")

    notification.is_read = True
    await db.commit()

    return {"message": "Notificação marcada como lida"}

@router.put("/mark-all-read")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marca todas as notificações como lidas"""
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.recipient_id == current_user.id,
                Notification.is_read == False
            )
        )
    )
    notifications = result.scalars().all()

    for notification in notifications:
        notification.is_read = True

    await db.commit()

    return {"message": f"{len(notifications)} notificações marcadas como lidas"}

@router.post("/", response_model=NotificationResponse, status_code=201)
async def create_notification(
    notification_data: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cria nova notificação - apenas admin ou sistema"""
    if get_user_role_str(current_user) not in ["admin"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    notification = Notification(
        title=notification_data.title,
        message=notification_data.message,
        type=notification_data.type,
        recipient_id=notification_data.recipient_id,
        related_entity_type=notification_data.related_entity_type,
        related_entity_id=notification_data.related_entity_id
    )

    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    return notification

# Função utilitária para criar notificações
async def create_notification_for_user(
    db: AsyncSession,
    recipient_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    related_entity_type: str = None,
    related_entity_id: int = None
):
    """Função utilitária para criar notificações"""
    notification = Notification(
        title=title,
        message=message,
        type=notification_type,
        recipient_id=recipient_id,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id
    )

    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    return notification
