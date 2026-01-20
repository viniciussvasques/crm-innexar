from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base
from datetime import datetime
import enum
from sqlalchemy import Enum as SQLEnum

class CommissionStructure(Base):
    """Estrutura de comissões configurável"""
    __tablename__ = "commission_structures"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Nome da estrutura (ex: "US Sales Team")
    weekly_base = Column(Numeric(10, 2), default=100.00)  # Base semanal em USD
    currency = Column(String, default="USD")  # Moeda
    
    # Estrutura de comissão por faixa (JSON)
    # Exemplo: [{"min": 0, "max": 2000, "rate": 0.20}, {"min": 2001, "max": 10000, "rate": 0.15}, ...]
    tiered_commissions = Column(JSONB)  # Lista de faixas
    
    # Bônus de performance (JSON)
    # Exemplo: [{"threshold": 10000, "bonus": 150}, {"threshold": 20000, "bonus": 300}, ...]
    performance_bonuses = Column(JSONB)
    
    # Comissão recorrente para assinaturas
    recurring_commission_rate = Column(Numeric(5, 4), default=0.10)  # 10%
    
    # Bônus por novos clientes
    new_client_bonus = Column(Numeric(10, 2), default=100.00)
    new_client_threshold = Column(Integer, default=10)  # A cada 10 clientes
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    commissions = relationship("Commission", back_populates="structure")


class Commission(Base):
    """Histórico de comissões calculadas e pagas"""
    __tablename__ = "commissions"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    structure_id = Column(Integer, ForeignKey("commission_structures.id"), nullable=True)
    
    # Origem da comissão
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    # Valores
    deal_value = Column(Numeric(10, 2), nullable=False)  # Valor do negócio
    commission_rate = Column(Numeric(5, 4), nullable=False)  # Taxa aplicada
    commission_amount = Column(Numeric(10, 2), nullable=False)  # Valor da comissão
    weekly_base = Column(Numeric(10, 2), default=0)  # Base semanal
    performance_bonus = Column(Numeric(10, 2), default=0)  # Bônus de performance
    new_client_bonus = Column(Numeric(10, 2), default=0)  # Bônus de novo cliente
    
    total_amount = Column(Numeric(10, 2), nullable=False)  # Total a pagar
    
    # Status
    status = Column(String, default="pending")  # pending, approved, paid, cancelled
    payment_date = Column(DateTime, nullable=True)
    payment_period = Column(String)  # Ex: "2025-01" para janeiro de 2025
    
    # Metadados
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    seller = relationship("User", foreign_keys=[seller_id])
    structure = relationship("CommissionStructure", back_populates="commissions")
    opportunity = relationship("Opportunity")
    project = relationship("Project")


class QuoteRequest(Base):
    """Solicitação de orçamento do vendedor para planejamento"""
    __tablename__ = "quote_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    planning_owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Status do orçamento
    status = Column(String, default="pending")  # pending, in_progress, completed, cancelled
    
    # Informações do vendedor
    seller_notes = Column(Text)  # Notas do vendedor sobre o projeto
    
    # Informações do planejamento (preenchidas pela equipe)
    technologies = Column(JSONB)  # Lista de tecnologias
    stages = Column(JSONB)  # Etapas do projeto com prazos
    # Exemplo: [{"name": "Planejamento", "duration_days": 5, "start_date": "2025-01-15"}, ...]
    estimated_deadline = Column(DateTime, nullable=True)
    estimated_hours = Column(Integer, nullable=True)  # Horas estimadas de desenvolvimento
    technical_specs = Column(Text)  # Especificações técnicas detalhadas
    ai_generated = Column(Boolean, default=False)  # Se foi gerado com IA
    
    # Valores
    estimated_value = Column(String)  # Valor estimado (pode ser range)
    breakdown = Column(JSONB)  # Breakdown detalhado dos custos
    
    # Notificações
    seller_notified_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project")
    seller = relationship("User", foreign_keys=[seller_id])
    planning_owner = relationship("User", foreign_keys=[planning_owner_id])

