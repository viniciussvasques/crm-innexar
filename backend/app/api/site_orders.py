"""
Site Orders API - Gerenciamento de pedidos de sites Launch
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Request, Header, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import logging
import stripe
import json

from app.core.database import get_db
from app.models.user import User
from app.models.site_order import (
    SiteOrder, SiteOrderStatus, SiteOnboarding, SiteAddon, 
    SiteOrderAddon, SiteTemplate, SiteNiche, SiteTone, SiteCTA
)
from app.models.site_deliverable import SiteDeliverable, DeliverableType, DeliverableStatus
from app.models.site_feedback import SiteFeedback
from app.models.site_order_message import SiteOrderMessage
from app.api.dependencies import get_current_user, require_admin
from app.api.site_customers import decode_customer_token, create_customer_account
from app.services.email_service import email_service
from app.services.site_generator_service import SiteGeneratorService
from app.services.ai_service import AIService
from app.services.stripe_service import StripeService
from app.repositories.order_repository import OrderRepository
from app.repositories.catalog_repository import CatalogRepository
from fastapi import Request


router = APIRouter(prefix="/site-orders", tags=["site-orders"])
logger = logging.getLogger(__name__)


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
    # Domain configuration
    has_existing_domain: Optional[bool] = False
    existing_domain: Optional[str] = None
    domain_to_purchase: Optional[str] = None
    # Legacy field - keep for backward compatibility
    desired_domain: Optional[str] = None
    
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
    # Locale of the customer's browser at onboarding time (e.g. 'en', 'pt', 'es')
    locale: Optional[str] = None


class SiteOrderStatusUpdate(BaseModel):
    status: SiteOrderStatus
    admin_notes: Optional[str] = None
    site_url: Optional[str] = None
    repository_url: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None


class SiteDeliverableResponse(BaseModel):
    id: int
    type: str
    title: str
    content: Optional[str]
    status: str
    created_at: datetime
    
    @classmethod
    def from_orm(cls, obj: SiteDeliverable):
        """Custom serializer to ensure enum values are converted to strings"""
        return cls(
            id=obj.id,
            type=obj.type.value if hasattr(obj.type, 'value') else str(obj.type),
            title=obj.title,
            content=obj.content,
            status=obj.status.value if hasattr(obj.status, 'value') else str(obj.status),
            created_at=obj.created_at
        )
    
    class Config:
        from_attributes = True
        # Use the custom serializer
        orm_mode = True


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


# ============== Public Endpoints (NO AUTH) ==============

@router.get("/public/{session_id}")
async def get_order_by_session_id(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint to get order by Stripe session ID.
    Used by the website to lookup order after payment.
    NO AUTHENTICATION REQUIRED - returns limited data only.
    
    Supports:
    - Full Stripe session ID (cs_test_xxx or cs_live_xxx)
    - Partial session ID (last 8 characters, case-insensitive)
    - Numeric database ID
    """
    logger.info(f"[Public API] Looking up order by session_id: {session_id}")
    
    order = None
    
    # Try 1: Exact match by full session_id
    result = await db.execute(
        select(SiteOrder).where(SiteOrder.stripe_session_id == session_id)
    )
    order = result.scalar_one_or_none()
    
    # Try 2: Search by partial session_id (last 8 characters, case-insensitive)
    if not order and len(session_id) <= 12:
        # It's likely a partial ID (the masked version)
        logger.info(f"[Public API] Trying partial match for: {session_id}")
        result = await db.execute(
            select(SiteOrder).where(
                func.upper(func.right(SiteOrder.stripe_session_id, len(session_id))) == session_id.upper()
            )
        )
        order = result.scalar_one_or_none()
    
    # Try 3: If it's a numeric ID, try direct lookup
    if not order and session_id.isdigit():
        logger.info(f"[Public API] Trying numeric ID lookup: {session_id}")
        result = await db.execute(
            select(SiteOrder).where(SiteOrder.id == int(session_id))
        )
        order = result.scalar_one_or_none()
    
    if not order:
        logger.warning(f"[Public API] Order not found for session_id: {session_id}")
        raise HTTPException(status_code=404, detail="Order not found")
    
    logger.info(f"[Public API] Found order ID: {order.id}, status: {order.status}")
    
    # Return limited public data only
    return {
        "id": order.id,
        "stripe_session_id": order.stripe_session_id,
        "customer_email": order.customer_email,
        "customer_name": order.customer_name,
        "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
        "total_price": order.total_price,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "onboarding_completed_at": order.onboarding_completed_at.isoformat() if order.onboarding_completed_at else None
    }

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
            
            # Notify all admins
            try:
                from app.api.notifications import notify_all_admins
                await notify_all_admins(
                    db,
                    title="Nova ordem de site",
                    message=f"Pedido #{order.id} - {order.customer_name} - ${order.total_price}",
                    notification_type="info",
                    related_entity_type="site_order",
                    related_entity_id=order.id
                )
            except Exception as e:
                print(f"DEBUG: Failed to notify admins: {e}")
            
            # Create hosting subscription with free trial
            try:
                from app.api.system_config import get_config_value
                hosting_price_id = await get_config_value(db, "stripe_hosting_price_id")
                trial_days = await get_config_value(db, "hosting_trial_days")
                
                if hosting_price_id and order.stripe_customer_id:
                    trial_days_int = int(trial_days) if trial_days else 90
                    print(f"DEBUG: Creating hosting subscription for order {order.id} with {trial_days_int} day trial")
                    subscription = await stripe_service.create_hosting_subscription(
                        customer_id=order.stripe_customer_id,
                        order_id=order.id,
                        price_id=hosting_price_id,
                        trial_days=trial_days_int
                    )
                    print(f"DEBUG: Hosting subscription created: {subscription.id}")
                else:
                    print(f"DEBUG: Skipping hosting subscription - price_id: {hosting_price_id}, customer_id: {order.stripe_customer_id}")
            except Exception as e:
                print(f"DEBUG: Error creating hosting subscription for order {order.id}: {e}")
                # Don't fail the webhook if subscription creation fails
            
            # Send payment confirmation email
            try:
                print(f"DEBUG: Sending confirmation email for order {order.id}")
                # Get locale from metadata or default to 'en'
                locale = "en"  # Default, can be extracted from Stripe metadata if needed
                await email_service.send_payment_confirmation(
                    order={
                        "id": order.id, 
                        "customer_name": order.customer_name, 
                        "customer_email": order.customer_email, 
                        "total_price": order.total_price,
                        "stripe_session_id": order.stripe_session_id,
                        "locale": locale
                    }
                )
                print("DEBUG: Email sent successfully")
            except Exception as e:
                print(f"DEBUG: Failed to send email: {e}")
            
            print(f"✅ Order Flow Complete! ID: {order.id}")
            
    return {"status": "success"}

