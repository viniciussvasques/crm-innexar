from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from decimal import Decimal
from datetime import datetime, date
from typing import List, Optional, Dict
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.commission import CommissionStructure, Commission, QuoteRequest
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.api.dependencies import get_current_user, get_user_role_str

router = APIRouter(prefix="/commissions", tags=["commissions"])


# Schemas
class CommissionTier(BaseModel):
    min: float
    max: Optional[float] = None
    rate: float

class PerformanceBonus(BaseModel):
    threshold: float
    bonus: float

class CommissionCalculationRequest(BaseModel):
    deal_value: float
    structure_id: Optional[int] = None

class CommissionStructureCreate(BaseModel):
    name: str
    weekly_base: float = 100.00
    currency: str = "USD"
    tiered_commissions: List[CommissionTier]
    performance_bonuses: List[PerformanceBonus]
    recurring_commission_rate: float = 0.10
    new_client_bonus: float = 100.00
    new_client_threshold: int = 10

class CommissionStructureResponse(BaseModel):
    id: int
    name: str
    weekly_base: float
    currency: str
    tiered_commissions: List[Dict]
    performance_bonuses: List[Dict]
    recurring_commission_rate: float
    new_client_bonus: float
    new_client_threshold: int
    is_active: bool

    class Config:
        from_attributes = True

class CommissionResponse(BaseModel):
    id: int
    seller_id: int
    seller_name: Optional[str] = None
    deal_value: float
    commission_amount: float
    total_amount: float
    status: str
    payment_period: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/structures", response_model=List[CommissionStructureResponse])
