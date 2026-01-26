import stripe
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.system_config import SystemConfig
from app.core.database import AsyncSessionLocal

# Default fallback (from env or hardcoded logic if needed, but we prefer DB)
DEFAULT_STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY")
DEFAULT_STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

class StripeService:
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self.api_key = None
        self.webhook_secret = None

    async def _load_config(self):
        """Load Stripe configuration from database."""
        if not self.db:
            # Create a new session if one wasn't provided
            async with AsyncSessionLocal() as session:
                await self._load_from_session(session)
        else:
            await self._load_from_session(self.db)

    async def _load_from_session(self, session: AsyncSession):
        result = await session.execute(
            select(SystemConfig).where(
                SystemConfig.key.in_(["stripe_secret_key", "stripe_webhook_secret", "stripe_enabled"])
            )
        )
        configs = {row.key: row for row in result.scalars().all()}
        
        self.api_key = configs.get("stripe_secret_key").value if configs.get("stripe_secret_key") else DEFAULT_STRIPE_KEY
        self.webhook_secret = configs.get("stripe_webhook_secret").value if configs.get("stripe_webhook_secret") else DEFAULT_STRIPE_WEBHOOK_SECRET
        
        # Set the key globally for stripe library
        if self.api_key:
            stripe.api_key = self.api_key

    async def create_checkout_session(self, order_data: dict, success_url: str, cancel_url: str):
        """Create a Stripe Checkout Session."""
        await self._load_config()
        
        if not self.api_key:
            raise ValueError("Stripe API Key not configured")

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Innexar Website Launch Service",
                            "description": "Professional Website Design & Development",
                        },
                        "unit_amount": int(order_data.get("total_price", 0) * 100), # Amount in cents
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=order_data.get("customer_email"),
                client_reference_id=str(order_data.get("order_id", "")),
                metadata={
                    "order_id": order_data.get("order_id"),
                    "customer_name": order_data.get("customer_name"),
                }
            )
            return session
        except stripe.error.StripeError as e:
            print(f"Stripe Error: {e}")
            raise e

    async def construct_event(self, payload: bytes, sig_header: str):
        """Construct and verify a Stripe Webhook Event."""
        await self._load_config()
        
        if not self.webhook_secret:
            raise ValueError("Stripe Webhook Secret not configured")

        try:
            # Run blocking crypto operation in threadpool
            from fastapi.concurrency import run_in_threadpool
            event = await run_in_threadpool(
                stripe.Webhook.construct_event,
                payload, sig_header, self.webhook_secret
            )
            return event
        except ValueError as e:
            raise e
        except stripe.error.SignatureVerificationError as e:
            raise e
