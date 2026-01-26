"""
Site Orders API - Gerenciamento de pedidos de sites Launch
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User
from app.models.site_order import (
    SiteOrder, SiteOrderStatus, SiteOnboarding, SiteAddon, 
    SiteOrderAddon, SiteTemplate, SiteNiche, SiteTone, SiteCTA
)
from app.models.site_deliverable import SiteDeliverable, DeliverableType, DeliverableStatus
from app.api.dependencies import get_current_user, require_admin
from app.api.site_customers import create_customer_account
from app.services.email_service import email_service
from app.services.site_generator_service import SiteGeneratorService
from app.services.ai_service import AIService
from app.services.stripe_service import StripeService
from app.repositories.order_repository import OrderRepository
from app.repositories.catalog_repository import CatalogRepository
from fastapi import Request
import stripe
import json


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
    # Step 1: Business Identity
    business_name: str
    business_email: EmailStr
    business_phone: str
    has_whatsapp: bool = False
    business_address: Optional[str] = None
    
    # Step 2: Niche & Location
    niche: SiteNiche
    custom_niche: Optional[str] = None
    primary_city: str
    state: str
    service_areas: Optional[List[str]] = None
    
    # Step 3: Services
    services: List[str]
    primary_service: str
    
    # Step 4: Site Objective & Pages
    site_objective: Optional[str] = None
    site_description: Optional[str] = None
    selected_pages: Optional[List[str]] = None
    total_pages: Optional[int] = 5
    tone: SiteTone = SiteTone.PROFESSIONAL
    primary_cta: SiteCTA = SiteCTA.CALL
    cta_text: Optional[str] = None
    
    # Step 5: Design & Colors
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    reference_sites: Optional[List[str]] = None
    design_notes: Optional[str] = None
    
    # Step 6: Business Details
    business_hours: Optional[dict] = None
    social_facebook: Optional[str] = None
    social_instagram: Optional[str] = None
    social_linkedin: Optional[str] = None
    social_youtube: Optional[str] = None
    
    # Step 7: Testimonials & About
    testimonials: Optional[List[dict]] = None
    google_reviews_link: Optional[str] = None
    about_owner: Optional[str] = None
    years_in_business: Optional[int] = None
    
    # Metadata
    is_complete: bool = False
    completed_steps: int = 0
    
    # Account creation
    password: Optional[str] = None


class SiteOrderStatusUpdate(BaseModel):
    status: SiteOrderStatus
    admin_notes: Optional[str] = None
    site_url: Optional[str] = None
    repository_url: Optional[str] = None


class SiteDeliverableResponse(BaseModel):
    id: int
    type: str
    title: str
    content: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


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
    deliverables: List[SiteDeliverableResponse] = []

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

@router.get("/public/{identifier}")
async def get_order_public(
    identifier: str,
    email: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get order by identifier (stripe_session_id or last 8 chars) - no auth required"""
    repo = OrderRepository(db)
    order = await repo.find_by_identifier(identifier)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # If email provided, verify it matches (basic security)
    if email and order.customer_email.lower() != email.lower():
        raise HTTPException(status_code=403, detail="Email does not match order")
    
    # Eager load relationships for the response
    # Note: Ideally this should be in the repository, but for now we rely on the session
    # caching or we update repository to support options.
    # For now, let's keep it simple as repository methods return objects.
    
    return order


