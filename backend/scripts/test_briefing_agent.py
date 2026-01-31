import asyncio
import sys
import os
import logging
from unittest.mock import MagicMock, AsyncMock

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.briefing_service import BriefingService
from app.models.site_order import SiteOrder, SiteOnboarding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_briefing_generation():
    logger.info("🧠 Testing Briefing Agent...")
    
    # Mock DB Session
    mock_db = MagicMock()
    
    # Mock Order & Onboarding
    mock_order = MagicMock(spec=SiteOrder)
    mock_order.id = 999
    
    mock_onboarding = MagicMock(spec=SiteOnboarding)
    mock_onboarding.business_name = "Innexar Pizza"
    mock_onboarding.niche = "Restaurant"
    mock_onboarding.site_description = "The best pizza in Sao Paulo"
    mock_onboarding.services = ["Custom Pizza", "Delivery", "Catering"]
    mock_onboarding.tone = "Friendly"
    mock_onboarding.site_objective = "Sell more pizza"
    mock_onboarding.business_phone = "11999999999"
    mock_onboarding.business_email = "pizza@innexar.com"
    
    mock_order.onboarding = mock_onboarding
    
    # Mock DB Query
    mock_db.query.return_value.get.return_value = mock_order
    
    # Init Service
    service = BriefingService(mock_db)
    
    # Force Mock LLM response to save tokens/time for this test
    # (In real dev, we'd mock the httpx client or use a real key)
    service.call_llm = AsyncMock(return_value=service._get_mock_response())
    
    try:
        logger.info("1️⃣ Generating Briefing...")
        content = await service.generate_briefing(999)
        
        logger.info(f"✅ Generated Briefing for: {content.business_name}")
        logger.info(f"   Tagline: {content.tagline}")
        logger.info(f"   Colors: {content.colors}")
        logger.info(f"   Pages: {[p.path for p in content.pages]}")
        
        assert content.business_name == "Mock Business"
        assert content.contact_phone == "11999999999" # Should be overridden
        
        logger.info("✅ Validation Passed!")
        
    except Exception as e:
        logger.error(f"❌ Test Failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_briefing_generation())