def serialize_deliverable(d: SiteDeliverable) -> dict:
    """Helper to serialize deliverable with enum values converted to strings"""
    return {
        "id": d.id,
        "type": d.type.value if hasattr(d.type, 'value') else str(d.type),
        "title": d.title,
        "content": d.content,
        "status": d.status.value if hasattr(d.status, 'value') else str(d.status),
        "created_at": d.created_at.isoformat() if d.created_at else None
    }

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
    
    # Serialize orders with deliverables properly
    serialized_orders = []
    for order in orders:
        order_dict = {
            **{k: v for k, v in order.__dict__.items() if not k.startswith('_')},
            'deliverables': [serialize_deliverable(d) for d in (order.deliverables or [])]
        }
        serialized_orders.append(order_dict)
    
    return serialized_orders

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
    
    # Serialize deliverables properly
    order_dict = {
        **{k: v for k, v in order.__dict__.items() if not k.startswith('_')},
        'deliverables': [serialize_deliverable(d) for d in (order.deliverables or [])]
    }
    
    return order_dict

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
    
    # Update status (even when keeping the same value we persist other fields)
    order.status = status_update.status
    
    # Update optional fields if provided
    if status_update.admin_notes is not None:
        order.admin_notes = status_update.admin_notes
    if status_update.site_url is not None:
        order.site_url = status_update.site_url
    if status_update.repository_url is not None:
        order.repository_url = status_update.repository_url
    if status_update.expected_delivery_date is not None:
        order.expected_delivery_date = status_update.expected_delivery_date
    
    await db.commit()
    await db.refresh(order)
    
    # === NOTIFICAÇÕES AUTOMÁTICAS DE STATUS ===
    try:
        from app.services.email_service import EmailService
        email_service = EmailService()
        
        order_data = {
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "id": order.id,
            "locale": order.onboarding.locale if order.onboarding else "pt"
        }
        
        if status_update.status == SiteOrderStatus.BUILDING:
            email_service.send_site_in_progress(order_data)
            logger.info(f"[EMAIL] Sent 'in progress' email for order {order.id}")
        elif status_update.status == SiteOrderStatus.PREVIEW:
            preview_url = order.site_url or f"https://innexar.app/portal/{order.id}"
            email_service.send_ready_for_review(order_data, preview_url)
            logger.info(f"[EMAIL] Sent 'ready for review' email for order {order.id}")
        elif status_update.status == SiteOrderStatus.DELIVERED:
            site_url = order.site_url or ""
            email_service.send_site_delivered(order_data, site_url)
            logger.info(f"[EMAIL] Sent 'delivered' email for order {order.id}")
    except Exception as e:
        logger.error(f"[EMAIL] Failed to send status notification: {e}")
    
    return {
        "message": "Status updated successfully",
        "order_id": order.id,
        "status": order.status.value
    }

