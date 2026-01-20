"""
Site Orders API - Gerenciamento de pedidos de sites Launch
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User
from app.models.site_order import (
    SiteOrder, SiteOrderStatus, SiteOnboarding, SiteAddon, 
    SiteOrderAddon, SiteTemplate, SiteNiche, SiteTone, SiteCTA
)
from app.api.dependencies import get_current_user, require_admin


router = APIRouter(prefix="/site-orders", tags=["site-orders"])


# ============== Pydantic Schemas ==============

class SiteOrderCreate(BaseModel):
    customer_name: str
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    stripe_session_id: str
    stripe_customer_id: Optional[str] = None
    total_price: float
    addon_ids: List[int] = []


class SiteOnboardingCreate(BaseModel):
    business_name: str
    business_email: EmailStr
    business_phone: str
    has_whatsapp: bool = False
    niche: SiteNiche
    primary_city: str
    state: str
    services: List[str]
    primary_service: str
    tone: SiteTone = SiteTone.PROFESSIONAL
    primary_cta: SiteCTA = SiteCTA.CALL
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None


class SiteOrderStatusUpdate(BaseModel):
    status: SiteOrderStatus
    admin_notes: Optional[str] = None
    site_url: Optional[str] = None
    repository_url: Optional[str] = None


class SiteOrderResponse(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    customer_phone: Optional[str]
    status: SiteOrderStatus
    total_price: float
    delivery_days: int
    expected_delivery_date: Optional[datetime]
    revisions_included: int
    revisions_used: int
    site_url: Optional[str]
    created_at: datetime
    paid_at: Optional[datetime]
    onboarding_completed_at: Optional[datetime]
    delivered_at: Optional[datetime]

    class Config:
        from_attributes = True


class SiteAddonCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    price: float
    is_subscription: bool = False
    subscription_interval: Optional[str] = None
    stripe_price_id: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class SiteTemplateCreate(BaseModel):
    name: str
    slug: str
    niche: SiteNiche
    description: Optional[str] = None
    preview_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    default_colors: Optional[dict] = None
    default_sections: Optional[List[str]] = None
    is_active: bool = True
    sort_order: int = 0


# ============== Order Endpoints ==============

@router.get("/")
async def list_orders(
    status_filter: Optional[SiteOrderStatus] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Lista todos os pedidos de site (admin only)"""
    query = select(SiteOrder).options(
        selectinload(SiteOrder.onboarding),
        selectinload(SiteOrder.addons)
    ).order_by(SiteOrder.created_at.desc())
    
    if status_filter:
        query = query.where(SiteOrder.status == status_filter)
    
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return orders


