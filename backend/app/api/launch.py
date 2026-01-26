"""
Launch API - Public endpoints for website launch flow
Routes the Stripe webhook from /api/launch/webhook to the site_orders handler
"""
from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.site_orders import stripe_webhook as site_orders_webhook

router = APIRouter(prefix="/launch", tags=["launch"])


@router.post("/webhook")
async def launch_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Launch webhook endpoint - forwards to site_orders Stripe webhook handler.
    This endpoint exists because Stripe is configured to call /api/launch/webhook.
    """
    return await site_orders_webhook(request, stripe_signature, db)
