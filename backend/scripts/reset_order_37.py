import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import AsyncSessionLocal
from app.models.site_order import SiteOrder, SiteOrderStatus
from sqlalchemy import select, update

async def reset_order_37():
    async with AsyncSessionLocal() as session:
        # Check current status
        stmt = select(SiteOrder).where(SiteOrder.id == 37)
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()
        
        if order:
            print(f"Current status: {order.status}")
            # Reset to GENERATING (which will trigger generation)
            order.status = SiteOrderStatus.GENERATING
            await session.commit()
            print("Reset order 37 status to PENDING")
        else:
            print("Order 37 not found")

if __name__ == "__main__":
    asyncio.run(reset_order_37())
