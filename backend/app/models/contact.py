from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, index=True)
    phone = Column(String)
    company = Column(String)
    status = Column(String, default="lead")  # lead, client, prospect
    notes = Column(Text)
    # Campos opcionais do formulário do site
    project_type = Column(String)  # web, saas, mobile, ecommerce, erp, integration, consulting, other
    budget_range = Column(String)  # under-10k, 10k-25k, 25k-50k, 50k-100k, 100k-250k, over-250k, discuss
    timeline = Column(String)  # asap, 1-3months, 3-6months, 6-12months, flexible, discuss
    website = Column(String)  # URL do site da empresa
    linkedin = Column(String)  # LinkedIn da empresa ou pessoa
    position = Column(String)  # Cargo/função do contato
    industry = Column(String)  # Setor/indústria
    company_size = Column(String)  # Tamanho da empresa
    source = Column(String)  # Origem do lead (website, landing_page, referral, etc.)
    contact_metadata = Column(Text)  # JSON com informações adicionais (checklist, etc.) - renomeado de 'metadata' pois é palavra reservada
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="contacts")
    opportunities = relationship("Opportunity", back_populates="contact")
    activities = relationship("Activity", back_populates="contact")
    projects = relationship("Project", back_populates="contact")
    lead_analysis = relationship("LeadAnalysis", back_populates="contact", uselist=False)

