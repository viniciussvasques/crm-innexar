"""
Support Tickets API - Endpoints for customer portal and admin workspace
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.models import (
    SupportTicket, TicketMessage, CustomerNotification,
    TicketStatus, TicketPriority, User
)
from app.models.site_customer import SiteCustomer
from app.api.customer_auth.utils import decode_token, extract_token


router = APIRouter()


# ===================== SCHEMAS =====================

class CreateTicketRequest(BaseModel):
    subject: str
    message: str
    order_id: Optional[int] = None
    priority: Optional[str] = "medium"


class TicketReplyRequest(BaseModel):
    message: str


class TicketResponse(BaseModel):
    id: int
    subject: str
    status: str
    priority: str
    order_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    sender_type: str
    sender_name: Optional[str]
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class TicketDetailResponse(BaseModel):
    id: int
    subject: str
    status: str
    priority: str
    order_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    message: Optional[str]
    link_type: Optional[str]
    link_id: Optional[int]
    is_read: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===================== CUSTOMER ENDPOINTS =====================

@router.get("/me/tickets", response_model=List[TicketResponse])
async def get_customer_tickets(
    request: Request,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all tickets for the logged in customer"""
    jwt_token = extract_token(request, token)
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Token required")
    
    payload = decode_token(jwt_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    customer_id = payload.get("sub")
    
    tickets = db.query(SupportTicket).filter(
        SupportTicket.customer_id == customer_id
    ).order_by(desc(SupportTicket.updated_at)).all()
    
    result = []
    for t in tickets:
        result.append({
            "id": t.id,
            "subject": t.subject,
            "status": t.status,
            "priority": t.priority,
            "order_id": t.order_id,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "message_count": len(t.messages) if t.messages else 0
        })
    
    return result


@router.post("/me/tickets", response_model=TicketResponse)
async def create_customer_ticket(
    request: Request,
    data: CreateTicketRequest,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Create a new support ticket"""
    jwt_token = extract_token(request, token)
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Token required")
    
    payload = decode_token(jwt_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    customer_id = payload.get("sub")
    
    # Get customer for name
    customer = db.query(SiteCustomer).filter(SiteCustomer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Create ticket
    ticket = SupportTicket(
        customer_id=customer_id,
        order_id=data.order_id,
        subject=data.subject,
        status=TicketStatus.OPEN.value,
        priority=data.priority or TicketPriority.MEDIUM.value
    )
    db.add(ticket)
    db.flush()
    
    # Create initial message
    message = TicketMessage(
        ticket_id=ticket.id,
        sender_type="customer",
        sender_id=customer_id,
        sender_name=customer.email.split("@")[0],
        message=data.message
    )
    db.add(message)
    db.commit()
    db.refresh(ticket)
    
    return {
        "id": ticket.id,
        "subject": ticket.subject,
        "status": ticket.status,
        "priority": ticket.priority,
        "order_id": ticket.order_id,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "message_count": 1
    }


@router.get("/me/tickets/{ticket_id}", response_model=TicketDetailResponse)
async def get_customer_ticket_detail(
    ticket_id: int,
    request: Request,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get ticket details with all messages"""
    jwt_token = extract_token(request, token)
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Token required")
    
    payload = decode_token(jwt_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    customer_id = payload.get("sub")
    
    ticket = db.query(SupportTicket).options(
        selectinload(SupportTicket.messages)
    ).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.customer_id == customer_id
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return ticket


@router.post("/me/tickets/{ticket_id}/reply")
async def customer_reply_ticket(
    ticket_id: int,
    data: TicketReplyRequest,
    request: Request,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Customer replies to a ticket"""
    jwt_token = extract_token(request, token)
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Token required")
    
    payload = decode_token(jwt_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    customer_id = payload.get("sub")
    
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.customer_id == customer_id
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    customer = db.query(SiteCustomer).filter(SiteCustomer.id == customer_id).first()
    
    # Add message
    message = TicketMessage(
        ticket_id=ticket_id,
        sender_type="customer",
        sender_id=customer_id,
        sender_name=customer.email.split("@")[0] if customer else "Customer",
        message=data.message
    )
    db.add(message)
    
    # Update ticket status if it was resolved
    if ticket.status == TicketStatus.RESOLVED.value:
        ticket.status = TicketStatus.OPEN.value
    
    ticket.updated_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "Reply sent"}


@router.get("/me/notifications", response_model=List[NotificationResponse])
async def get_customer_notifications(
    request: Request,
    token: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get customer notifications"""
    jwt_token = extract_token(request, token)
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Token required")
    
    payload = decode_token(jwt_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    customer_id = payload.get("sub")
    
    query = db.query(CustomerNotification).filter(
        CustomerNotification.customer_id == customer_id
    )
    
    if unread_only:
        query = query.filter(CustomerNotification.is_read == "false")
    
    notifications = query.order_by(desc(CustomerNotification.created_at)).limit(50).all()
    
    return notifications


@router.post("/me/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    request: Request,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    jwt_token = extract_token(request, token)
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Token required")
    
    payload = decode_token(jwt_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    customer_id = payload.get("sub")
    
    notification = db.query(CustomerNotification).filter(
        CustomerNotification.id == notification_id,
        CustomerNotification.customer_id == customer_id
    ).first()
    
    if notification:
        notification.is_read = "true"
        db.commit()
    
    return {"success": True}
