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
        # Filter out 'password' and 'locale' as they're not part of SiteOnboarding model
        onboarding_data_dict = {k: v for k, v in onboarding_data.model_dump().items() if k not in ["password", "locale"]}
        
        # Handle domain fields - set desired_domain for backward compatibility
        if onboarding_data.has_existing_domain and onboarding_data.existing_domain:
            onboarding_data_dict["desired_domain"] = onboarding_data.existing_domain
        elif onboarding_data.domain_to_purchase:
            onboarding_data_dict["desired_domain"] = onboarding_data.domain_to_purchase
        
        onboarding = SiteOnboarding(
            order_id=order.id,
            **onboarding_data_dict
        )
        self.db.add(onboarding)
        
        # 2.5. Check domain availability if domain_to_purchase is provided (but not purchased yet)
        if onboarding_data.domain_to_purchase and not onboarding_data_dict.get("domain_purchased"):
            await self._check_domain_and_notify(order, onboarding_data.domain_to_purchase)
        
        # 3. Update Order Status to BRIEFING (manual workflow - equipe recebe e constrói)
        # The custom TypeDecorator will ensure the enum value ("briefing") is used, not the name
        order.status = SiteOrderStatus.BRIEFING
        order.onboarding_completed_at = datetime.utcnow()
        order.expected_delivery_date = datetime.utcnow() + timedelta(days=order.delivery_days)
        
        # 4. Handle Customer Account
        await self._handle_customer_account(order, onboarding_data)
        
        await self.db.commit()
        
        # 5. Manual workflow - NO automatic generation
        # Equipe recebe o briefing e constrói manualmente
        logger.info(f"✅ Onboarding completed for order {order.id}. Status set to BRIEFING (manual workflow)")
        
        return {
            "message": "Onboarding submitted successfully",
            "order_id": order_identifier,
            "status": "briefing",
            "workflow": "manual"
        }

    async def _handle_customer_account(self, order: SiteOrder, onboarding_data):
        """Creates or links customer account, handling duplicate emails gracefully."""
        
        # Check if customer account already exists for THIS order
        existing_customer = await self.repo.get_customer_by_order_id(order.id)
        
        if existing_customer:
            # Re-submission: Account exists, just resend verification if needed (logic simplified)
            return
        
        # Determine preferred locale from onboarding data (fallback to 'en')
        preferred_locale = getattr(onboarding_data, "locale", None) or "en"
        preferred_locale = preferred_locale.split("-")[0]
        
        try:
            # Create new account using business email from ONBOARDING (not Stripe)
            customer, temp_password = await create_customer_account(
                db=self.db,
                order_id=order.id,
                email=onboarding_data.business_email,
                password=onboarding_data.password,
                locale=preferred_locale,
            )
            
            # Send verification email in the customer's locale
            self.background_tasks.add_task(
                email_service.send_verification_email,
                customer_name=onboarding_data.business_name,
                to_email=customer.email,
                temp_password=temp_password,
                verification_token=customer.verification_token,
                locale=preferred_locale,
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

    async def _check_domain_and_notify(self, order: SiteOrder, domain: str):
        """Check domain availability via Dynadot and notify admins."""
        try:
            from app.services.dynadot_service import DynadotService
            from app.api.notifications import notify_all_admins
            
            dynadot_service = DynadotService(self.db)
            result = await dynadot_service.check_domain_availability(domain)
            
            # Create notification for admins
            if result.get("available"):
                price = result.get("price", 0)
                is_free = result.get("is_free", False)
                price_msg = "GRÁTIS" if is_free else f"${price:.2f}"
                
                await notify_all_admins(
                    self.db,
                    title=f"Domínio Disponível - Pedido #{order.id}",
                    message=f"Domínio {domain} está disponível por {price_msg}\nCliente: {order.customer_name}",
                    notification_type="success" if is_free else "info",
                    related_entity_type="site_order",
                    related_entity_id=order.id
                )
            else:
                await notify_all_admins(
                    self.db,
                    title=f"Domínio Indisponível - Pedido #{order.id}",
                    message=f"Domínio {domain} não está disponível\nCliente: {order.customer_name}\nErro: {result.get('error', 'Domínio já registrado')}",
                    notification_type="warning",
                    related_entity_type="site_order",
                    related_entity_id=order.id
                )
        except Exception as e:
            logger.error(f"Error checking domain {domain} for order {order.id}: {e}")
            # Don't fail onboarding if domain check fails
            try:
                from app.api.notifications import notify_all_admins
                await notify_all_admins(
                    self.db,
                    title=f"Erro ao Verificar Domínio - Pedido #{order.id}",
                    message=f"Erro ao verificar domínio {domain}: {str(e)}",
                    notification_type="error",
                    related_entity_type="site_order",
                    related_entity_id=order.id
                )
            except:
                pass  # If notification fails too, just log it
    
    # Removed _trigger_ai_generation - manual workflow doesn't auto-generate
