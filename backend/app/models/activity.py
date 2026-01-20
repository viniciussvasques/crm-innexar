from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Date, Time
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

class ActivityType(str, enum.Enum):
    TASK = "task"
    CALL = "call"
    MEETING = "meeting"
    NOTE = "note"

class ActivityStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # task, call, meeting, note
    subject = Column(String, nullable=False)
    description = Column(Text)
    due_date = Column(Date)
    due_time = Column(Time)
    status = Column(String, default="pending")  # pending, completed, cancelled
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contact = relationship("Contact", back_populates="activities")
    opportunity = relationship("Opportunity", back_populates="activities")
    project = relationship("Project", back_populates="activities")
    owner = relationship("User", back_populates="activities")

