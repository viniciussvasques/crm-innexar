"""
Admin Tickets API - Endpoints for workspace ticket management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models import (
    SupportTicket, TicketMessage, CustomerNotification,
    TicketStatus, TicketPriority, User
)
from app.models.site_customer import SiteCustomer


router = APIRouter()


# ===================== SCHEMAS =====================

class AdminTicketResponse(BaseModel):
    id: int
    subject: str
    status: str
    priority: str
    customer_email: Optional[str] = None
    order_id: Optional[int] = None
    assigned_to: Optional[int] = None
    assigned_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class AssignTicketRequest(BaseModel):
    user_id: int


class UpdateTicketStatusRequest(BaseModel):
    status: str


class AdminReplyRequest(BaseModel):
    message: str


class TicketStatsResponse(BaseModel):
    open: int
    pending: int
    resolved: int
    closed: int
    total: int


# ===================== ADMIN ENDPOINTS =====================

@router.get("/stats", response_model=TicketStatsResponse)
async def get_ticket_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ticket statistics"""
    stats = db.query(
        SupportTicket.status,
        func.count(SupportTicket.id)
    ).group_by(SupportTicket.status).all()
    
    result = {"open": 0, "pending": 0, "resolved": 0, "closed": 0, "total": 0}
    for status, count in stats:
        if status in result:
            result[status] = count
        result["total"] += count
    
    return result


@router.get("", response_model=List[AdminTicketResponse])
async def get_all_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[int] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tickets with filters"""
    query = db.query(SupportTicket).options(
        joinedload(SupportTicket.customer),
        joinedload(SupportTicket.assigned_user)
    )
    
    if status:
        query = query.filter(SupportTicket.status == status)
    if priority:
        query = query.filter(SupportTicket.priority == priority)
    if assigned_to:
        query = query.filter(SupportTicket.assigned_to == assigned_to)
    
    tickets = query.order_by(desc(SupportTicket.updated_at)).offset(offset).limit(limit).all()
    
    result = []
    for t in tickets:
        result.append({
            "id": t.id,
            "subject": t.subject,
            "status": t.status,
            "priority": t.priority,
            "customer_email": t.customer.email if t.customer else None,
            "order_id": t.order_id,
            "assigned_to": t.assigned_to,
            "assigned_name": t.assigned_user.name if t.assigned_user else None,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "message_count": len(t.messages) if t.messages else 0
        })
    
    return result


@router.get("/{ticket_id}")
async def get_ticket_detail(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ticket details with all messages"""
    ticket = db.query(SupportTicket).options(
        selectinload(SupportTicket.messages),
        joinedload(SupportTicket.customer),
        joinedload(SupportTicket.assigned_user),
        joinedload(SupportTicket.order)
    ).filter(SupportTicket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return {
        "id": ticket.id,
        "subject": ticket.subject,
        "status": ticket.status,
        "priority": ticket.priority,
        "customer_email": ticket.customer.email if ticket.customer else None,
        "customer_id": ticket.customer_id,
        "order_id": ticket.order_id,
        "order_name": ticket.order.onboarding.business_name if ticket.order and ticket.order.onboarding else None,
        "assigned_to": ticket.assigned_to,
        "assigned_name": ticket.assigned_user.name if ticket.assigned_user else None,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "resolved_at": ticket.resolved_at,
        "messages": [
            {
                "id": m.id,
                "sender_type": m.sender_type,
                "sender_name": m.sender_name,
                "message": m.message,
                "created_at": m.created_at
            }
            for m in ticket.messages
        ]
    }


@router.post("/{ticket_id}/reply")
async def admin_reply_ticket(
    ticket_id: int,
    data: AdminReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin/Staff replies to a ticket"""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Add message
    message = TicketMessage(
        ticket_id=ticket_id,
        sender_type="staff",
        sender_id=current_user.id,
        sender_name=current_user.name,
        message=data.message
    )
    db.add(message)
    
    # Update ticket status to pending (waiting for customer)
    if ticket.status == TicketStatus.OPEN.value:
        ticket.status = TicketStatus.PENDING.value
    
    ticket.updated_at = datetime.utcnow()
    
    # Create notification for customer
    notification = CustomerNotification(
        customer_id=ticket.customer_id,
        type="ticket_reply",
        title="New reply on your ticket",
        message=f"Your ticket '{ticket.subject}' has a new reply from support.",
        link_type="ticket",
        link_id=ticket_id
    )
    db.add(notification)
    
    db.commit()
    
    return {"success": True, "message": "Reply sent and customer notified"}


@router.post("/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: int,
    data: AssignTicketRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assign ticket to a user"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can assign tickets")
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    ticket.assigned_to = data.user_id
    ticket.updated_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "assigned_to": user.name}


@router.patch("/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: int,
    data: UpdateTicketStatusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update ticket status"""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    valid_statuses = [s.value for s in TicketStatus]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    old_status = ticket.status
    ticket.status = data.status
    ticket.updated_at = datetime.utcnow()
    
    if data.status == TicketStatus.RESOLVED.value:
        ticket.resolved_at = datetime.utcnow()
        
        # Notify customer
        notification = CustomerNotification(
            customer_id=ticket.customer_id,
            type="ticket_resolved",
            title="Your ticket has been resolved",
            message=f"Your ticket '{ticket.subject}' has been marked as resolved.",
            link_type="ticket",
            link_id=ticket_id
        )
        db.add(notification)
    
    db.commit()
    
    return {"success": True, "old_status": old_status, "new_status": data.status}


@router.patch("/{ticket_id}/priority")
async def update_ticket_priority(
    ticket_id: int,
    priority: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update ticket priority"""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    valid_priorities = [p.value for p in TicketPriority]
    if priority not in valid_priorities:
        raise HTTPException(status_code=400, detail=f"Invalid priority. Must be one of: {valid_priorities}")
    
    ticket.priority = priority
    ticket.updated_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "priority": priority}
