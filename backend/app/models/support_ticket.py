"""
Support Ticket Model - Support tickets from client portal
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SupportTicket(Base):
    """Support ticket from customer portal"""
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Customer relationship
    customer_id = Column(Integer, ForeignKey("site_customers.id"), nullable=False, index=True)
    
    # Optional order relationship
    order_id = Column(Integer, ForeignKey("site_orders.id"), nullable=True, index=True)
    
    # Ticket details
    subject = Column(String(255), nullable=False)
    status = Column(String(20), default=TicketStatus.OPEN.value, index=True)
    priority = Column(String(20), default=TicketPriority.MEDIUM.value)
    
    # Assignment
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    customer = relationship("SiteCustomer", backref="tickets")
    order = relationship("SiteOrder", backref="tickets")
    assigned_user = relationship("User", backref="assigned_tickets")
    messages = relationship("TicketMessage", back_populates="ticket", order_by="TicketMessage.created_at")


class TicketMessage(Base):
    """Message in a support ticket conversation"""
    __tablename__ = "ticket_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Ticket relationship
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False, index=True)
    
    # Sender info
    sender_type = Column(String(20), nullable=False)  # 'customer' or 'staff'
    sender_id = Column(Integer, nullable=False)  # customer_id or user_id
    sender_name = Column(String(100), nullable=True)  # Cached name for display
    
    # Message content
    message = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ticket = relationship("SupportTicket", back_populates="messages")


class CustomerNotification(Base):
    """Notification for customer portal"""
    __tablename__ = "customer_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Customer relationship
    customer_id = Column(Integer, ForeignKey("site_customers.id"), nullable=False, index=True)
    
    # Notification details
    type = Column(String(50), nullable=False)  # ticket_reply, order_update, etc
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    
    # Link data
    link_type = Column(String(50), nullable=True)  # ticket, order, etc
    link_id = Column(Integer, nullable=True)
    
    # Status
    is_read = Column(String(10), default="false")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("SiteCustomer", backref="notifications")
