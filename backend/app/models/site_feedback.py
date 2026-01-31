from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class SiteFeedback(Base):
    """Feedback e solicitações de revisão do cliente/admin"""
    __tablename__ = "site_feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("site_orders.id"), nullable=False, index=True)
    
    # Conteúdo
    message = Column(Text, nullable=False)
    attachments = Column(JSON, nullable=True) # ["https://...", ...]
    
    # Metadados
    role = Column(String, default="client") # client, admin, system
    revision_number = Column(Integer, nullable=True) # Se for pedido de revisão, qual o número (1, 2)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("SiteOrder", back_populates="feedbacks")
