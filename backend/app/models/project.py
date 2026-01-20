from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

class ProjectStatus(str, enum.Enum):
    """Status do projeto no fluxo Innexar"""
    LEAD = "lead"  # Lead captado
    QUALIFICACAO = "qualificacao"  # Vendedor qualificando
    PROPOSTA = "proposta"  # Proposta criada, aguardando aprovação
    APROVADO = "aprovado"  # Cliente aprovou, pronto para planejamento
    EM_PLANEJAMENTO = "em_planejamento"  # Equipe de planejamento trabalhando
    PLANEJAMENTO_CONCLUIDO = "planejamento_concluido"  # Planejamento concluído, pronto para dev
    EM_DESENVOLVIMENTO = "em_desenvolvimento"  # Equipe técnica trabalhando
    EM_REVISAO = "em_revisao"  # Em revisão/ajustes
    CONCLUIDO = "concluido"  # Projeto entregue
    CANCELADO = "cancelado"  # Projeto cancelado

class ProjectType(str, enum.Enum):
    """Tipos de projeto Innexar"""
    MARKETING_SITE = "marketing_site"  # Site de marketing
    SAAS_PLATFORM = "saas_platform"  # Plataforma SaaS
    ENTERPRISE_SOFTWARE = "enterprise_software"  # Software empresarial
    CUSTOM_DEVELOPMENT = "custom_development"  # Desenvolvimento customizado
    CONSULTING = "consulting"  # Consultoria
    OTHER = "other"  # Outro

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    
    # Relacionamentos
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)  # Pode vir de uma oportunidade
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Vendedor responsável
    planning_owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Responsável planejamento
    dev_owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Responsável desenvolvimento
    
    # Tipo e status
    project_type = Column(SQLEnum(ProjectType), default=ProjectType.CUSTOM_DEVELOPMENT)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.LEAD, index=True)
    
    # Valores e prazos
    estimated_value = Column(String)  # Valor estimado (pode ser range)
    approved_value = Column(String)  # Valor aprovado
    start_date = Column(DateTime, nullable=True)
    expected_delivery_date = Column(DateTime, nullable=True)
    actual_delivery_date = Column(DateTime, nullable=True)
    
    # Informações técnicas
    technical_requirements = Column(Text)  # Requisitos técnicos
    tech_stack = Column(String)  # Stack tecnológico (opcional)
    repository_url = Column(String, nullable=True)  # URL do repositório
    deployment_url = Column(String, nullable=True)  # URL de deploy
    
    # Notas e comunicação
    internal_notes = Column(Text)  # Notas internas (vendedor/gestor)
    planning_notes = Column(Text)  # Notas do planejamento
    dev_notes = Column(Text)  # Notas do desenvolvimento
    client_notes = Column(Text)  # Notas do cliente
    
    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_to_planning_at = Column(DateTime, nullable=True)  # Quando foi enviado para planejamento
    sent_to_dev_at = Column(DateTime, nullable=True)  # Quando foi enviado para desenvolvimento
    
    # Relationships
    contact = relationship("Contact", back_populates="projects")
    opportunity = relationship("Opportunity", back_populates="projects")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_projects")
    planning_owner = relationship("User", foreign_keys=[planning_owner_id], back_populates="planning_projects")
    dev_owner = relationship("User", foreign_keys=[dev_owner_id], back_populates="dev_projects")
    activities = relationship("Activity", back_populates="project")

