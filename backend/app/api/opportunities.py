from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.core.database import get_db
from app.models.opportunity import Opportunity
from app.models.user import User
from app.api.dependencies import get_current_user, get_user_role_str
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal

router = APIRouter()

class OpportunityBase(BaseModel):
    name: str
    contact_id: int
    value: Optional[Decimal] = None
    stage: str = "qualificacao"
    probability: int = 0
    expected_close_date: Optional[date] = None

class OpportunityCreate(OpportunityBase):
    pass

class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    contact_id: Optional[int] = None
    value: Optional[Decimal] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    expected_close_date: Optional[date] = None

class OpportunityResponse(OpportunityBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[OpportunityResponse])
async def list_opportunities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    query = select(Opportunity)
    if get_user_role_str(current_user) == "vendedor":
        query = query.where(Opportunity.owner_id == current_user.id)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    opportunities = result.scalars().all()
    return [OpportunityResponse.model_validate(opp) for opp in opportunities]

@router.post("/", response_model=OpportunityResponse)
async def create_opportunity(
    opportunity_data: OpportunityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opportunity = Opportunity(
        **opportunity_data.model_dump(),
        owner_id=current_user.id
    )
    db.add(opportunity)
    await db.commit()
    await db.refresh(opportunity)
    return OpportunityResponse.model_validate(opportunity)

@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Opportunity).where(Opportunity.id == opportunity_id)
    if get_user_role_str(current_user) == "vendedor":
        query = query.where(Opportunity.owner_id == current_user.id)
    
    result = await db.execute(query)
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada")
    
    return OpportunityResponse.model_validate(opportunity)

@router.put("/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: int,
    opportunity_data: OpportunityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Opportunity).where(Opportunity.id == opportunity_id)
    if get_user_role_str(current_user) == "vendedor":
        query = query.where(Opportunity.owner_id == current_user.id)
    
    result = await db.execute(query)
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada")
    
    for key, value in opportunity_data.model_dump(exclude_unset=True).items():
        setattr(opportunity, key, value)
    
    await db.commit()
    await db.refresh(opportunity)
    return OpportunityResponse.model_validate(opportunity)

@router.delete("/{opportunity_id}")
async def delete_opportunity(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Opportunity).where(Opportunity.id == opportunity_id)
    if get_user_role_str(current_user) == "vendedor":
        query = query.where(Opportunity.owner_id == current_user.id)
    
    result = await db.execute(query)
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada")
    
    await db.delete(opportunity)
    await db.commit()
    return {"message": "Oportunidade deletada"}

