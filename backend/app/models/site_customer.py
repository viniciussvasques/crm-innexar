"""
Site Customer Model - Customer accounts for the client portal
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import secrets


class SiteCustomer(Base):
    """Customer account for site portal access"""
    __tablename__ = "site_customers"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Link to order
    order_id = Column(Integer, ForeignKey("site_orders.id"), unique=True, nullable=False)
    
    # Auth
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    
    # Email verification
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True, index=True)
    verification_sent_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Password reset
    reset_token = Column(String, nullable=True, index=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # Session
    last_login = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = relationship("SiteOrder", back_populates="customer")
    
    @staticmethod
    def generate_verification_token():
        """Generate a secure verification token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_temp_password():
        """Generate a temporary password"""
        return secrets.token_urlsafe(12)
