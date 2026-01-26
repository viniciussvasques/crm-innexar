"""
Celery Tasks for Site Generation
"""
import asyncio
import logging
import traceback
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.celery_app import celery_app
from app.services.site_generator_service import SiteGeneratorService

logger = logging.getLogger(__name__)


def _create_isolated_session():
    """
    Creates an isolated database engine and session for this Celery task.
    This prevents "Future attached to different loop" errors by ensuring
    each task has its own engine bound to the current event loop.
    """
    from app.core.config import settings
    
    # Get database URL and ensure it uses asyncpg
    database_url = settings.DATABASE_URL
    if not database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    
    # Create a NEW engine for this event loop
    # This is critical - each asyncio.run() creates a new loop, so we need a new engine
    engine = create_async_engine(
        database_url,
        echo=False,  # Disable echo in Celery to reduce noise
        future=True,
        pool_pre_ping=True,
        pool_reset_on_return='commit',
        # Isolate this engine from the global one
        pool_size=5,
        max_overflow=10
    )
    
    # Create session factory for this engine
    SessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    return SessionLocal, engine


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, name="app.tasks.site_generation.generate_site_task")
def generate_site_task(self, order_id: int, resume: bool = True):
    """
    Celery task to generate a site using AI.
    
    Uses asyncio.run() with an isolated database engine to avoid
    "Future attached to a different loop" errors.
    
    Args:
        order_id: The site order ID
        resume: Whether to resume from existing files
    
    Returns:
        dict: Result with success status and details
    """
    logger.info(f"[Celery] Starting site generation task for order {order_id} (resume={resume})")
    
    async def _generate():
        """Async function that does the actual work"""
        # Create isolated session for this event loop
        SessionLocal, engine = _create_isolated_session()
        
        try:
            async with SessionLocal() as session:
                try:
                    # Ensure we start with a clean session state
                    await session.rollback()
                    
                    service = SiteGeneratorService(session)
                    result = await service.generate_site(order_id, resume=resume)
                    
                    if result and result.get("success"):
                        logger.info(f"[Celery] Site generation completed successfully for order {order_id}")
                        return result
                    else:
                        error_msg = result.get("error", "Unknown error") if result else "No result returned"
                        logger.warning(f"[Celery] Site generation finished with issues for order {order_id}: {error_msg}")
                        return result
                except Exception as e:
                    # Always rollback on error
                    try:
                        await session.rollback()
                    except Exception as rollback_error:
                        logger.warning(f"[Celery] Rollback failed: {rollback_error}")
                    
                    # Use logger.exception for full stack trace
                    logger.exception(f"[Celery] Error during site generation for order {order_id}: %r", e)
                    raise
        finally:
            # Clean up the engine for this event loop
            await engine.dispose()
    
    try:
        # Use asyncio.run() instead of manual loop management
        # This properly creates and manages the event loop
        result = asyncio.run(_generate())
        return result
        
    except Exception as exc:
        # Use logger.exception for full stack trace with context
        logger.exception(f"[Celery] Task failed for order {order_id}, will retry")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
