from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

class GoalType(str, enum.Enum):
    INDIVIDUAL = "individual"
    TEAM = "team"
    DEPARTMENT = "department"

class GoalPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class GoalStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"

class GoalCategory(str, enum.Enum):
    REVENUE = "revenue"
    DEALS = "deals"
    ACTIVITIES = "activities"
    CONVERSION_RATE = "conversion_rate"
    NEW_CLIENTS = "new_clients"
    CUSTOM = "custom"

class Goal(Base):
    """Sistema de metas para equipe de vendas"""
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Tipo e categoria
    goal_type = Column(Enum(GoalType), default=GoalType.INDIVIDUAL)
    category = Column(Enum(GoalCategory), default=GoalCategory.REVENUE)
    period = Column(Enum(GoalPeriod), default=GoalPeriod.MONTHLY)

    # Valores da meta
    target_value = Column(Float, nullable=False)  # Valor alvo
    current_value = Column(Float, default=0.0)    # Valor atual
    unit = Column(String(50), default="BRL")      # Unidade (BRL, USD, %, etc.)

    # Relacionamentos
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Para metas individuais

    # Datas
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Status e progresso
    status = Column(Enum(GoalStatus), default=GoalStatus.ACTIVE)
    progress_percentage = Column(Float, default=0.0)

    # Recompensas e penalidades
    reward_description = Column(Text)
    penalty_description = Column(Text)

    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_goals")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_goals")
