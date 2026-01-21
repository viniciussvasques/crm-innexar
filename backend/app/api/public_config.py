"""
Public Configuration API - No auth required for frontend configs
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any

from app.core.database import get_db
from app.models.system_config import SystemConfig


router = APIRouter(prefix="/public-config", tags=["public-config"])


@router.get("/site")
async def get_site_config(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get public site configuration (no auth required)"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.category == "site")
    )
    configs = result.scalars().all()
    
    return {c.key: c.get_value() for c in configs}


@router.get("/stripe/public-key")
async def get_stripe_public_key(db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """Get Stripe publishable key (no auth, public key only)"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "stripe_publishable_key")
    )
    config = result.scalar_one_or_none()
    
    return {"publishable_key": config.value if config else ""}


@router.get("/stripe/enabled")
async def get_stripe_enabled(db: AsyncSession = Depends(get_db)) -> Dict[str, bool]:
    """Check if Stripe is enabled"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "stripe_enabled")
    )
    config = result.scalar_one_or_none()
    
    enabled = config.get_value() if config else False
    return {"enabled": enabled}


@router.get("/stripe/keys")
async def get_stripe_keys(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Get all Stripe keys for internal server-to-server communication.
    This endpoint is meant for internal use (Docker network) only.
    """
    stripe_keys = [
        "stripe_secret_key",
        "stripe_publishable_key",
        "stripe_webhook_secret",
    ]
    
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key.in_(stripe_keys))
    )
    configs = result.scalars().all()
    
    return {c.key: c.value for c in configs}

