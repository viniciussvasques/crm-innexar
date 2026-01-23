from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.configuration import (
    IntegrationConfigCreate, IntegrationConfigResponse, IntegrationConfigUpdate,
    DeployServerCreate, DeployServerResponse, DeployServerUpdate
)
from app.services.config_service import ConfigService
from app.models.configuration import IntegrationType, ServerType, DeployServer, IntegrationConfig

router = APIRouter()

# --- Integration Configs ---

@router.get("/config/integrations/{type}", response_model=List[IntegrationConfigResponse])
async def get_integrations_by_type(
    type: IntegrationType,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all configs for a specific integration type"""
    # Check admin permission if needed
    service = ConfigService(db)
    # This returns dict, we need models
    # Re-querying via model directly for response mapping or map manually
    configs = db.query(IntegrationConfig).filter(
        IntegrationConfig.integration_type == type,
        IntegrationConfig.is_active == True
    ).all()
    
    # Mask secrets
    for c in configs:
        if c.is_secret:
            c.value = "********" 
            
    return configs

@router.post("/config/integrations", response_model=IntegrationConfigResponse)
async def create_integration_config(
    config: IntegrationConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ConfigService(db)
    return service.set_config(
        type=config.integration_type,
        key=config.key,
        value=config.value,
        is_secret=config.is_secret,
        description=config.description
    )

@router.put("/config/integrations/{id}", response_model=IntegrationConfigResponse)
async def update_integration_config(
    id: int,
    config_update: IntegrationConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ConfigService(db)
    # Logic to fetch and update using service or direct DB
    # Using direct DB for update wrapper for now
    config = db.get(IntegrationConfig, id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
        
    if config_update.value is not None:
        if config.is_secret or config_update.is_secret:
            config.value = service.encrypt_value(config_update.value)
        else:
            config.value = config_update.value
            
    if config_update.is_secret is not None:
        config.is_secret = config_update.is_secret
    if config_update.description is not None:
        config.description = config_update.description
    if config_update.is_active is not None:
        config.is_active = config_update.is_active
        
    db.commit()
    db.refresh(config)
    return config

# --- Deploy Servers ---

@router.get("/config/deploy-servers", response_model=List[DeployServerResponse])
async def get_deploy_servers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(DeployServer).filter(DeployServer.is_active == True).all()

@router.post("/config/deploy-servers", response_model=DeployServerResponse)
async def create_deploy_server(
    server: DeployServerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ConfigService(db)
    return service.create_deploy_server(
        name=server.name,
        type=server.server_type,
        host=server.host,
        port=server.port,
        username=server.username,
        deploy_path=server.deploy_path,
        is_default=server.is_default,
        password=server.password,
        ssh_key=server.ssh_key
    )
