"""
Celery Application Configuration
"""
import os

# Try to import Celery, but don't fail if not available (for backend that doesn't need it)
try:
    from celery import Celery
    from app.core.config import settings
    
    # Redis URL from environment or default
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # Create Celery app
    celery_app = Celery(
        "innexar_crm",
        broker=redis_url,
        backend=redis_url,
        include=["app.tasks.site_generation", "app.tasks.auto_start_stuck_orders"]
    )
except ImportError:
    # Celery not installed - this is OK for backend that only enqueues
    celery_app = None

# Celery configuration (only if celery_app is available)
if celery_app:
    celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Timeout settings
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit (warning)
    
    # Result expiration
    result_expires=86400,  # 24 hours
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time for AI jobs
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks to prevent memory leaks
    
    # Queue routing
    task_routes={
        "app.tasks.site_generation.*": {"queue": "site_generation"},
    },
    
    # Task default settings
    task_default_queue="site_generation",
    task_default_exchange="site_generation",
    task_default_routing_key="site_generation",
    
    # Periodic task schedule (Celery Beat)
    beat_schedule={
        'auto-start-stuck-orders': {
            'task': 'app.tasks.auto_start_stuck_orders.check_and_start_stuck_orders',
            'schedule': 120.0,  # Run every 2 minutes
        },
    },
    )

if __name__ == "__main__":
    if celery_app:
        celery_app.start()
