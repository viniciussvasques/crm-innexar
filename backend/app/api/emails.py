"""
Email API endpoints for sending notifications.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models import SiteOrder
from app.services.email_service import email_service
from app.api.auth import require_admin

router = APIRouter(prefix="/api/emails", tags=["emails"])


class SendEmailRequest(BaseModel):
    """Request body for sending emails."""
    order_id: int
    email_type: str  # payment_confirmation, onboarding_complete, in_progress, ready_for_review, delivered
    preview_url: Optional[str] = None
    site_url: Optional[str] = None


def order_to_dict(order: SiteOrder) -> dict:
    """Convert SiteOrder model to dict for email service."""
    result = {
        "id": order.id,
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "total_price": float(order.total_price),
        "status": order.status.value if order.status else "pending",
        "revisions_included": order.revisions_included,
        "revisions_used": order.revisions_used,
    }

    if order.onboarding:
        result["onboarding"] = {
            "business_name": order.onboarding.business_name,
            "primary_city": order.onboarding.primary_city,
            "state": order.onboarding.state,
        }

    return result


@router.post("/send")
async def send_email(
    request: SendEmailRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Send an email notification for an order."""
    # Get order
    order = db.query(SiteOrder).filter(SiteOrder.id == request.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_dict = order_to_dict(order)

    # Send appropriate email
    success = False
    if request.email_type == "payment_confirmation":
        success = email_service.send_payment_confirmation(order_dict)
    elif request.email_type == "onboarding_complete":
        success = email_service.send_onboarding_complete(order_dict)
    elif request.email_type == "in_progress":
        success = email_service.send_site_in_progress(order_dict)
    elif request.email_type == "ready_for_review":
        if not request.preview_url:
            raise HTTPException(status_code=400, detail="preview_url required for ready_for_review email")
        success = email_service.send_ready_for_review(order_dict, request.preview_url)
    elif request.email_type == "delivered":
        if not request.site_url:
            raise HTTPException(status_code=400, detail="site_url required for delivered email")
        success = email_service.send_site_delivered(order_dict, request.site_url)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown email_type: {request.email_type}")

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")

    return {"success": True, "message": f"Email '{request.email_type}' sent to {order.customer_email}"}


@router.post("/send-payment-confirmation/{order_id}")
async def send_payment_confirmation_email(
    order_id: int,
    db: Session = Depends(get_db),
):
    """Public endpoint to send payment confirmation (called by webhook)."""
    order = db.query(SiteOrder).filter(SiteOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_dict = order_to_dict(order)
    success = email_service.send_payment_confirmation(order_dict)

    return {"success": success}


@router.post("/send-onboarding-complete/{order_id}")
async def send_onboarding_complete_email(
    order_id: int,
    db: Session = Depends(get_db),
):
    """Public endpoint to send onboarding complete email."""
    order = db.query(SiteOrder).filter(SiteOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_dict = order_to_dict(order)
    success = email_service.send_onboarding_complete(order_dict)

    return {"success": success}


class VerificationEmailRequest(BaseModel):
    """Request body for verification email."""
    email: str
    verification_token: str
    temp_password: str
    order_id: int
    customer_name: str


@router.post("/send-verification")
async def send_verification_email(
    request: VerificationEmailRequest,
):
    """Send email verification with portal credentials."""
    verification_url = f"https://innexar.app/dashboard/verify?token={request.verification_token}"
    
    success = email_service.send_custom_email(
        to_email=request.email,
        subject="Verifique seu email - Innexar Portal",
        template_data={
            "customer_name": request.customer_name,
            "verification_url": verification_url,
            "temp_password": request.temp_password,
            "login_url": "https://innexar.app/dashboard/login",
        },
        template_name="verification"
    )
    
    return {"success": success}