@router.post("/{order_id}/onboarding")
async def submit_onboarding(
    order_id: str,
    onboarding_data: SiteOnboardingCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Cliente submete dados do onboarding"""
    # Use the service to handle everything
    from app.services.onboarding_service import OnboardingService
    service = OnboardingService(db, background_tasks)
    
    return await service.process_onboarding(order_id, onboarding_data)


@router.get("/{order_id}/onboarding")
async def get_onboarding(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Obtém dados do onboarding de um pedido"""
    repo = OrderRepository(db)
    onboarding = await repo.get_onboarding(order_id)
    
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
    repo = CatalogRepository(db)
    return await repo.list_addons(active_only)


@router.post("/addons")
async def create_addon(
    addon_data: SiteAddonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Cria um novo addon"""
    repo = CatalogRepository(db)
    addon = SiteAddon(**addon_data.model_dump())
    return await repo.create_addon(addon)


@router.patch("/addons/{addon_id}")
async def update_addon(
    addon_id: int,
    addon_data: SiteAddonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Atualiza um addon"""
    repo = CatalogRepository(db)
    addon = await repo.get_addon(addon_id)
    if not addon:
        raise HTTPException(status_code=404, detail="Addon not found")
    
    for key, value in addon_data.model_dump().items():
        setattr(addon, key, value)
    
    return await repo.update_addon(addon)


# ============== Template Endpoints ==============

@router.get("/templates/list")
async def list_templates(
    niche: Optional[SiteNiche] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Lista templates disponíveis"""
    repo = CatalogRepository(db)
    return await repo.list_templates(niche, active_only)


@router.post("/templates")
async def create_template(
    template_data: SiteTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Cria um novo template"""
    repo = CatalogRepository(db)
    template = SiteTemplate(**template_data.model_dump())
    return await repo.create_template(template)


@router.patch("/templates/{template_id}")
async def update_template(
    template_id: int,
    template_data: SiteTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Atualiza um template"""
    repo = CatalogRepository(db)
    template = await repo.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for key, value in template_data.model_dump().items():
        setattr(template, key, value)
    
    return await repo.update_template(template)

# ============== Restored Endpoints ==============

@router.post("/checkout")
async def create_checkout(
    order_data: SiteOrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create Stripe Checkout Session"""
    stripe_service = StripeService(db)
    
    # Success/Cancel URLs (should be configured or passed from frontend)
    from app.core.config import settings
    domain = settings.FRONTEND_URL
    # Redirect directly to onboarding using session_id
    success_url = f"{domain}/en/launch/onboarding?order_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{domain}/en/launch/cancel"
    
    print(f"DEBUG: Redirect Success URL: {success_url}")
    
    session = await stripe_service.create_checkout_session(
        order_data=order_data.model_dump(),
        success_url=success_url,
        cancel_url=cancel_url
    )
    
    return {"id": session.id, "url": session.url}

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Stripe Webhook Handler"""
    stripe_service = StripeService(db)
    payload = await request.body()
    
    try:
        print(f"DEBUG: Webhook received. Processing payload...")
        event = await stripe_service.construct_event(payload, stripe_signature)
    except Exception as e:
        print(f"DEBUG: Webhook Signature Verification Failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    print(f"DEBUG: Webhook verified. Event Type: {event['type']}")
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print(f"DEBUG: Processing checkout.session.completed: {session['id']}")
        
        # Here we would create the order securely
        customer_email = session.get("customer_details", {}).get("email")
        customer_name = session.get("customer_details", {}).get("name")
        total_price = session.get("amount_total", 0) / 100.0
        
        # Check if order already exists
        result = await db.execute(
            select(SiteOrder).where(SiteOrder.stripe_session_id == session["id"])
        )
        existing_order = result.scalar_one_or_none()
        
        if existing_order:
            print(f"DEBUG: Order already exists: {existing_order.id}, Status: {existing_order.status}")
            # Idempotency: Order already created
            if existing_order.status == SiteOrderStatus.PENDING_PAYMENT:
                existing_order.status = SiteOrderStatus.PAID
                existing_order.paid_at = datetime.utcnow()
                await db.commit()
                print(f"DEBUG: Order {existing_order.id} updated to PAID")
        else:
            print("DEBUG: Creating NEW order...")
            # Create new order
            order = SiteOrder(
                customer_name=customer_name or "Cliente Desconhecido",
                customer_email=customer_email or "",
                stripe_session_id=session["id"],
                stripe_customer_id=session.get("customer"),
                stripe_payment_intent_id=session.get("payment_intent"),
                total_price=total_price,
                status=SiteOrderStatus.PAID,
                paid_at=datetime.utcnow(),
                expected_delivery_date=datetime.utcnow() + timedelta(days=5)
            )
            
            db.add(order)
            await db.commit()
            await db.refresh(order)
            print(f"DEBUG: New Order Created! ID: {order.id}")
            
            # Send payment confirmation email
            try:
                print(f"DEBUG: Sending confirmation email for order {order.id}")
                await email_service.send_payment_confirmation(
                    order={
                        "id": order.id, 
                        "customer_name": order.customer_name, 
                        "customer_email": order.customer_email, 
                        "total_price": order.total_price
                    }
                )
                print("DEBUG: Email sent successfully")
            except Exception as e:
                print(f"DEBUG: Failed to send email: {e}")
            
            print(f"✅ Order Flow Complete! ID: {order.id}")
            
    return {"status": "success"}

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
        selectinload(SiteOrder.addons).selectinload(SiteOrderAddon.addon),
        selectinload(SiteOrder.deliverables)  # CRITICAL: Load deliverables for Creation Journey
    ).order_by(SiteOrder.created_at.desc())
    
    if status_filter:
        query = query.where(SiteOrder.status == status_filter)
    
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return orders

@router.post("/auto-start-stuck-orders")
async def auto_start_stuck_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Automatically start generation for orders that are BUILDING with completed onboarding
    but haven't started generation yet. This ensures the system is fully automatic.
    """
    from sqlalchemy.orm import selectinload
    from app.tasks.site_generation import generate_site_task
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Find orders that are BUILDING with completed onboarding but not generating
    result = await db.execute(
        select(SiteOrder)
        .options(selectinload(SiteOrder.onboarding))
        .where(SiteOrder.status == SiteOrderStatus.BUILDING)
        .where(SiteOrder.onboarding_completed_at.isnot(None))
    )
    stuck_orders = result.scalars().all()
    
    started = []
    errors = []
    
    for order in stuck_orders:
        if order.onboarding:  # Only if onboarding exists
            try:
                # Update status to GENERATING
                order.status = SiteOrderStatus.GENERATING
                order.admin_notes = f"Auto-started generation (was stuck in BUILDING). Original: {order.admin_notes or 'N/A'}"
                await db.commit()
                
                # Start generation
                celery_task = generate_site_task.delay(order.id, resume=True)
                started.append({
                    "order_id": order.id,
                    "task_id": celery_task.id,
                    "customer_email": order.customer_email
                })
                logger.info(f"✅ Auto-started generation for stuck order {order.id} (task: {celery_task.id})")
            except Exception as e:
                errors.append({
                    "order_id": order.id,
                    "error": str(e)
                })
                logger.error(f"❌ Failed to auto-start order {order.id}: {e}", exc_info=True)
                await db.rollback()
    
    return {
        "success": True,
        "started_count": len(started),
        "errors_count": len(errors),
        "started_orders": started,
        "errors": errors,
        "message": f"Auto-started generation for {len(started)} stuck orders"
    }

@router.get("/stats")
async def get_order_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Estatísticas de pedidos"""
    from app.core.database import AsyncSessionLocal
    
    # Use a separate session to avoid conflicts with ongoing operations
    async with AsyncSessionLocal() as stats_session:
        # Total por status
        status_counts = await stats_session.execute(
            select(SiteOrder.status, func.count(SiteOrder.id))
            .group_by(SiteOrder.status)
        )
        
        # Revenue total
        revenue = await stats_session.execute(
            select(func.sum(SiteOrder.total_price))
            .where(SiteOrder.status != SiteOrderStatus.CANCELLED)
        )
        
        # Pedidos este mês
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_orders = await stats_session.execute(
            select(func.count(SiteOrder.id))
            .where(SiteOrder.created_at >= month_start)
        )
        
        return {
            "status_counts": dict(status_counts.all()),
            "total_revenue": revenue.scalar() or 0,
            "orders_this_month": monthly_orders.scalar() or 0
        }

# IMPORTANTE: Rotas específicas DEVEM vir ANTES das rotas dinâmicas {order_id}
# Caso contrário, o FastAPI tentará interpretar strings como "check-empty-generations" como order_id

@router.get("/check-empty-generations")
async def check_empty_generations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Check orders in GENERATING status that have no generated files"""
    import os
    from app.services.site_generator_service import SiteGeneratorService
    
    # Get all orders in GENERATING status
    result = await db.execute(
        select(SiteOrder)
        .where(SiteOrder.status == SiteOrderStatus.GENERATING)
    )
    generating_orders = result.scalars().all()
    
    service = SiteGeneratorService(db)
    empty_orders = []
    valid_orders = []
    
    for order in generating_orders:
        target_dir = service._get_target_dir(order.id)
        stage_info = service._check_stage_files(target_dir)
        
        # Consider empty if no files or very few files (< 5)
        if stage_info["files_count"] < 5:
            empty_orders.append({
                "order_id": order.id,
                "customer_name": order.customer_name,
                "customer_email": order.customer_email,
                "status": order.status.value,
                "files_count": stage_info["files_count"],
                "current_stage": stage_info["current_stage"],
                "has_directory": os.path.exists(target_dir),
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "onboarding_completed_at": order.onboarding_completed_at.isoformat() if order.onboarding_completed_at else None
            })
        else:
            valid_orders.append({
                "order_id": order.id,
                "customer_name": order.customer_name,
                "files_count": stage_info["files_count"]
            })
    
    return {
        "total_generating": len(generating_orders),
        "empty_generations": len(empty_orders),
        "valid_generations": len(valid_orders),
        "empty_orders": empty_orders,
        "valid_orders": valid_orders
    }

@router.post("/reset-empty-generations")
async def reset_empty_generations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Reset all orders in GENERATING status that have no generated files and automatically start generation"""
    import os
    import shutil
    import threading
    import logging
    from app.services.site_generator_service import SiteGeneratorService
    
    logger = logging.getLogger(__name__)
    
    # Get all orders in GENERATING status with onboarding loaded
    result = await db.execute(
        select(SiteOrder)
        .options(selectinload(SiteOrder.onboarding))
        .where(SiteOrder.status == SiteOrderStatus.GENERATING)
    )
    generating_orders = result.scalars().all()
    
    reset_orders = []
    errors = []
    auto_started = []
    
    # Import Celery task
    from app.tasks.site_generation import generate_site_task
    
    for order in generating_orders:
        # Use static path calculation to avoid session conflicts
        target_dir = os.path.abspath(os.path.join(os.getcwd(), "generated_sites", f"project_{order.id}"))
        
        # Check stage files manually
        stage_info = {"current_stage": "none", "stages": {}, "files_count": 0}
        if os.path.exists(target_dir):
            files_count = 0
            for root, dirs, files in os.walk(target_dir):
                files_count += len(files)
            stage_info["files_count"] = files_count
            if files_count > 0:
                stage_info["current_stage"] = "phase_2"
        
        # Consider empty if no files or very few files (< 5)
        if stage_info["files_count"] < 5:
            try:
                # Remove directory if it exists
                if os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                
                # Reset status to BUILDING
                order.status = SiteOrderStatus.BUILDING
                order.admin_notes = f"Auto-reset: Generation had {stage_info['files_count']} files (too few). Auto-starting generation..."
                await db.commit()
                
                reset_orders.append({
                    "order_id": order.id,
                    "customer_name": order.customer_name,
                    "files_removed": stage_info["files_count"]
                })
                
                # Automatically start generation if onboarding is complete
                if order.onboarding:
                    celery_task = generate_site_task.delay(order.id, resume=True)
                    auto_started.append(order.id)
                    logger.info(f"Enqueued Celery task {celery_task.id} for order {order.id} after bulk reset")
                
            except Exception as e:
                errors.append({
                    "order_id": order.id,
                    "error": str(e)
                })
    
    return {
        "success": True,
        "reset_count": len(reset_orders),
        "errors_count": len(errors),
        "auto_started_count": len(auto_started),
        "reset_orders": reset_orders,
        "auto_started_orders": auto_started,
        "errors": errors,
        "message": f"Reset {len(reset_orders)} orders and automatically started generation for {len(auto_started)} orders"
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
            selectinload(SiteOrder.addons).selectinload(SiteOrderAddon.addon),
            selectinload(SiteOrder.deliverables)
        )
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order

@router.post("/{order_id}/build")
async def trigger_build(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Dispara a geração do site via IA"""
    ai_service = AIService(db)
    validation = await ai_service.validate_task("coding")
    if not validation.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation.get("detail", "Configuração de IA inválida.")
        )

    # Use selectinload to eager load onboarding and avoid MissingGreenlet
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(SiteOrder)
        .options(selectinload(SiteOrder.onboarding))
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if not order.onboarding:
        raise HTTPException(status_code=400, detail="Onboarding not completed")
    
    # Atualiza status para em geração
    order.status = SiteOrderStatus.GENERATING
    await db.commit()
    
    # Enqueue Celery task instead of threading
    from app.tasks.site_generation import generate_site_task
    import logging
    
    logger = logging.getLogger(__name__)
    
    celery_task = generate_site_task.delay(order_id, resume=True)
    logger.info(f"Enqueued Celery task {celery_task.id} for order {order_id}")
    
    return {
        "message": "Build started",
        "order_id": order_id,
        "task_id": celery_task.id,
        "status": "queued"
    }

@router.get("/{order_id}/logs")
async def get_order_logs(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna os logs de geração para um pedido"""
    repo = OrderRepository(db)
    
    # Verify order exists first
    order = await repo.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    return await repo.get_logs(order_id)

@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: int,
    status_update: SiteOrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Atualiza o status de um pedido"""
    result = await db.execute(
        select(SiteOrder)
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Update status
    order.status = status_update.status
    
    # Update optional fields if provided
    if status_update.admin_notes is not None:
        order.admin_notes = status_update.admin_notes
    if status_update.site_url is not None:
        order.site_url = status_update.site_url
    if status_update.repository_url is not None:
        order.repository_url = status_update.repository_url
    
    await db.commit()
    await db.refresh(order)
    
    return {
        "message": "Status updated successfully",
        "order_id": order.id,
        "status": order.status.value
    }

@router.post("/{order_id}/reset-generation")
async def reset_generation(
    order_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Reset generation for an order - clears files and automatically starts generation"""
    import os
    import shutil
    import threading
    import logging
    from app.services.site_generator_service import SiteGeneratorService
    
    logger = logging.getLogger(__name__)
    
    # Use selectinload to eager load onboarding and avoid MissingGreenlet
    result = await db.execute(
        select(SiteOrder)
        .options(selectinload(SiteOrder.onboarding))
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if not order.onboarding:
        raise HTTPException(status_code=400, detail="Onboarding not completed")
    
    # Get target directory (use absolute path consistent with volume mount)
    base_dir = os.getenv("SITES_BASE_DIR", "/app/generated_sites")
    target_dir = os.path.join(base_dir, f"project_{order_id}")
    
    # Check if directory exists and has files
    has_files = False
    files_count = 0
    if os.path.exists(target_dir):
        for root, dirs, files in os.walk(target_dir):
            files_count += len(files)
        has_files = files_count > 0
    
    # Remove directory if it exists
    if os.path.exists(target_dir):
        try:
            shutil.rmtree(target_dir)
            removed = True
        except Exception as e:
            removed = False
            error_msg = str(e)
    else:
        removed = True
        error_msg = None
    
    # Reset order status to BUILDING to allow retry
    order.status = SiteOrderStatus.BUILDING
    order.admin_notes = f"Generation reset. Previous attempt had {files_count} files. Auto-starting generation..."
    await db.commit()
    
    # Automatically trigger generation after reset using Celery
    from app.tasks.site_generation import generate_site_task
    
    celery_task = generate_site_task.delay(order_id, resume=True)
    logger.info(f"Enqueued Celery task {celery_task.id} for order {order_id} after reset")
    
    return {
        "success": True,
        "order_id": order_id,
        "had_files": has_files,
        "files_removed": files_count,
        "directory_removed": removed,
        "new_status": order.status.value,
        "error": error_msg,
        "auto_generation_started": True,
        "task_id": celery_task.id,
        "message": "Generation reset and automatically started"
    }
