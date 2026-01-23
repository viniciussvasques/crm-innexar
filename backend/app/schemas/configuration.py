from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.configuration import IntegrationType, ServerType

class IntegrationConfigBase(BaseModel):
    integration_type: IntegrationType
    key: str
    value: str
    is_secret: bool = False
    description: Optional[str] = None

class IntegrationConfigCreate(IntegrationConfigBase):
    pass

class IntegrationConfigUpdate(BaseModel):
    value: Optional[str] = None
    is_secret: Optional[bool] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class IntegrationConfigResponse(IntegrationConfigBase):
    id: int
    is_active: bool
    last_tested_at: Optional[datetime] = None
    last_test_success: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    
    # Override value to mask secrets in response if needed, 
    # but frontend might need to see it if not secret.
    # Logic handled in endpoint.

    class Config:
        from_attributes = True

class DeployServerBase(BaseModel):
    name: str
    server_type: ServerType = ServerType.SSH
    host: Optional[str] = None
    port: int = 22
    username: Optional[str] = None
    deploy_path: Optional[str] = None
    is_default: bool = False

class DeployServerCreate(DeployServerBase):
    password: Optional[str] = None
    ssh_key: Optional[str] = None

class DeployServerUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_key: Optional[str] = None
    deploy_path: Optional[str] = None
    is_active: Optional[bool] = None

class DeployServerResponse(DeployServerBase):
    id: int
    is_active: bool
    disk_total_gb: Optional[int] = None
    disk_used_gb: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
