from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
from datetime import datetime

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    VENDEDOR = "vendedor"
    PLANEJAMENTO = "planejamento"  # Equipe de planejamento
    DEV = "dev"  # Equipe de desenvolvimento

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    # Usar String em vez de Enum para evitar problemas com valores do enum
    role = Column(String(20), default=UserRole.VENDEDOR.value, nullable=False)
    
    @property
    def role_enum(self) -> UserRole:
        """Retorna o role como enum para compatibilidade"""
        return UserRole(self.role) if isinstance(self.role, str) else self.role
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contacts = relationship("Contact", back_populates="owner")
    opportunities = relationship("Opportunity", back_populates="owner")
    activities = relationship("Activity", back_populates="owner")
    owned_projects = relationship("Project", foreign_keys="Project.owner_id", back_populates="owner")
    planning_projects = relationship("Project", foreign_keys="Project.planning_owner_id", back_populates="planning_owner")
    dev_projects = relationship("Project", foreign_keys="Project.dev_owner_id", back_populates="dev_owner")

    # Goals relationships
    created_goals = relationship("Goal", foreign_keys="Goal.creator_id", back_populates="creator")
    assigned_goals = relationship("Goal", foreign_keys="Goal.assignee_id", back_populates="assignee")

