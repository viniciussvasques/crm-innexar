from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime

from app.models.site_order import SiteOrder
from app.models.site_customer import SiteCustomer

class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, order_id: int) -> Optional[SiteOrder]:
        """Get order by numeric ID"""
        return await self.db.get(SiteOrder, order_id)

    async def get_by_session_id(self, session_id: str) -> Optional[SiteOrder]:
        """Get order by Stripe Session ID"""
        result = await self.db.execute(
            select(SiteOrder).where(SiteOrder.stripe_session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def find_by_identifier(self, identifier: str) -> Optional[SiteOrder]:
        """
        Smart lookup by either full session ID, short ID (last 8 chars), or numeric ID.
        This optimized query handles all cases.
        """
        # 1. Exact match (fastest)
        order = await self.get_by_session_id(identifier)
        if order:
            return order

        # 2. Short ID match (last 8 chars) - Optimized with functional index logic if possible
        # For now, we use the substring logic which is what was there, but encapsulated
        result = await self.db.execute(
            select(SiteOrder).where(
                func.upper(func.right(SiteOrder.stripe_session_id, 8)) == identifier.upper()
            )
        )
        order = result.scalar_one_or_none()
        if order:
            return order

        # 3. Numeric ID (fallback)
        if identifier.isdigit():
            return await self.get_by_id(int(identifier))
            
        return None

    async def get_customer_by_order_id(self, order_id: int) -> Optional[SiteCustomer]:
        """Get customer account associated with an order"""
        result = await self.db.execute(
            select(SiteCustomer).where(SiteCustomer.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_onboarding(self, order_id: int) -> Optional['SiteOnboarding']:
        """Get onboarding data for an order"""
        from app.models.site_order import SiteOnboarding
        result = await self.db.execute(
            select(SiteOnboarding).where(SiteOnboarding.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_logs(self, order_id: int) -> List[dict]:
        """Get logs for a specific order"""
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        
        # Use a separate session to avoid conflicts with ongoing operations
        try:
            async with AsyncSessionLocal() as log_session:
                result = await log_session.execute(
                    text("""
                        SELECT id, step, message, status, details, created_at 
                        FROM site_generation_logs 
                        WHERE order_id = :oid 
                        ORDER BY created_at ASC
                    """),
                    {"oid": order_id}
                )
                logs = []
                for row in result:
                    # Handle details which might be JSONB or text
                    details = row.details
                    if details and isinstance(details, str):
                        try:
                            import json
                            details = json.loads(details)
                        except:
                            pass
                    
                    logs.append({
                        "id": row.id,
                        "step": row.step or "",
                        "message": row.message or "",
                        "status": row.status or "info",
                        "details": details,
                        "timestamp": row.created_at.isoformat() if row.created_at else datetime.utcnow().isoformat()
                    })
                return logs
        except Exception as e:
            # Log error but return empty list to avoid breaking the frontend
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error fetching logs for order {order_id}: {e}", exc_info=True)
            return []
