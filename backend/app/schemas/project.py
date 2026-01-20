from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.project import ProjectStatus, ProjectType

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    contact_id: int
    opportunity_id: Optional[int] = None
    project_type: ProjectType = ProjectType.CUSTOM_DEVELOPMENT
    estimated_value: Optional[str] = None
    technical_requirements: Optional[str] = None
    tech_stack: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    project_type: Optional[ProjectType] = None
    estimated_value: Optional[str] = None
    approved_value: Optional[str] = None
    planning_owner_id: Optional[int] = None
    dev_owner_id: Optional[int] = None
    start_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    technical_requirements: Optional[str] = None
    tech_stack: Optional[str] = None
    repository_url: Optional[str] = None
    deployment_url: Optional[str] = None
    internal_notes: Optional[str] = None
    planning_notes: Optional[str] = None
    dev_notes: Optional[str] = None
    client_notes: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: int
    status: ProjectStatus
    owner_id: int
    planning_owner_id: Optional[int] = None
    dev_owner_id: Optional[int] = None
    approved_value: Optional[str] = None
    start_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    repository_url: Optional[str] = None
    deployment_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    sent_to_planning_at: Optional[datetime] = None
    sent_to_dev_at: Optional[datetime] = None
    
    # Relacionamentos (opcionais)
    contact_name: Optional[str] = None
    owner_name: Optional[str] = None
    planning_owner_name: Optional[str] = None
    dev_owner_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class ProjectListResponse(BaseModel):
    id: int
    name: str
    status: ProjectStatus
    project_type: ProjectType
    contact_name: str
    owner_name: str
    planning_owner_name: Optional[str] = None
    dev_owner_name: Optional[str] = None
    estimated_value: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

