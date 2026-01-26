"""
Periodic task to automatically start generation for stuck orders
"""
import asyncio
import logging
from app.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.site_order import SiteOrder, SiteOrderStatus
from app.tasks.site_generation import generate_site_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.auto_start_stuck_orders.check_and_start_stuck_orders")
def check_and_start_stuck_orders():
    """
    Periodic task that checks for orders stuck in BUILDING with completed onboarding
    and automatically starts generation for them.
    
    This runs every 2 minutes to ensure orders don't get stuck.
    """
    logger.info("[Auto-Start] Checking for stuck orders...")
    
    # Create new event loop for this process
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        async def _check():
            async with AsyncSessionLocal() as db:
                # Find orders that are BUILDING with completed onboarding but not generating
                result = await db.execute(
                    select(SiteOrder)
                    .options(selectinload(SiteOrder.onboarding))
                    .where(SiteOrder.status == SiteOrderStatus.BUILDING)
                    .where(SiteOrder.onboarding_completed_at.isnot(None))
                )
                stuck_orders = result.scalars().all()
                
                if not stuck_orders:
                    logger.info("[Auto-Start] No stuck orders found")
                    return {"found": 0, "started": 0}
                
                logger.info(f"[Auto-Start] Found {len(stuck_orders)} stuck order(s)")
                
                started = []
                errors = []
                
                for order in stuck_orders:
                    if order.onboarding and order.onboarding.is_complete:
                        try:
                            # Update status to GENERATING
                            order.status = SiteOrderStatus.GENERATING
                            order.admin_notes = f"Auto-started by periodic task (was stuck in BUILDING). Original: {order.admin_notes or 'N/A'}"
                            await db.commit()
                            
                            # Start generation
                            celery_task = generate_site_task.delay(order.id, resume=True)
                            started.append({
                                "order_id": order.id,
                                "task_id": celery_task.id,
                                "customer_email": order.customer_email
                            })
                            logger.info(f"[Auto-Start] ✅ Auto-started generation for stuck order {order.id} (task: {celery_task.id})")
                        except Exception as e:
                            errors.append({
                                "order_id": order.id,
                                "error": str(e)
                            })
                            logger.error(f"[Auto-Start] ❌ Failed to auto-start order {order.id}: {e}", exc_info=True)
                            await db.rollback()
                
                result = {
                    "found": len(stuck_orders),
                    "started": len(started),
                    "errors": len(errors),
                    "started_orders": started,
                    "errors_list": errors
                }
                
                if started:
                    logger.info(f"[Auto-Start] ✅ Successfully started {len(started)} stuck order(s)")
                
                return result
        
        result = loop.run_until_complete(_check())
        return result
        
    except Exception as e:
        logger.error(f"[Auto-Start] Error in periodic task: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        loop.close()