async def list_structures(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista estruturas de comissão - apenas admin"""
    if get_user_role_str(current_user) != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    result = await db.execute(select(CommissionStructure))
    structures = result.scalars().all()
    return structures


@router.post("/structures", response_model=CommissionStructureResponse, status_code=status.HTTP_201_CREATED)
async def create_structure(
    structure_data: CommissionStructureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cria estrutura de comissão - apenas admin"""
    if get_user_role_str(current_user) != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    structure = CommissionStructure(
        name=structure_data.name,
        weekly_base=Decimal(str(structure_data.weekly_base)),
        currency=structure_data.currency,
        tiered_commissions=[tier.dict() for tier in structure_data.tiered_commissions],
        performance_bonuses=[bonus.dict() for bonus in structure_data.performance_bonuses],
        recurring_commission_rate=Decimal(str(structure_data.recurring_commission_rate)),
        new_client_bonus=Decimal(str(structure_data.new_client_bonus)),
        new_client_threshold=structure_data.new_client_threshold
    )
    
    db.add(structure)
    await db.commit()
    await db.refresh(structure)
    
    return structure


def calculate_commission(deal_value: float, structure: CommissionStructure) -> Dict[str, Decimal]:
    """Calcula comissão baseado na estrutura"""
    deal_decimal = Decimal(str(deal_value))
    
    # Encontrar faixa de comissão
    commission_rate = Decimal("0")
    for tier in structure.tiered_commissions:
        min_val = Decimal(str(tier["min"]))
        max_val = Decimal(str(tier.get("max", float("inf"))))
        if min_val <= deal_decimal <= max_val:
            commission_rate = Decimal(str(tier["rate"]))
            break
    
    commission_amount = deal_decimal * commission_rate
    
    # Calcular bônus de performance
    performance_bonus = Decimal("0")
    for bonus in structure.performance_bonuses:
        if deal_decimal >= Decimal(str(bonus["threshold"])):
            performance_bonus = Decimal(str(bonus["bonus"]))
    
    weekly_base = structure.weekly_base
    
    total = weekly_base + commission_amount + performance_bonus
    
    return {
        "weekly_base": weekly_base,
        "commission_rate": commission_rate,
        "commission_amount": commission_amount,
        "performance_bonus": performance_bonus,
        "total_amount": total
    }


@router.post("/calculate")
async def calculate_commission(
    request: CommissionCalculationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calcula comissão baseada no valor do deal"""
    if get_user_role_str(current_user) != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")

    # Buscar estrutura ativa (ou usar padrão)
    structure = None
    if request.structure_id:
        result = await db.execute(
            select(CommissionStructure).where(
                CommissionStructure.id == request.structure_id,
                CommissionStructure.is_active == True
            )
        )
        structure = result.scalar_one_or_none()

    if not structure:
        # Usar estrutura padrão
        result = await db.execute(
            select(CommissionStructure).where(CommissionStructure.is_active == True).limit(1)
        )
        structure = result.scalar_one_or_none()

    if not structure:
        raise HTTPException(status_code=404, detail="Nenhuma estrutura de comissão ativa encontrada")

    # Calcular comissão
    result = calculate_commission(deal_value=request.deal_value, structure=structure)

    return {
        "deal_value": request.deal_value,
        "structure_used": structure.name,
        "calculation": result
    }


@router.post("/calculate/{opportunity_id}")
async def calculate_opportunity_commission(
    opportunity_id: int,
    structure_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calcula comissão para uma oportunidade"""
    # Buscar oportunidade
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada")
    
    # Verificar se é o dono ou admin
    user_role = get_user_role_str(current_user)
    if user_role != "admin" and opportunity.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Buscar estrutura (ou usar padrão)
    if structure_id:
        result = await db.execute(
            select(CommissionStructure).where(CommissionStructure.id == structure_id)
        )
        structure = result.scalar_one_or_none()
    else:
        result = await db.execute(
            select(CommissionStructure).where(CommissionStructure.is_active == True)
        )
        structure = result.scalar_one_or_none()
    
    if not structure:
        raise HTTPException(status_code=404, detail="Estrutura de comissão não encontrada")
    
    deal_value = float(opportunity.value or 0)
    calculation = calculate_commission(deal_value, structure)
    
    return {
        "opportunity_id": opportunity_id,
        "deal_value": deal_value,
        "calculation": {k: float(v) for k, v in calculation.items()},
        "structure": {
            "id": structure.id,
            "name": structure.name
        }
    }


@router.get("/", response_model=List[CommissionResponse])
async def list_commissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todas as comissões - apenas admin"""
    if get_user_role_str(current_user) != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    result = await db.execute(
        select(Commission)
        .options(selectinload(Commission.seller))
        .order_by(Commission.created_at.desc())
    )
    commissions = result.scalars().all()
    
    return [
        CommissionResponse(
            id=c.id,
            seller_id=c.seller_id,
            seller_name=c.seller.name if c.seller else None,
            deal_value=float(c.deal_value),
            commission_amount=float(c.commission_amount),
            total_amount=float(c.total_amount),
            status=c.status,
            payment_period=c.payment_period,
            created_at=c.created_at
        )
        for c in commissions
    ]


@router.get("/seller/{seller_id}", response_model=List[CommissionResponse])
async def get_seller_commissions(
    seller_id: int,
    period: Optional[str] = None,  # Formato: "2025-01"
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista comissões de um vendedor"""
    # Verificar acesso
    user_role = get_user_role_str(current_user)
    if user_role != "admin" and current_user.id != seller_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    query = select(Commission).where(Commission.seller_id == seller_id)
    
    if period:
        query = query.where(Commission.payment_period == period)
    
    result = await db.execute(query.options(selectinload(Commission.seller)))
    commissions = result.scalars().all()
    
    return [
        CommissionResponse(
            id=c.id,
            seller_id=c.seller_id,
            seller_name=c.seller.name if c.seller else None,
            deal_value=float(c.deal_value),
            commission_amount=float(c.commission_amount),
            total_amount=float(c.total_amount),
            status=c.status,
            payment_period=c.payment_period,
            created_at=c.created_at
        )
        for c in commissions
    ]

