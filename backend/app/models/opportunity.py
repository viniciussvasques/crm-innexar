from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Opportunity(Base):
    __tablename__ = "opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    value = Column(Numeric(10, 2))
    stage = Column(String, default="qualificacao")  # qualificacao, proposta, negociacao, fechado, perdido
    probability = Column(Integer, default=0)  # 0-100
    expected_close_date = Column(Date)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contact = relationship("Contact", back_populates="opportunities")
    owner = relationship("User", back_populates="opportunities")
    activities = relationship("Activity", back_populates="opportunity")
    projects = relationship("Project", back_populates="opportunity")