@router.get("/stats")
async def get_order_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Estatísticas de pedidos"""
    # Total por status
    status_counts = await db.execute(
        select(SiteOrder.status, func.count(SiteOrder.id))
        .group_by(SiteOrder.status)
    )
    
    # Revenue total
    revenue = await db.execute(
        select(func.sum(SiteOrder.total_price))
        .where(SiteOrder.status != SiteOrderStatus.CANCELLED)
    )
    
    # Pedidos este mês
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_orders = await db.execute(
        select(func.count(SiteOrder.id))
        .where(SiteOrder.created_at >= month_start)
    )
    
    return {
        "status_counts": dict(status_counts.all()),
        "total_revenue": revenue.scalar() or 0,
        "orders_this_month": monthly_orders.scalar() or 0
    }


@router.get("/{order_id}")
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Obtém detalhes de um pedido"""
    result = await db.execute(
        select(SiteOrder)
        .options(
            selectinload(SiteOrder.onboarding),
            selectinload(SiteOrder.addons).selectinload(SiteOrderAddon.addon)
        )
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order


@router.post("/")
async def create_order(
    order_data: SiteOrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """Cria um novo pedido (chamado pelo webhook do Stripe)"""
    order = SiteOrder(
        customer_name=order_data.customer_name,
        customer_email=order_data.customer_email,
        customer_phone=order_data.customer_phone,
        stripe_session_id=order_data.stripe_session_id,
        stripe_customer_id=order_data.stripe_customer_id,
        total_price=order_data.total_price,
        status=SiteOrderStatus.PAID,
        paid_at=datetime.utcnow(),
        expected_delivery_date=datetime.utcnow() + timedelta(days=5)
    )
    
    db.add(order)
    await db.flush()
    
    # Adiciona addons
    for addon_id in order_data.addon_ids:
        addon = await db.get(SiteAddon, addon_id)
        if addon:
            order_addon = SiteOrderAddon(
                order_id=order.id,
                addon_id=addon_id,
                price_paid=addon.price
            )
            db.add(order_addon)
    
    await db.commit()
    await db.refresh(order)
    
    return order


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: int,
    status_data: SiteOrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Atualiza status de um pedido"""
    order = await db.get(SiteOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = status_data.status
    
    if status_data.admin_notes:
        order.admin_notes = status_data.admin_notes
    if status_data.site_url:
        order.site_url = status_data.site_url
    if status_data.repository_url:
        order.repository_url = status_data.repository_url
    
    # Atualiza timestamps especiais
    if status_data.status == SiteOrderStatus.DELIVERED:
        order.delivered_at = datetime.utcnow()
        order.actual_delivery_date = datetime.utcnow()
    
    await db.commit()
    await db.refresh(order)
    
    return order


# ============== Onboarding Endpoints ==============

@router.post("/{order_id}/onboarding")
async def submit_onboarding(
    order_id: int,
    onboarding_data: SiteOnboardingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Cliente submete dados do onboarding"""
    order = await db.get(SiteOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.onboarding_completed_at:
        raise HTTPException(status_code=400, detail="Onboarding already completed")
    
    onboarding = SiteOnboarding(
        order_id=order_id,
        business_name=onboarding_data.business_name,
        business_email=onboarding_data.business_email,
        business_phone=onboarding_data.business_phone,
        has_whatsapp=onboarding_data.has_whatsapp,
        niche=onboarding_data.niche,
        primary_city=onboarding_data.primary_city,
        state=onboarding_data.state,
        services=onboarding_data.services,
        primary_service=onboarding_data.primary_service,
        tone=onboarding_data.tone,
        primary_cta=onboarding_data.primary_cta,
        primary_color=onboarding_data.primary_color,
        secondary_color=onboarding_data.secondary_color
    )
    
    db.add(onboarding)
    
    # Atualiza status do pedido
    order.status = SiteOrderStatus.BUILDING
    order.onboarding_completed_at = datetime.utcnow()
    order.expected_delivery_date = datetime.utcnow() + timedelta(days=order.delivery_days)
    
    await db.commit()
    
    return {"message": "Onboarding submitted successfully", "order_id": order_id}


@router.get("/{order_id}/onboarding")
async def get_onboarding(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Obtém dados do onboarding de um pedido"""
    result = await db.execute(
        select(SiteOnboarding).where(SiteOnboarding.order_id == order_id)
    )
    onboarding = result.scalar_one_or_none()
    
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding not found")
    
    return onboarding


# ============== Addon Endpoints ==============

@router.get("/addons/list")
async def list_addons(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Lista todos os addons disponíveis"""
    query = select(SiteAddon).order_by(SiteAddon.sort_order)
    if active_only:
        query = query.where(SiteAddon.is_active == True)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/addons")
async def create_addon(
    addon_data: SiteAddonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Cria um novo addon"""
    addon = SiteAddon(**addon_data.model_dump())
    db.add(addon)
    await db.commit()
    await db.refresh(addon)
    return addon


@router.patch("/addons/{addon_id}")
async def update_addon(
    addon_id: int,
    addon_data: SiteAddonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Atualiza um addon"""
    addon = await db.get(SiteAddon, addon_id)
    if not addon:
        raise HTTPException(status_code=404, detail="Addon not found")
    
    for key, value in addon_data.model_dump().items():
        setattr(addon, key, value)
    
    await db.commit()
    await db.refresh(addon)
    return addon


# ============== Template Endpoints ==============

@router.get("/templates/list")
async def list_templates(
    niche: Optional[SiteNiche] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Lista templates disponíveis"""
    query = select(SiteTemplate).order_by(SiteTemplate.sort_order)
    
    if active_only:
        query = query.where(SiteTemplate.is_active == True)
    if niche:
        query = query.where(SiteTemplate.niche == niche)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/templates")
async def create_template(
    template_data: SiteTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Cria um novo template"""
    template = SiteTemplate(**template_data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.patch("/templates/{template_id}")
async def update_template(
    template_id: int,
    template_data: SiteTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Atualiza um template"""
    template = await db.get(SiteTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for key, value in template_data.model_dump().items():
        setattr(template, key, value)
    
    await db.commit()
    await db.refresh(template)
    return template
