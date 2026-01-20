from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.core.database import get_db
from app.models.activity import Activity
from app.models.user import User
from app.api.dependencies import get_current_user, get_user_role_str
from pydantic import BaseModel
from datetime import datetime, date, time

router = APIRouter()

class ActivityBase(BaseModel):
    type: str  # task, call, meeting, note
    subject: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    status: str = "pending"
    contact_id: Optional[int] = None
    opportunity_id: Optional[int] = None

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(BaseModel):
    type: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    status: Optional[str] = None
    contact_id: Optional[int] = None
    opportunity_id: Optional[int] = None

class ActivityResponse(ActivityBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[ActivityResponse])
async def list_activities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
):
    query = select(Activity)
    if get_user_role_str(current_user) == "vendedor":
        query = query.where(Activity.owner_id == current_user.id)
    
    if status:
        query = query.where(Activity.status == status)
    
    query = query.offset(skip).limit(limit).order_by(Activity.due_date, Activity.due_time)
    result = await db.execute(query)
    activities = result.scalars().all()
    return [ActivityResponse.model_validate(activity) for activity in activities]

@router.post("/", response_model=ActivityResponse)
async def create_activity(
    activity_data: ActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    activity = Activity(
        **activity_data.model_dump(),
        owner_id=current_user.id
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return ActivityResponse.model_validate(activity)

@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Activity).where(Activity.id == activity_id)
    if get_user_role_str(current_user) == "vendedor":
        query = query.where(Activity.owner_id == current_user.id)
    
    result = await db.execute(query)
    activity = result.scalar_one_or_none()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Atividade não encontrada")
    
    return ActivityResponse.model_validate(activity)

@router.put("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: int,
    activity_data: ActivityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Activity).where(Activity.id == activity_id)
    if get_user_role_str(current_user) == "vendedor":
        query = query.where(Activity.owner_id == current_user.id)
    
    result = await db.execute(query)
    activity = result.scalar_one_or_none()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Atividade não encontrada")
    
    for key, value in activity_data.model_dump(exclude_unset=True).items():
        setattr(activity, key, value)
    
    await db.commit()
    await db.refresh(activity)
    return ActivityResponse.model_validate(activity)

@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Activity).where(Activity.id == activity_id)
    if get_user_role_str(current_user) == "vendedor":
        query = query.where(Activity.owner_id == current_user.id)
    
    result = await db.execute(query)
    activity = result.scalar_one_or_none()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Atividade não encontrada")
    
    await db.delete(activity)
    await db.commit()
    return {"message": "Atividade deletada"}

