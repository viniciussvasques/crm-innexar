from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import logging

from app.repositories.order_repository import OrderRepository
from app.api.site_customers import create_customer_account
from app.services.email_service import email_service
from app.services.site_generator_service import SiteGeneratorService
from app.models.site_order import SiteOrder, SiteOrderStatus, SiteOnboarding
from app.models.site_customer import SiteCustomer

logger = logging.getLogger(__name__)

class OnboardingService:
    def __init__(self, db: AsyncSession, background_tasks: BackgroundTasks):
        self.db = db
        self.background_tasks = background_tasks
        self.repo = OrderRepository(db)

    async def process_onboarding(self, order_identifier: str, onboarding_data: dict) -> dict:
        """
        Process the onboarding submission.
        - Validates order existence
        - Creates Onboarding record
        - Updates Order status
        - Creates/Links Customer Account (handling duplicates)
        - Triggers AI Generation
        """
        
        # 1. Find Order
        order = await self.repo.find_by_identifier(order_identifier)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
            
        if order.onboarding_completed_at:
             raise HTTPException(status_code=400, detail="Onboarding already completed")

        # 2. Create Onboarding Record
        onboarding = SiteOnboarding(
            order_id=order.id,
            **{k: v for k, v in onboarding_data.model_dump().items() if k != "password"}
        )
        self.db.add(onboarding)
        
        # 3. Update Order Status to GENERATING (not BUILDING) since we're starting generation immediately
        order.status = SiteOrderStatus.GENERATING
        order.onboarding_completed_at = datetime.utcnow()
        order.expected_delivery_date = datetime.utcnow() + timedelta(days=order.delivery_days)
        
        # 4. Handle Customer Account
        await self._handle_customer_account(order, onboarding_data)
        
        await self.db.commit()
        
        # 5. Trigger AI Generation (Background) - AUTOMATIC AND MANDATORY
        try:
            self._trigger_ai_generation(order.id)
            generation_started = True
            logger.info(f"✅ AI generation AUTOMATICALLY triggered for order {order.id} after onboarding completion")
        except Exception as e:
            logger.error(f"❌ CRITICAL: Failed to trigger AI generation for order {order.id}: {e}", exc_info=True)
            # Don't revert status - keep as GENERATING and log the error
            # The auto-start-stuck-orders endpoint will catch this
            generation_started = False
            # Still commit the order status change
            await self.db.commit()
        
        return {
            "message": "Onboarding submitted successfully",
            "order_id": order_identifier,
            "generation_started": generation_started
        }

    async def _handle_customer_account(self, order: SiteOrder, onboarding_data):
        """Creates or links customer account, handling duplicate emails gracefully."""
        
        # Check if customer account already exists for THIS order
        existing_customer = await self.repo.get_customer_by_order_id(order.id)
        
        if existing_customer:
            # Re-submission: Account exists, just resend verification if needed (logic simplified)
            return

        try:
            # Create new account using business email from ONBOARDING (not Stripe)
            customer, temp_password = await create_customer_account(
                db=self.db,
                order_id=order.id,
                email=onboarding_data.business_email, 
                password=onboarding_data.password
            )
            
            # Send verification email
            self.background_tasks.add_task(
                email_service.send_verification_email,
                customer_name=onboarding_data.business_name,
                to_email=customer.email,
                temp_password=temp_password,
                verification_token=customer.verification_token
            )
            
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "EMAIL_ALREADY_EXISTS",
                    "message": "Este e-mail já está cadastrado em outro pedido. Use um email diferente ou faça login.",
                    "field": "email"
                }
            )

    def _trigger_ai_generation(self, order_id: int):
        """Triggers AI generation using Celery task queue."""
        import logging
        from app.tasks.site_generation import generate_site_task
        
        logger = logging.getLogger(__name__)
        
        try:
            # Enqueue Celery task instead of threading
            celery_task = generate_site_task.delay(order_id, resume=True)
            logger.info(f"✅ Enqueued Celery task {celery_task.id} for AI generation of order {order_id}")
            return celery_task
        except Exception as e:
            logger.error(f"❌ Failed to enqueue Celery task for order {order_id}: {e}", exc_info=True)
            raise
