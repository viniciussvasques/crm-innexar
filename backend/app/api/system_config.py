"""
System Configuration API - Admin-configurable settings
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.models.user import User
from app.models.system_config import SystemConfig, DEFAULT_CONFIGS
from app.api.dependencies import get_current_user, require_admin


router = APIRouter(prefix="/system-config", tags=["system-config"])


class ConfigUpdate(BaseModel):
    value: str


class ConfigResponse(BaseModel):
    key: str
    value: Optional[str]
    value_type: str
    category: str
    description: Optional[str]
    is_secret: bool

    class Config:
        from_attributes = True


class ConfigBulkUpdate(BaseModel):
    configs: Dict[str, str]  # key: value pairs


# ============== Endpoints ==============

@router.get("/")
async def list_configs(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> List[ConfigResponse]:
    """List all system configurations (admin only)"""
    query = select(SystemConfig).order_by(SystemConfig.category, SystemConfig.key)
    
    if category:
        query = query.where(SystemConfig.category == category)
    
    result = await db.execute(query)
    configs = result.scalars().all()
    
    # Mask secret values
    return [
        ConfigResponse(
            key=c.key,
            value=c.get_masked_value() if c.is_secret else c.value,
            value_type=c.value_type,
            category=c.category,
            description=c.description,
            is_secret=c.is_secret
        )
        for c in configs
    ]


@router.get("/categories")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> List[str]:
    """List all configuration categories"""
    result = await db.execute(
        select(SystemConfig.category).distinct()
    )
    return [row[0] for row in result.all()]


@router.get("/by-category/{category}")
async def get_configs_by_category(
    category: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Get all configs for a category as a dictionary"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.category == category)
    )
    configs = result.scalars().all()
    
    return {
        c.key: {
            "value": c.get_masked_value() if c.is_secret else c.value,
            "value_type": c.value_type,
            "description": c.description,
            "is_secret": c.is_secret
        }
        for c in configs
    }


@router.get("/{key}")
async def get_config(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
) -> ConfigResponse:
    """Get a specific configuration value"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    return ConfigResponse(
        key=config.key,
        value=config.get_masked_value() if config.is_secret else config.value,
        value_type=config.value_type,
        category=config.category,
        description=config.description,
        is_secret=config.is_secret
    )


@router.put("/{key}")
async def update_config(
    key: str,
    update: ConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a configuration value (admin only)"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    config.value = update.value
    await db.commit()
    
    return {"message": f"Config '{key}' updated successfully"}


@router.put("/bulk/update")
async def bulk_update_configs(
    updates: ConfigBulkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update multiple configurations at once (admin only)"""
    updated = []
    
    for key, value in updates.configs.items():
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        config = result.scalar_one_or_none()
        
        if config:
            config.value = value
            updated.append(key)
    
    await db.commit()
    
    return {"message": f"Updated {len(updated)} configs", "keys": updated}


@router.post("/seed")
async def seed_default_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Seed default configurations if they don't exist (admin only)"""
    created = []
    
    for config_data in DEFAULT_CONFIGS:
        # Check if exists
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == config_data["key"])
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            config = SystemConfig(
                key=config_data["key"],
                value=config_data.get("value"),
                value_type=config_data.get("value_type", "string"),
                category=config_data["category"],
                description=config_data.get("description"),
                is_secret=config_data.get("is_secret", False)
            )
            db.add(config)
            created.append(config_data["key"])
    
    await db.commit()
    
    return {"message": f"Seeded {len(created)} new configs", "keys": created}


# ============== Public getter (for internal use) ==============

async def get_config_value(db: AsyncSession, key: str) -> Optional[Any]:
    """Get a config value (internal use, no auth required)"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalar_one_or_none()
    
    if config:
        return config.get_value()
    return None


async def get_stripe_config(db: AsyncSession) -> Dict[str, Any]:
    """Get all Stripe config values"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.category == "stripe")
    )
    configs = result.scalars().all()
    
    return {c.key: c.get_value() for c in configs}


async def get_email_config(db: AsyncSession) -> Dict[str, Any]:
    """Get all Email config values"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.category == "email")
    )
    configs = result.scalars().all()
    
    return {c.key: c.get_value() for c in configs}
