from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Notification(Base):
    """Sistema de notificações do CRM"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info")  # info, success, warning, error
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Entidade relacionada (opcional)
    related_entity_type = Column(String(50))  # opportunity, project, activity, etc.
    related_entity_id = Column(Integer)

    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_id])
