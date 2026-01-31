import asyncio
import sys
import os

# Adjust path to find app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import AsyncSessionLocal
from app.models.site_order import SiteOrder
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(SiteOrder))
        orders = result.scalars().all()
        print(f"Total Orders: {len(orders)}")
        for order in orders:
            print(f"ID: {order.id}, Status: {order.status}, Customer: {order.customer_email}, StripeID: {order.stripe_session_id}")

if __name__ == "__main__":
    asyncio.run(main())