@router.post("/{order_id}/deliverables/briefing", response_model=SiteDeliverableResponse)
async def generate_briefing_deliverable(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Gera um documento de briefing consolidado a partir do onboarding
    e salva como SiteDeliverable (uso interno da equipe).
    """
    result = await db.execute(
        select(SiteOrder)
        .options(selectinload(SiteOrder.onboarding))
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order.onboarding:
        raise HTTPException(status_code=400, detail="Onboarding not completed for this order")

    ob = order.onboarding

    lines: List[str] = []
    lines.append(f"# Strategic Briefing - {ob.business_name}")
    lines.append("")
    lines.append("## 1. Business Overview")
    lines.append(f"- Business name: **{ob.business_name}**")
    lines.append(f"- Segment / niche: **{ob.niche}**")
    lines.append(f"- Location: **{ob.primary_city}, {ob.state}**")
    lines.append(f"- Primary service: **{ob.primary_service}**")
    lines.append(f"- Contact email: {ob.business_email}")
    lines.append(f"- Phone / WhatsApp: {ob.business_phone} ({'has WhatsApp' if ob.has_whatsapp else 'no WhatsApp'})")
    lines.append("")

    lines.append("## 2. Services & Offer")
    if ob.services:
        lines.append("**Services offered:**")
        for s in ob.services:
            lines.append(f"- {s}")
    if ob.service_descriptions:
        lines.append("")
        lines.append("**Service details:**")
        for name, desc in (ob.service_descriptions or {}).items():
            lines.append(f"- **{name}** – {desc}")
    lines.append("")

    lines.append("## 3. Site Objective & Pages")
    if ob.site_objective:
        lines.append(f"- **Primary objective:** {ob.site_objective}")
    if ob.site_description:
        lines.append("")
        lines.append("**Business / about copy (raw):**")
        lines.append("")
        lines.append(ob.site_description)
    if ob.selected_pages:
        lines.append("")
        lines.append("**Pages included:**")
        for p in ob.selected_pages:
            lines.append(f"- {p}")
    lines.append("")

    lines.append("## 4. Brand & Positioning")
    if ob.tone:
        lines.append(f"- **Tone of voice:** {ob.tone}")
    if ob.primary_cta:
        lines.append(f"- **Primary CTA:** {ob.primary_cta}")
    if ob.cta_text:
        lines.append(f"- **CTA text suggestion:** “{ob.cta_text}”")
    if ob.primary_color or ob.secondary_color or ob.accent_color:
        lines.append("")
        lines.append("**Brand colors:**")
        if ob.primary_color:
            lines.append(f"- Primary: {ob.primary_color}")
        if ob.secondary_color:
            lines.append(f"- Secondary: {ob.secondary_color}")
        if ob.accent_color:
            lines.append(f"- Accent: {ob.accent_color}")
    if ob.reference_sites:
        lines.append("")
        lines.append("**Reference sites:**")
        for url in ob.reference_sites:
            lines.append(f"- {url}")
    if ob.design_notes:
        lines.append("")
        lines.append("**Design notes:**")
        lines.append(ob.design_notes)
    lines.append("")

    lines.append("## 5. Social Proof & Authority")
    if ob.google_reviews_link:
        lines.append(f"- Google reviews: {ob.google_reviews_link}")
    if ob.testimonials:
        lines.append("")
        lines.append("**Testimonials provided:**")
        for t in ob.testimonials:
            name = t.get("name") or "Client"
            role = t.get("role") or ""
            text = t.get("text") or ""
            suffix = f" ({role})" if role else ""
            lines.append(f"- “{text}” — {name}{suffix}")
    if ob.about_owner:
        lines.append("")
        lines.append("**Story / About the owner:**")
        lines.append(ob.about_owner)

    content = "\n".join(lines)

    deliverable = SiteDeliverable(
        order_id=order.id,
        type=DeliverableType.BRIEFING,
        title=f"Strategic Briefing - {ob.business_name}",
        content=content,
        status=DeliverableStatus.READY,
        is_visible_to_client=True,  # Changed: Show briefing to client in portal
    )

    db.add(deliverable)
    await db.commit()
    await db.refresh(deliverable)

    return deliverable


@router.post("/{order_id}/ai/plan-sitemap", response_model=SiteDeliverableResponse)
async def generate_sitemap_ai(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Usa IA para propor um sitemap/arquitetura do site a partir do briefing.
    Salva como SiteDeliverable(type=SITEMAP, status=READY).
    """
    result = await db.execute(
        select(SiteOrder)
        .options(selectinload(SiteOrder.onboarding))
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order.onboarding:
        raise HTTPException(status_code=400, detail="Onboarding not completed for this order")

    ob = order.onboarding

    ai_service = AIService(db)

    system_instruction = (
        "You are a senior website information architect and UX strategist specializing in small business websites. "
        "Your task is to create a comprehensive, detailed sitemap proposal that maximizes conversions, builds trust, "
        "and guides visitors through a clear user journey. Be thorough, specific, and strategic. "
        "Respond in well-structured Markdown with clear headings, detailed sections, and actionable recommendations."
    )

    pages = ", ".join(ob.selected_pages or []) if ob.selected_pages else "home, about, services, contact"
    services = ", ".join(ob.services or [])
    
    # Build service descriptions string
    service_descriptions_str = ""
    if ob.service_descriptions:
        service_descriptions_lines = [f"- {k}: {v}" for k, v in (ob.service_descriptions or {}).items()]
        service_descriptions_str = "\n".join(service_descriptions_lines)
    
    # Build reference sites string
    reference_sites_str = ""
    if ob.reference_sites:
        reference_sites_lines = [f"- {ref}" for ref in (ob.reference_sites or [])]
        reference_sites_str = "\n".join(reference_sites_lines)
    
    # Build social media string
    social_media_lines = []
    if ob.social_facebook:
        social_media_lines.append(f"- Facebook: {ob.social_facebook}")
    if ob.social_instagram:
        social_media_lines.append(f"- Instagram: {ob.social_instagram}")
    if ob.social_linkedin:
        social_media_lines.append(f"- LinkedIn: {ob.social_linkedin}")
    if ob.social_youtube:
        social_media_lines.append(f"- YouTube: {ob.social_youtube}")
    social_media_str = "\n".join(social_media_lines) if social_media_lines else ""

    # Build prompt parts
    prompt_parts = [
        "# Business Context",
        "",
        f"**Business Name:** {ob.business_name}",
        f"**Industry/Niche:** {ob.niche}{f' ({ob.custom_niche})' if ob.custom_niche else ''}",
        f"**Location:** {ob.primary_city}, {ob.state}",
    ]
    
    if ob.service_areas:
        prompt_parts.append(f"**Service Areas:** {', '.join(ob.service_areas)}")
    
    prompt_parts.extend([
        "",
        f"**Primary Service:** {ob.primary_service}",
        f"**All Services:** {services}",
    ])
    
    if service_descriptions_str:
        prompt_parts.append("**Service Descriptions:**")
        prompt_parts.append(service_descriptions_str)
    
    prompt_parts.extend([
        "",
        f"**Site Objective:** {ob.site_objective or 'Generate leads and build trust'}",
        f"**Target Tone:** {ob.tone}",
        f"**Primary CTA Strategy:** {ob.primary_cta}",
    ])
    
    if ob.cta_text:
        prompt_parts.append(f"**Custom CTA Text:** {ob.cta_text}")
    
    prompt_parts.extend([
        "",
        f"**Selected Pages:** {pages}",
        f"**Total Pages Included:** {ob.total_pages or 5}",
        "",
    ])
    
    if reference_sites_str:
        prompt_parts.append("**Reference Websites (for inspiration):**")
        prompt_parts.append(reference_sites_str)
        prompt_parts.append("")
    
    if ob.site_description:
        prompt_parts.append(f"**Business Description:** {ob.site_description}")
    if ob.about_owner:
        prompt_parts.append(f"**About the Owner:** {ob.about_owner}")
    if ob.years_in_business:
        prompt_parts.append(f"**Years in Business:** {ob.years_in_business}")
    if ob.business_hours:
        prompt_parts.append(f"**Business Hours:** {ob.business_hours}")
    
    if social_media_str:
        prompt_parts.append("")
        prompt_parts.append("**Social Media:**")
        prompt_parts.append(social_media_str)
    
    if ob.google_reviews_link:
        prompt_parts.append("")
        prompt_parts.append(f"**Google Reviews Link:** {ob.google_reviews_link}")
    if ob.testimonials:
        prompt_parts.append(f"**Testimonials Available:** {len(ob.testimonials)} testimonials")
    
    prompt_parts.extend([
        "",
        "# Task",
        "",
        "Create a comprehensive, detailed sitemap proposal that includes:",
        "",
        "1. **Complete Page List** - All pages that should be included, with clear rationale for each",
        "2. **Detailed Page Structure** - For EACH page, provide:",
        "   - Page purpose and goals",
        "   - Complete list of sections/blocks (be specific: Hero, Features, Benefits, Testimonials, FAQ, etc.)",
        "   - Content recommendations for each section",
        "   - CTA placement strategy",
        "   - SEO considerations",
        "3. **Navigation Strategy** - How pages should be organized in menus (primary, footer, etc.)",
        "4. **User Journey Flow** - How visitors should move through the site",
        "5. **Conversion Optimization** - Where and how to place CTAs, forms, and trust elements",
        "6. **Mobile Considerations** - How the structure adapts for mobile users",
        "7. **Trust Building Elements** - Where to place testimonials, reviews, certifications, etc.",
        "",
        "Be extremely detailed and specific. Think like a professional web strategist creating a blueprint for a high-converting website.",
    ])
    
    prompt = "\n".join(prompt_parts)

    ai_info = None
    try:
        # Prefer dedicated task type, but gracefully fall back to creative_writing
        try:
            ai_result = await ai_service.generate(
                task_type="site_sitemap",
                prompt=prompt,
                system_instruction=system_instruction,
            )
        except Exception as e_primary:
            logger.error("AI sitemap (site_sitemap) failed, falling back to creative_writing: %r", e_primary)
            ai_result = await ai_service.generate(
                task_type="creative_writing",
                prompt=prompt,
                system_instruction=system_instruction,
            )
        content = ai_result.get("content") or ai_result.get("text") or json.dumps(ai_result, ensure_ascii=False)
        # Capture AI info if available
        ai_info = ai_result.get("ai_info")
    except Exception as e:
        # Se IA falhar totalmente, gera um sitemap detalhado a partir do onboarding
        logger.error("AI sitemap generation failed completely, using fallback template: %r", e)
        lines: List[str] = []
        lines.append(f"# Sitemap Proposal - {ob.business_name}")
        lines.append("")
        lines.append("## Page Structure")
        lines.append("")
        for page in ob.selected_pages or ["home", "about", "services", "contact"]:
            page_title = page.title()
            lines.append(f"### {page_title} Page")
            if page == "home":
                lines.append("- **Hero Section:** Main headline, value proposition, primary CTA")
                lines.append("- **Services Overview:** Grid/list of {len(ob.services or [])} key services with brief descriptions")
                lines.append("- **About Preview:** Short introduction to the business with link to full About page")
                lines.append("- **Social Proof:** Testimonials, reviews, or trust indicators")
                lines.append("- **Benefits Section:** Why choose this business (3-5 key points)")
                lines.append("- **Final CTA:** Secondary call-to-action with contact options")
            elif page == "about":
                lines.append("- **Hero/Header:** Business name and tagline")
                lines.append("- **Our Story:** Business history and mission")
                lines.append("- **Owner/Team:** Personal introduction and credentials")
                lines.append("- **Why Choose Us:** Unique selling points and differentiators")
                lines.append("- **CTA Section:** Contact or consultation request")
            elif page == "services":
                lines.append("- **Page Header:** Services overview introduction")
                for service in ob.services or []:
                    lines.append(f"- **{service}:** Detailed description, benefits, and pricing (if applicable)")
                lines.append("- **Process Section:** How the business works with clients")
                lines.append("- **CTA:** Request quote or consultation")
            elif page == "contact":
                lines.append("- **Contact Form:** Name, email, phone, message fields")
                lines.append("- **Contact Information:** Phone, email, address")
                lines.append("- **Business Hours:** Operating hours and availability")
                if ob.has_whatsapp:
                    lines.append("- **WhatsApp Button:** Direct messaging option")
                if ob.service_areas:
                    lines.append(f"- **Service Areas:** {', '.join(ob.service_areas)}")
                lines.append("- **Map:** Location map or service area visualization")
            lines.append("")
        
        lines.append("## Navigation Strategy")
        lines.append("- **Primary Menu:** Home, About, Services, Contact")
        lines.append("- **Footer Menu:** Additional links (Privacy Policy, Terms, etc.)")
        lines.append("")
        lines.append("## Conversion Elements")
        lines.append("- Primary CTA in hero section")
        lines.append("- Secondary CTAs throughout content sections")
        lines.append("- Contact form on Contact page")
        lines.append("- Phone/WhatsApp buttons in header and footer")
        content = "\n".join(lines)
        ai_info = {"provider": "fallback", "model": "template", "used_fallback": True}

    metadata = {}
    if ai_info:
        metadata["ai_provider"] = ai_info.get("provider", "unknown")
        metadata["ai_model"] = ai_info.get("model", "unknown")
        metadata["ai_config_name"] = ai_info.get("config_name", "")
        metadata["ai_used_fallback"] = ai_info.get("used_fallback", False)
    metadata["generated_at"] = datetime.utcnow().isoformat()

    deliverable = SiteDeliverable(
        order_id=order.id,
        type=DeliverableType.SITEMAP,
        title=f"Sitemap Proposal - {ob.business_name}",
        content=content,
        status=DeliverableStatus.READY,
        metadata_json=metadata,
        # Sitemap é seguro para o cliente visualizar por padrão
        is_visible_to_client=True,
    )

    db.add(deliverable)
    await db.commit()
    await db.refresh(deliverable)

    return deliverable


@router.post("/{order_id}/ai/home-copy", response_model=SiteDeliverableResponse)
async def generate_home_copy_ai(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Usa IA para gerar um rascunho de copy da página Home a partir do briefing.
    Salva como SiteDeliverable(type=CONTENT_PLAN, status=READY, metadata_json.page='home').
    """
    result = await db.execute(
        select(SiteOrder)
        .options(selectinload(SiteOrder.onboarding))
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order.onboarding:
        raise HTTPException(status_code=400, detail="Onboarding not completed for this order")

    ob = order.onboarding

    ai_service = AIService(db)

    system_instruction = (
        "You are a senior web copywriter and conversion specialist specializing in small business websites. "
        "Your task is to write compelling, conversion-optimized copy for the HOME page that builds trust, "
        "clearly communicates value, and drives action. Write in a professional yet approachable tone. "
        "Be specific, detailed, and persuasive. Use Markdown formatting with clear headings, subheadings, "
        "bullet points, and emphasis. Do NOT include HTML tags. Write complete, ready-to-use copy."
    )

    services = ", ".join(ob.services or [])
    
    # Build service descriptions string
    service_descriptions_str = ""
    if ob.service_descriptions:
        service_descriptions_lines = [f"- **{k}:** {v}" for k, v in (ob.service_descriptions or {}).items()]
        service_descriptions_str = "\n".join(service_descriptions_lines)
    
    # Build testimonials string
    testimonials_str = ""
    testimonials_count = len(ob.testimonials or [])
    if ob.testimonials:
        testimonials_lines = [f"- {t}" for t in (ob.testimonials or [])]
        testimonials_str = "\n".join(testimonials_lines)
    
    # Build social media string
    social_media_lines = []
    if ob.social_facebook:
        social_media_lines.append(f"- Facebook: {ob.social_facebook}")
    if ob.social_instagram:
        social_media_lines.append(f"- Instagram: {ob.social_instagram}")
    if ob.social_linkedin:
        social_media_lines.append(f"- LinkedIn: {ob.social_linkedin}")
    if ob.social_youtube:
        social_media_lines.append(f"- YouTube: {ob.social_youtube}")
    social_media_str = "\n".join(social_media_lines) if social_media_lines else ""

    # Build prompt parts
    prompt_parts = [
        "# Business Information",
        "",
        f"**Business Name:** {ob.business_name}",
        f"**Industry/Niche:** {ob.niche}{f' ({ob.custom_niche})' if ob.custom_niche else ''}",
        f"**Location:** {ob.primary_city}, {ob.state}",
    ]
    
    if ob.service_areas:
        prompt_parts.append(f"**Service Areas:** {', '.join(ob.service_areas)}")
    
    prompt_parts.extend([
        "",
        f"**Primary Service:** {ob.primary_service}",
        f"**All Services:** {services}",
    ])
    
    if service_descriptions_str:
        prompt_parts.append("**Service Descriptions:**")
        prompt_parts.append(service_descriptions_str)
    
    prompt_parts.extend([
        "",
        f"**Site Objective:** {ob.site_objective or 'Generate leads and build trust'}",
        f"**Target Tone:** {ob.tone}",
        f"**Primary CTA Strategy:** {ob.primary_cta}",
        f"**Custom CTA Text:** {ob.cta_text or 'Contact us today'}",
        "",
        f"**Business Description:** {ob.site_description or 'Professional service provider'}",
        f"**About the Owner:** {ob.about_owner or 'N/A'}",
    ])
    
    if ob.years_in_business:
        prompt_parts.append(f"**Years in Business:** {ob.years_in_business}")
    if ob.business_hours:
        prompt_parts.append(f"**Business Hours:** {ob.business_hours}")
    
    prompt_parts.append("")
    
    if testimonials_str:
        prompt_parts.append(f"**Testimonials ({testimonials_count}):**")
        prompt_parts.append(testimonials_str)
    else:
        prompt_parts.append("**Testimonials:** Available but not provided")
    
    if ob.google_reviews_link:
        prompt_parts.append(f"**Google Reviews:** {ob.google_reviews_link}")
    
    if social_media_str:
        prompt_parts.append("")
        prompt_parts.append("**Social Media:**")
        prompt_parts.append(social_media_str)
    
    prompt_parts.extend([
        "",
        "**Design Preferences:**",
    ])
    
    if ob.primary_color:
        prompt_parts.append(f"- Primary Color: {ob.primary_color}")
    if ob.secondary_color:
        prompt_parts.append(f"- Secondary Color: {ob.secondary_color}")
    if ob.accent_color:
        prompt_parts.append(f"- Accent Color: {ob.accent_color}")
    
    prompt_parts.extend([
        "",
        "# Task",
        "",
        "Write a complete, professional HOME page copy that includes:",
        "",
        "1. **Hero Section** - Compelling headline, subheadline, value proposition, and primary CTA",
        "2. **Services Section** - Detailed description of each service with benefits and value propositions",
        "3. **About Preview** - Engaging introduction to the business that builds trust",
        "4. **Social Proof** - Testimonials, reviews, or trust indicators (use provided testimonials if available)",
        "5. **Benefits/Why Choose Us** - Clear reasons why customers should choose this business",
        "6. **Call to Action** - Multiple strategic CTAs throughout the page",
        "7. **Contact Information** - Clear ways to get in touch",
        "",
        f"Write in a {ob.tone} tone. Be specific, detailed, and conversion-focused. Include actual copy, not just placeholders.",
        "Make it feel professional, trustworthy, and compelling. Use the business name, location, and specific details throughout.",
    ])
    
    prompt = "\n".join(prompt_parts)

    ai_info = None
    try:
        # Try dedicated task type
        ai_result = await ai_service.generate(
            task_type="site_home_copy",
            prompt=prompt,
            system_instruction=system_instruction,
        )
        content = ai_result.get("content") or ai_result.get("text") or json.dumps(ai_result, ensure_ascii=False)
        # Capture AI info if available
        ai_info = ai_result.get("ai_info")
    except Exception as e:
        # Se IA falhar totalmente, gera uma copy detalhada de Home a partir do briefing
        logger.error("AI home copy generation failed completely, using fallback template: %r", e)
        lines: List[str] = []
        lines.append(f"# Home Page Copy - {ob.business_name}")
        lines.append("")
        lines.append("## Hero Section")
        lines.append("")
        lines.append(f"### Headline")
        lines.append(f"Welcome to {ob.business_name}")
        lines.append("")
        lines.append(f"### Subheadline")
        lines.append(f"{ob.site_description or f'Professional {ob.primary_service or ob.niche.value} services in {ob.primary_city}, {ob.state}'}")
        lines.append("")
        lines.append(f"### Value Proposition")
        if ob.site_objective:
            lines.append(f"We help you {ob.site_objective}. Experience the difference of working with a dedicated professional.")
        else:
            lines.append(f"Quality {ob.primary_service or 'services'} delivered with expertise and care.")
        lines.append("")
        lines.append(f"### Primary CTA")
        lines.append(f"{ob.cta_text or 'Get Started Today'}")
        lines.append("")
        lines.append("## Services Section")
        lines.append("")
        lines.append("### Our Services")
        for s in ob.services or []:
            lines.append(f"#### {s}")
            if ob.service_descriptions and s in ob.service_descriptions:
                lines.append(ob.service_descriptions[s])
            else:
                lines.append(f"Professional {s.lower()} services tailored to your needs.")
            lines.append("")
        lines.append("## About Preview")
        lines.append("")
        if ob.about_owner:
            lines.append(ob.about_owner)
        elif ob.site_description:
            lines.append(ob.site_description)
        else:
            lines.append(f"{ob.business_name} is a trusted provider of {ob.primary_service or 'professional services'} in {ob.primary_city}, {ob.state}.")
            if ob.years_in_business:
                lines.append(f"With {ob.years_in_business} years of experience, we've built a reputation for excellence and reliability.")
        lines.append("")
        lines.append("[Learn More About Us →]")
        lines.append("")
        lines.append("## Why Choose Us")
        lines.append("")
        lines.append("- **Expertise:** Professional knowledge and experience")
        lines.append("- **Reliability:** Consistent, quality service")
        lines.append("- **Local Focus:** Serving {ob.primary_city} and surrounding areas")
        if ob.years_in_business:
            lines.append(f"- **Experience:** {ob.years_in_business} years in business")
        lines.append("")
        lines.append("## Social Proof")
        lines.append("")
        if ob.testimonials:
            lines.append("### What Our Clients Say")
            for i, testimonial in enumerate((ob.testimonials or [])[:3], 1):
                lines.append(f'"{testimonial}"')
                lines.append("")
        elif ob.google_reviews_link:
            lines.append(f"### Google Reviews")
            lines.append(f"See what our clients are saying: [View Reviews]({ob.google_reviews_link})")
            lines.append("")
        else:
            lines.append("### Trusted by Local Businesses")
            lines.append("We're proud to serve clients throughout {ob.primary_city} and {ob.state}.")
            lines.append("")
        lines.append("## Final Call to Action")
        lines.append("")
        lines.append("### Ready to Get Started?")
        lines.append(f"Contact {ob.business_name} today to discuss your needs and learn how we can help.")
        lines.append("")
        lines.append(f"**{ob.cta_text or 'Contact Us Now'}**")
        if ob.business_phone:
            lines.append(f"Call: {ob.business_phone}")
        if ob.business_email:
            lines.append(f"Email: {ob.business_email}")
        content = "\n".join(lines)
        ai_info = {"provider": "fallback", "model": "template", "used_fallback": True}

    metadata = {"page": "home"}
    if ai_info:
        metadata["ai_provider"] = ai_info.get("provider", "unknown")
        metadata["ai_model"] = ai_info.get("model", "unknown")
        metadata["ai_config_name"] = ai_info.get("config_name", "")
        metadata["ai_used_fallback"] = ai_info.get("used_fallback", False)
    metadata["generated_at"] = datetime.utcnow().isoformat()

    deliverable = SiteDeliverable(
        order_id=order.id,
        type=DeliverableType.CONTENT_PLAN,
        title=f"Home Page Copy Draft - {ob.business_name}",
        content=content,
        status=DeliverableStatus.READY,
        metadata_json=metadata,
        # Rascunho de Home pode ser compartilhado com o cliente
        is_visible_to_client=True,
    )

    db.add(deliverable)
    await db.commit()
    await db.refresh(deliverable)

    return deliverable


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

# ============== Manual Workflow Endpoints ==============

class PreviewUrlUpdate(BaseModel):
    preview_url: str

class FeedbackRequest(BaseModel):
    message: str
    attachments: Optional[List[str]] = None

class ApproveRequest(BaseModel):
    notes: Optional[str] = None

@router.patch("/{order_id}/preview-url")
async def update_preview_url(
    order_id: int,
    preview_data: PreviewUrlUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Define URL de preview e muda status para PREVIEW"""
    result = await db.execute(
        select(SiteOrder)
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Update preview URL and status
    order.preview_url = preview_data.preview_url
    if order.status == SiteOrderStatus.BUILDING:
        order.status = SiteOrderStatus.PREVIEW
    
    await db.commit()
    await db.refresh(order)
    
    # Send email to customer
    try:
        if order.onboarding:
            email_service.send_ready_for_review(
                {
                    "customer_name": order.customer_name,
                    "customer_email": order.customer_email,
                    "business_name": order.onboarding.business_name,
                    "order_id": order.id,
                    "revisions_included": order.revisions_included,
                    "revisions_used": order.revisions_used,
                    "onboarding": {"business_name": order.onboarding.business_name}
                },
                preview_data.preview_url
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send preview email: {e}")
    
    return {
        "message": "Preview URL updated successfully",
        "order_id": order.id,
        "preview_url": order.preview_url,
        "status": order.status.value
    }

@router.post("/{order_id}/feedback")
async def submit_feedback(
    order_id: int,
    feedback_data: FeedbackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Cliente ou admin envia feedback/revisão"""
    # Try to get auth token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token required")
    
    token = auth_header.replace("Bearer ", "")
    role = "client"  # Default to client
    
    # Check if it's an admin token
    try:
        from app.api.dependencies import decode_token
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            # It's an admin token - get user
            from app.api.dependencies import get_current_user
            try:
                current_user = await get_current_user(request, token)
                if current_user and current_user.role == "admin":
                    role = "admin"
            except:
                pass  # Not an admin, try customer token
    except:
        pass  # Not an admin token, try customer token
    
    # If not admin, verify customer token
    if role == "client":
        try:
            payload = decode_customer_token(token)
            # Token is valid customer token
        except:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.execute(
        select(SiteOrder)
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Calculate revision number
    existing_feedbacks = await db.execute(
        select(SiteFeedback)
        .where(SiteFeedback.order_id == order_id)
        .where(SiteFeedback.role == "client")
    )
    revision_count = len(existing_feedbacks.scalars().all())
    revision_number = revision_count + 1 if role == "client" else None
    
    # Create feedback
    feedback = SiteFeedback(
        order_id=order_id,
        message=feedback_data.message,
        attachments=feedback_data.attachments or [],
        role=role,
        revision_number=revision_number
    )
    db.add(feedback)
    
    # Update order status if client is requesting revision
    if role == "client" and order.status == SiteOrderStatus.PREVIEW:
        order.status = SiteOrderStatus.REVIEW
        order.revisions_used = min(order.revisions_used + 1, order.revisions_included)
    
    await db.commit()
    await db.refresh(feedback)
    
    return {
        "message": "Feedback submitted successfully",
        "feedback_id": feedback.id,
        "revision_number": revision_number,
        "order_status": order.status.value
    }

@router.post("/{order_id}/approve")
async def approve_site(
    order_id: int,
    approve_data: ApproveRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Cliente aprova o site"""
    # Verify customer token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token required")
    
    token = auth_header.replace("Bearer ", "")
    try:
        payload = decode_customer_token(token)
        customer_id = int(payload["sub"])
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.execute(
        select(SiteOrder)
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Verify customer owns this order
    from app.models.site_customer import SiteCustomer
    customer = await db.get(SiteCustomer, customer_id)
    if not customer or customer.order_id != order_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if order.status != SiteOrderStatus.PREVIEW:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot approve order in status {order.status.value}. Must be in PREVIEW."
        )
    
    # Update status to delivered
    order.status = SiteOrderStatus.DELIVERED
    order.delivered_at = datetime.utcnow()
    if approve_data.notes:
        order.admin_notes = approve_data.notes
    
    await db.commit()
    await db.refresh(order)
    
    # Send delivery email
    try:
        if order.onboarding:
            # Get locale from customer if available
            locale = "en"
            if order.customer and hasattr(order.customer, 'preferred_locale') and order.customer.preferred_locale:
                locale = order.customer.preferred_locale
            
            email_service.send_site_delivered(
                {
                    "customer_name": order.customer_name,
                    "customer_email": order.customer_email,
                    "business_name": order.onboarding.business_name,
                    "order_id": order.id,
                    "onboarding": {"business_name": order.onboarding.business_name},
                    "locale": locale
                },
                order.site_url or order.preview_url or ""
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send delivery email: {e}")
    
    return {
        "message": "Site approved and delivered",
        "order_id": order.id,
        "status": order.status.value,
        "delivered_at": order.delivered_at
    }

@router.get("/{order_id}/feedbacks")
async def get_feedbacks(
    order_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Lista todos os feedbacks de um pedido"""
    result = await db.execute(
        select(SiteFeedback)
        .where(SiteFeedback.order_id == order_id)
        .order_by(SiteFeedback.created_at.desc())
    )
    feedbacks = result.scalars().all()
    
    return {
        "order_id": order_id,
        "feedbacks": [
            {
                "id": f.id,
                "message": f.message,
                "attachments": f.attachments or [],
                "role": f.role,
                "revision_number": f.revision_number,
                "created_at": f.created_at.isoformat()
            }
            for f in feedbacks
        ]
    }

@router.get("/{order_id}/timeline")
async def get_timeline(
    order_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Retorna timeline de eventos do pedido"""
    result = await db.execute(
        select(SiteOrder)
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    timeline = []
    
    # Order created
    timeline.append({
        "event": "order_created",
        "timestamp": order.created_at.isoformat(),
        "description": "Pedido criado"
    })
    
    # Payment
    if order.paid_at:
        timeline.append({
            "event": "payment_received",
            "timestamp": order.paid_at.isoformat(),
            "description": "Pagamento confirmado"
        })
    
    # Onboarding
    if order.onboarding_completed_at:
        timeline.append({
            "event": "onboarding_completed",
            "timestamp": order.onboarding_completed_at.isoformat(),
            "description": "Onboarding completo"
        })
    
    # Status changes
    if order.status == SiteOrderStatus.BRIEFING:
        timeline.append({
            "event": "briefing_ready",
            "timestamp": order.onboarding_completed_at.isoformat() if order.onboarding_completed_at else order.created_at.isoformat(),
            "description": "Briefing disponível para equipe"
        })
    
    if order.status in [SiteOrderStatus.BUILDING, SiteOrderStatus.GENERATING]:
        timeline.append({
            "event": "building_started",
            "timestamp": order.updated_at.isoformat(),
            "description": "Construção iniciada"
        })
    
    if order.preview_url:
        timeline.append({
            "event": "preview_ready",
            "timestamp": order.updated_at.isoformat(),
            "description": "Preview disponível"
        })
    
    # Delivery
    if order.delivered_at:
        timeline.append({
            "event": "delivered",
            "timestamp": order.delivered_at.isoformat(),
            "description": "Site entregue"
        })
    
    # Get feedbacks
    feedbacks_result = await db.execute(
        select(SiteFeedback)
        .where(SiteFeedback.order_id == order_id)
        .order_by(SiteFeedback.created_at.asc())
    )
    feedbacks = feedbacks_result.scalars().all()
    
    for feedback in feedbacks:
        timeline.append({
            "event": "feedback_submitted",
            "timestamp": feedback.created_at.isoformat(),
            "description": f"Feedback enviado ({feedback.role})" + (f" - Revisão #{feedback.revision_number}" if feedback.revision_number else ""),
            "message": feedback.message
        })
    
    # Sort by timestamp
    timeline.sort(key=lambda x: x["timestamp"])
    
    return {
        "order_id": order_id,
        "timeline": timeline
    }


# ============== Communication Endpoints ==============

class MessageCreate(BaseModel):
    message: Optional[str] = None
    message_type: str = "message"  # "message", "file", "link", "status_update"
    files: Optional[List[dict]] = None  # [{"name": "...", "url": "...", "size": 123}]
    links: Optional[List[dict]] = None  # [{"title": "...", "url": "...", "description": "..."}]
    is_important: bool = False


@router.post("/{order_id}/messages")
async def send_message(
    order_id: int,
    message_data: MessageCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Equipe ou cliente envia mensagem/arquivo/link"""
    # Verificar se pedido existe
    result = await db.execute(
        select(SiteOrder)
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Determinar remetente (admin ou cliente)
    sender_type = "admin"
    sender_id = None
    sender_name = None
    
    # Verificar token (admin ou cliente)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        
        # Tentar decodificar como customer token
        try:
            from app.models.site_customer import SiteCustomer
            payload = decode_customer_token(token)  # Returns dict with sub, email, type
            if payload and payload.get("type") == "customer":
                customer_id = int(payload["sub"])
                customer = await db.get(SiteCustomer, customer_id)
                if customer and customer.order_id == order_id:
                    sender_type = "client"
                    sender_id = customer.id
                    sender_name = customer.email.split("@")[0] if customer.email else "Cliente"
        except:
            pass
        
        # Se não for cliente, tentar como admin
        if sender_type != "client":
            try:
                from app.api.auth import decode_token
                user_data = decode_token(token)
                if user_data:
                    sender_type = "admin"
                    sender_id = user_data.get("user_id")
                    # Buscar nome do usuário
                    user_result = await db.execute(
                        select(User).where(User.id == sender_id)
                    )
                    user = user_result.scalar_one_or_none()
                    sender_name = user.name if user else "Equipe"
            except:
                pass
    
    # Se não tem token, assumir admin (para compatibilidade)
    if not sender_name:
        sender_name = "Equipe"
    
    # Criar mensagem
    message = SiteOrderMessage(
        order_id=order_id,
        sender_type=sender_type,
        sender_id=sender_id,
        sender_name=sender_name,
        message=message_data.message,
        message_type=message_data.message_type,
        files=message_data.files,
        links=message_data.links,
        is_important=message_data.is_important,
        is_read=False if sender_type == "admin" else True  # Admin envia, cliente precisa ler
    )
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    # Notify admins when client sends a message
    if sender_type == "client":
        try:
            from app.api.notifications import notify_all_admins
            await notify_all_admins(
                db,
                title="Nova mensagem do cliente",
                message=f"Pedido #{order_id}: {message_data.message[:80] or 'Arquivo/link enviado'}...",
                notification_type="info",
                related_entity_type="site_order",
                related_entity_id=order_id
            )
        except Exception as e:
            logger.warning(f"Failed to notify admins of client message: {e}")
    
    return {
        "id": message.id,
        "order_id": message.order_id,
        "sender_type": message.sender_type,
        "sender_name": message.sender_name,
        "message": message.message,
        "message_type": message.message_type,
        "files": message.files,
        "links": message.links,
        "is_important": message.is_important,
        "is_read": message.is_read,
        "created_at": message.created_at.isoformat()
    }


@router.get("/{order_id}/messages")
async def get_messages(
    order_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Lista todas as mensagens do pedido (admin ou cliente dono do pedido)."""
    from app.api.customer_auth.utils import extract_token, decode_token as decode_customer_token
    from app.models.site_customer import SiteCustomer
    
    # Try to authenticate as admin or customer
    is_authorized = False
    auth_header = request.headers.get("Authorization", "")
    
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        
        # Try customer token first
        try:
            customer_payload = decode_customer_token(token)
            customer_id = int(customer_payload["sub"])
            
            # Verify customer owns this order
            customer = await db.get(SiteCustomer, customer_id)
            if customer and customer.order_id == order_id:
                is_authorized = True
        except:
            pass
        
        # If not customer, try admin token
        if not is_authorized:
            try:
                from app.core.auth import verify_token
                user_payload = verify_token(token)
                if user_payload:
                    # Admin tokens have 'sub' (email) and 'user_id'
                    is_authorized = True
            except:
                pass
    
    if not is_authorized:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Verificar se pedido existe
    result = await db.execute(
        select(SiteOrder)
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Buscar mensagens
    messages_result = await db.execute(
        select(SiteOrderMessage)
        .where(SiteOrderMessage.order_id == order_id)
        .order_by(SiteOrderMessage.created_at.desc())
    )
    messages = messages_result.scalars().all()
    
    return {
        "order_id": order_id,
        "messages": [
            {
                "id": msg.id,
                "sender_type": msg.sender_type,
                "sender_name": msg.sender_name,
                "message": msg.message,
                "message_type": msg.message_type,
                "files": msg.files or [],
                "links": msg.links or [],
                "is_important": msg.is_important,
                "is_read": msg.is_read,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }


@router.patch("/{order_id}/messages/{message_id}/read")
async def mark_message_read(
    order_id: int,
    message_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Marca mensagem como lida (cliente)"""
    # Verificar se pedido existe
    result = await db.execute(
        select(SiteOrder)
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Buscar mensagem
    msg_result = await db.execute(
        select(SiteOrderMessage)
        .where(
            and_(
                SiteOrderMessage.id == message_id,
                SiteOrderMessage.order_id == order_id
            )
        )
    )
    message = msg_result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Marcar como lida
    message.is_read = True
    await db.commit()
    
    return {"success": True, "message_id": message_id}


@router.post("/{order_id}/upload")
async def upload_file(
    order_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Upload de arquivo para o pedido (apenas admin)"""
    import os
    import uuid
    from pathlib import Path
    
    # Verificar se pedido existe
    result = await db.execute(
        select(SiteOrder)
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Criar diretório para uploads do pedido
    upload_dir = Path(f"/app/generated_sites/uploads/order_{order_id}")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Gerar nome único
    file_ext = Path(file.filename).suffix
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / file_name
    
    # Salvar arquivo
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # URL relativa para acesso
    file_url = f"/api/site-orders/{order_id}/files/{file_name}"
    
    # Criar mensagem com arquivo
    message = SiteOrderMessage(
        order_id=order_id,
        sender_type="admin",
        sender_id=current_user.id,
        sender_name=current_user.name or "Equipe",
        message=description or f"Arquivo enviado: {file.filename}",
        message_type="file",
        files=[{
            "name": file.filename,
            "url": file_url,
            "size": len(content),
            "type": file.content_type or "application/octet-stream"
        }],
        is_read=False
    )
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return {
        "success": True,
        "message_id": message.id,
        "file": {
            "name": file.filename,
            "url": file_url,
            "size": len(content)
        }
    }


@router.get("/{order_id}/files/{filename}")
async def get_file(
    order_id: int,
    filename: str,
    db: AsyncSession = Depends(get_db)
):
    """Baixar arquivo do pedido"""
    from pathlib import Path
    
    # Verificar se pedido existe
    result = await db.execute(
        select(SiteOrder)
        .where(SiteOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Caminho do arquivo
    file_path = Path(f"/app/generated_sites/uploads/order_{order_id}/{filename}")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )
