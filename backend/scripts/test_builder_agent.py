import asyncio
import sys
import os
import logging
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.builder_service import BuilderService
from app.schemas.site_content import SiteContent, ColorPalette, SitePage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_builder_flow():
    logger.info("👷 Testing Builder Agent...")
    
    # 1. Prepare Mock Content
    content = SiteContent(
        business_name="Builder Test Corp",
        tagline="We Build Things Fast",
        colors=ColorPalette(
            primary="#0070f3", 
            secondary="#000000", 
            accent="#ff0000", 
            background="#ffffff", 
            text="#333333"
        ),
        fonts={"heading": "Inter", "body": "Inter"},
        pages=[],
        footer_text="© 2024",
        contact_phone="555-0199",
        contact_email="builder@test.com"
    )
    
    service = BuilderService()
    # Ensure client is connected
    if not service.container_service.client:
        logger.error("❌ Docker client not available. Test skipped.")
        return

    try:
        logger.info("🚀 Triggering Build (Order ID: 1001)...")
        # This will spawn a real container and run real commands
        # It might take a few minutes.
        result = await service.build_site(order_id=1001, content=content)
        
        logger.info(f"🏁 Build Result: {result['success']}")
        logger.info(f"   Container ID: {result.get('container_id')}")
        
        if result['success']:
            logger.info("✅ Builder Flow Success!")
        else:
            logger.error("❌ Builder Flow Failed.")
            logger.error(f"Output: {result.get('build_output')}")
            
    except Exception as e:
        logger.error(f"❌ Test Exception: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_builder_flow())
