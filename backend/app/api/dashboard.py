from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.models.user import User
from app.models.contact import Contact
from app.models.opportunity import Opportunity
from app.models.activity import Activity
from app.api.dependencies import get_current_user, get_user_role_str
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime, timedelta
from decimal import Decimal

router = APIRouter()

class DashboardStats(BaseModel):
    total_contacts: int
    total_opportunities: int
    total_value: Decimal
    pending_activities: int
    opportunities_by_stage: Dict[str, int]

class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_activities: List[dict]
    top_opportunities: List[dict]

@router.get("/vendedor", response_model=DashboardResponse)
async def get_vendedor_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Estatísticas do vendedor
    contacts_count = await db.scalar(
        select(func.count(Contact.id)).where(Contact.owner_id == current_user.id)
    )
    
    opportunities_count = await db.scalar(
        select(func.count(Opportunity.id)).where(Opportunity.owner_id == current_user.id)
    )
    
    total_value = await db.scalar(
        select(func.sum(Opportunity.value)).where(Opportunity.owner_id == current_user.id)
    ) or Decimal("0")
    
    pending_activities_count = await db.scalar(
        select(func.count(Activity.id)).where(
            and_(
                Activity.owner_id == current_user.id,
                Activity.status == "pending"
            )
        )
    )
    
    # Oportunidades por estágio
    opportunities_by_stage = {}
    stages = ["qualificacao", "proposta", "negociacao", "fechado", "perdido"]
    for stage in stages:
        count = await db.scalar(
            select(func.count(Opportunity.id)).where(
                and_(
                    Opportunity.owner_id == current_user.id,
                    Opportunity.stage == stage
                )
            )
        )
        opportunities_by_stage[stage] = count or 0
    
    # Atividades recentes
    activities_result = await db.execute(
        select(Activity)
        .where(Activity.owner_id == current_user.id)
        .order_by(Activity.created_at.desc())
        .limit(10)
    )
    recent_activities = [
        {
            "id": a.id,
            "type": a.type,
            "subject": a.subject,
            "status": a.status,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "created_at": a.created_at.isoformat()
        }
        for a in activities_result.scalars().all()
    ]
    
    # Top oportunidades
    opportunities_result = await db.execute(
        select(Opportunity)
        .where(Opportunity.owner_id == current_user.id)
        .order_by(Opportunity.value.desc())
        .limit(5)
    )
    top_opportunities = [
        {
            "id": o.id,
            "name": o.name,
            "value": float(o.value) if o.value else 0,
            "stage": o.stage,
            "probability": o.probability
        }
        for o in opportunities_result.scalars().all()
    ]
    
    return DashboardResponse(
        stats=DashboardStats(
            total_contacts=contacts_count or 0,
            total_opportunities=opportunities_count or 0,
            total_value=total_value,
            pending_activities=pending_activities_count or 0,
            opportunities_by_stage=opportunities_by_stage
        ),
        recent_activities=recent_activities,
        top_opportunities=top_opportunities
    )

@router.get("/admin", response_model=DashboardResponse)
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Apenas admin
    role_str = get_user_role_str(current_user)
    if role_str.lower() != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Estatísticas gerais
    contacts_count = await db.scalar(select(func.count(Contact.id)))
    opportunities_count = await db.scalar(select(func.count(Opportunity.id)))
    total_value = await db.scalar(select(func.sum(Opportunity.value))) or Decimal("0")
    pending_activities_count = await db.scalar(
        select(func.count(Activity.id)).where(Activity.status == "pending")
    )
    
    # Oportunidades por estágio
    opportunities_by_stage = {}
    stages = ["qualificacao", "proposta", "negociacao", "fechado", "perdido"]
    for stage in stages:
        count = await db.scalar(
            select(func.count(Opportunity.id)).where(Opportunity.stage == stage)
        )
        opportunities_by_stage[stage] = count or 0
    
    # Atividades recentes (todos)
    activities_result = await db.execute(
        select(Activity)
        .order_by(Activity.created_at.desc())
        .limit(10)
    )
    recent_activities = [
        {
            "id": a.id,
            "type": a.type,
            "subject": a.subject,
            "status": a.status,
            "owner_id": a.owner_id,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "created_at": a.created_at.isoformat()
        }
        for a in activities_result.scalars().all()
    ]
    
    # Top oportunidades (todas)
    opportunities_result = await db.execute(
        select(Opportunity)
        .order_by(Opportunity.value.desc())
        .limit(5)
    )
    top_opportunities = [
        {
            "id": o.id,
            "name": o.name,
            "value": float(o.value) if o.value else 0,
            "stage": o.stage,
            "probability": o.probability,
            "owner_id": o.owner_id
        }
        for o in opportunities_result.scalars().all()
    ]
    
    return DashboardResponse(
        stats=DashboardStats(
            total_contacts=contacts_count or 0,
            total_opportunities=opportunities_count or 0,
            total_value=total_value,
            pending_activities=pending_activities_count or 0,
            opportunities_by_stage=opportunities_by_stage
        ),
        recent_activities=recent_activities,
        top_opportunities=top_opportunities
    )

