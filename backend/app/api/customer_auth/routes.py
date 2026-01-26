from fastapi import APIRouter, Depends, Header, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional
import secrets

from app.core.database import get_db
from app.models.site_customer import SiteCustomer
from app.models.site_order import SiteOrder
from app.services.email_service import email_service

from .schemas import (
    LoginRequest, LoginResponse,
    VerifyEmailRequest, ForgotPasswordRequest, ResetPasswordRequest,
    CustomerProfile, OrderSummary
)
from .utils import hash_password, verify_password, create_token, decode_token, get_token_from_request

router = APIRouter(prefix="/customer-auth", tags=["Customer Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SiteCustomer).where(SiteCustomer.email == data.email.lower())
    )
    customer = result.scalar_one_or_none()
    
    if not customer or not verify_password(data.password, customer.password_hash):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    if not customer.email_verified:
        from fastapi import HTTPException
        # Return more helpful error with verification link
        raise HTTPException(
            status_code=403, 
            detail="Email não verificado. Por favor, verifique seu email antes de fazer login. Se não recebeu o email, verifique sua caixa de spam ou solicite um novo email de verificação."
        )
    
    customer.last_login = datetime.utcnow()
    await db.commit()
    
    return LoginResponse(
        access_token=create_token(customer.id, customer.email),
        customer_id=customer.id,
        email=customer.email
    )


@router.post("/verify")
async def verify_email(data: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SiteCustomer).where(SiteCustomer.verification_token == data.token)
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Invalid verification token")
    
    if customer.email_verified:
        return {"message": "Email already verified"}
    
    customer.email_verified = True
    customer.verified_at = datetime.utcnow()
    customer.verification_token = None
    await db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SiteCustomer).where(SiteCustomer.email == data.email.lower())
    )
    customer = result.scalar_one_or_none()
    
    if customer:
        reset_token = secrets.token_urlsafe(32)
        customer.reset_token = reset_token
        customer.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        await db.commit()
        
        background_tasks.add_task(
            email_service.send_password_reset_email,
            customer_name=customer.email.split("@")[0],
            to_email=customer.email,
            reset_token=reset_token
        )
    
    return {"message": "If email exists, reset instructions have been sent"}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SiteCustomer).where(SiteCustomer.reset_token == data.token)
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Invalid reset token")
    
    if customer.reset_token_expires and customer.reset_token_expires < datetime.utcnow():
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Reset token expired")
    
    customer.password_hash = hash_password(data.new_password)
    customer.reset_token = None
    customer.reset_token_expires = None
    await db.commit()
    
    return {"message": "Password reset successfully"}


@router.get("/me", response_model=CustomerProfile)
async def get_profile(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    actual_token = get_token_from_request(authorization, token)
    payload = decode_token(actual_token)
    customer_id = int(payload["sub"])
    
    customer = await db.get(SiteCustomer, customer_id)
    if not customer:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return CustomerProfile(
        id=customer.id,
        email=customer.email,
        email_verified=customer.email_verified,
        order_id=customer.order_id
    )


@router.get("/me/orders")
async def get_orders(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    actual_token = get_token_from_request(authorization, token)
    payload = decode_token(actual_token)
    customer_id = int(payload["sub"])
    
    customer = await db.get(SiteCustomer, customer_id)
    if not customer:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer.order_id:
        return {"orders": [], "customer": {"id": customer.id, "email": customer.email}}
    
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(SiteOrder)
        .options(selectinload(SiteOrder.onboarding))
        .where(SiteOrder.id == customer.order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        return {"orders": [], "customer": {"id": customer.id, "email": customer.email}}
    
    order_data = {
        "id": order.id,
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "status": order.status.value if order.status else "pending",
        "total_price": float(order.total_price),
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "expected_delivery_date": order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
        "site_url": order.site_url,
        "revisions_included": order.revisions_included,
        "revisions_used": order.revisions_used,
        "onboarding": None
    }
    
    if order.onboarding:
        order_data["onboarding"] = {
            "business_name": order.onboarding.business_name,
            "primary_city": order.onboarding.primary_city,
            "state": order.onboarding.state,
            "primary_color": order.onboarding.primary_color,
            "is_complete": order.onboarding.is_complete
        }
    
    return {
        "orders": [order_data],
        "customer": {"id": customer.id, "email": customer.email}
    }
