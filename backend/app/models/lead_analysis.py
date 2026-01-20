"""
Modelo para análises de leads geradas pela IA
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class LeadAnalysis(Base):
    """Análise de lead gerada pela IA"""
    __tablename__ = "lead_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False, unique=True)
    
    # Informações da análise
    company_info = Column(Text, nullable=True)  # Informações sobre a empresa
    market_analysis = Column(Text, nullable=True)  # Análise de mercado
    financial_insights = Column(Text, nullable=True)  # Insights financeiros
    recommendations = Column(Text, nullable=True)  # Recomendações para o vendedor
    risk_assessment = Column(Text, nullable=True)  # Avaliação de riscos
    opportunity_score = Column(Integer, nullable=True)  # Score de oportunidade (0-100)
    
    # Metadados
    analysis_metadata = Column(JSON, nullable=True)  # Dados adicionais (fontes, links, etc.)
    ai_model_used = Column(String(100), nullable=True)  # Modelo de IA usado
    analysis_status = Column(String(20), default="pending")  # pending, completed, error
    error_message = Column(Text, nullable=True)  # Mensagem de erro se falhar
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    analyzed_at = Column(DateTime, nullable=True)  # Quando a análise foi concluída
    
    # Relationships
    contact = relationship("Contact", foreign_keys=[contact_id], back_populates="lead_analysis")

