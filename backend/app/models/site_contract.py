from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class SiteContract(Base):
    """
    Electronic service agreement signed by the client during onboarding.
    Stores the full content of the contract, signing metadata and timestamp.
    """
    __tablename__ = "site_contracts"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("site_orders.id"), nullable=False, unique=True)
    
    # Contract details
    content = Column(Text, nullable=False)
    language = Column(String(5), default="pt") # pt, en, es
    
    # Signing metadata
    signed_name = Column(String, nullable=False)
    signed_email = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    signed_at = Column(DateTime, default=datetime.utcnow)
    
    # Optional document storage
    document_url = Column(String, nullable=True)
    version = Column(String, default="1.0")
    
    # Relationship
    order = relationship("SiteOrder", back_populates="contract")
