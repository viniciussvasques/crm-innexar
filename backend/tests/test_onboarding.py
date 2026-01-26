"""
Unit Tests for Onboarding Flow
Tests OrderRepository and OnboardingService with mocked dependencies
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.repositories.order_repository import OrderRepository
from app.services.onboarding_service import OnboardingService
from app.models.site_order import SiteOrder, SiteOrderStatus, SiteOnboarding
from app.models.site_deliverable import SiteDeliverable  # Required for SQLAlchemy relationship resolution


# ============== Fixtures ==============

@pytest.fixture
def mock_db():
    """Mock AsyncSession"""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.get = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_background_tasks():
    """Mock BackgroundTasks"""
    return MagicMock()


@pytest.fixture
def sample_order():
    """Sample SiteOrder for testing"""
    order = MagicMock(spec=SiteOrder)
    order.id = 1
    order.stripe_session_id = "cs_test_abc123xyz890"
    order.customer_email = "test@example.com"
    order.customer_name = "Test User"
    order.status = SiteOrderStatus.PAID
    order.delivery_days = 5
    order.onboarding_completed_at = None
    return order


@pytest.fixture
def sample_onboarding_data():
    """Sample onboarding data"""
    return MagicMock(
        business_name="Test Business",
        business_email="business@example.com",
        business_phone="11999999999",
        has_whatsapp=True,
        niche="construction",
        primary_city="São Paulo",
        state="SP",
        services=["service1", "service2"],
        primary_service="service1",
        password="securepass123",
        model_dump=MagicMock(return_value={
            "business_name": "Test Business",
            "business_email": "business@example.com",
            "business_phone": "11999999999",
            "has_whatsapp": True,
            "niche": "construction",
            "primary_city": "São Paulo",
            "state": "SP",
            "services": ["service1", "service2"],
            "primary_service": "service1",
            "password": "securepass123"
        })
    )


# ============== OrderRepository Tests ==============

class TestOrderRepository:
    
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, mock_db, sample_order):
        """Test finding order by numeric ID"""
        mock_db.get.return_value = sample_order
        
        repo = OrderRepository(mock_db)
        result = await repo.get_by_id(1)
        
        assert result == sample_order
        mock_db.get.assert_called_once_with(SiteOrder, 1)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_db):
        """Test order not found by ID"""
        mock_db.get.return_value = None
        
        repo = OrderRepository(mock_db)
        result = await repo.get_by_id(999)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_session_id_found(self, mock_db, sample_order):
        """Test finding order by Stripe session ID"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_order
        mock_db.execute.return_value = mock_result
        
        repo = OrderRepository(mock_db)
        result = await repo.get_by_session_id("cs_test_abc123xyz890")
        
        assert result == sample_order

    @pytest.mark.asyncio
    async def test_find_by_identifier_exact_match(self, mock_db, sample_order):
        """Test smart lookup with exact session ID"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_order
        mock_db.execute.return_value = mock_result
        
        repo = OrderRepository(mock_db)
        result = await repo.find_by_identifier("cs_test_abc123xyz890")
        
        assert result == sample_order

    @pytest.mark.asyncio
    async def test_find_by_identifier_short_id(self, mock_db, sample_order):
        """Test smart lookup with last 8 chars of session ID"""
        # First call (exact match) returns None
        # Second call (short ID) returns the order
        mock_result_none = MagicMock()
        mock_result_none.scalar_one_or_none.return_value = None
        
        mock_result_found = MagicMock()
        mock_result_found.scalar_one_or_none.return_value = sample_order
        
        mock_db.execute.side_effect = [mock_result_none, mock_result_found]
        
        repo = OrderRepository(mock_db)
        result = await repo.find_by_identifier("23xyz890")
        
        assert result == sample_order
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_find_by_identifier_numeric_fallback(self, mock_db, sample_order):
        """Test smart lookup falling back to numeric ID"""
        mock_result_none = MagicMock()
        mock_result_none.scalar_one_or_none.return_value = None
        mock_db.execute.side_effect = [mock_result_none, mock_result_none]
        mock_db.get.return_value = sample_order
        
        repo = OrderRepository(mock_db)
        result = await repo.find_by_identifier("123")
        
        assert result == sample_order
        mock_db.get.assert_called_once()


# ============== OnboardingService Tests ==============

class TestOnboardingService:

    @pytest.mark.asyncio
    async def test_process_onboarding_success(self, mock_db, mock_background_tasks, sample_order, sample_onboarding_data):
        """Test successful onboarding submission"""
        # Setup mocks
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_order
        mock_db.execute.return_value = mock_result
        
        with patch('app.services.onboarding_service.create_customer_account') as mock_create_customer:
            mock_customer = MagicMock()
            mock_customer.email = "business@example.com"
            mock_customer.verification_token = "token123"
            mock_create_customer.return_value = (mock_customer, "temppass")
            
            service = OnboardingService(mock_db, mock_background_tasks)
            result = await service.process_onboarding("cs_test_abc123xyz890", sample_onboarding_data)
            
            assert result["message"] == "Onboarding submitted successfully"
            assert result["generation_started"] == True
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_onboarding_order_not_found(self, mock_db, mock_background_tasks, sample_onboarding_data):
        """Test onboarding with non-existent order"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        mock_db.get.return_value = None
        
        service = OnboardingService(mock_db, mock_background_tasks)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.process_onboarding("invalid_order", sample_onboarding_data)
        
        assert exc_info.value.status_code == 404
        assert "Order not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_process_onboarding_already_completed(self, mock_db, mock_background_tasks, sample_order, sample_onboarding_data):
        """Test onboarding when already completed"""
        sample_order.onboarding_completed_at = datetime.utcnow()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_order
        mock_db.execute.return_value = mock_result
        
        service = OnboardingService(mock_db, mock_background_tasks)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.process_onboarding("cs_test_abc123xyz890", sample_onboarding_data)
        
        assert exc_info.value.status_code == 400
        assert "already completed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_handle_customer_account_existing(self, mock_db, mock_background_tasks, sample_order):
        """Test customer account handling when account already exists"""
        mock_customer = MagicMock()
        
        service = OnboardingService(mock_db, mock_background_tasks)
        service.repo.get_customer_by_order_id = AsyncMock(return_value=mock_customer)
        
        # Should not raise, just return
        await service._handle_customer_account(sample_order, MagicMock())

    @pytest.mark.asyncio
    async def test_trigger_ai_generation(self, mock_db, mock_background_tasks):
        """Test AI generation is triggered in background"""
        service = OnboardingService(mock_db, mock_background_tasks)
        service._trigger_ai_generation(1)
        
        mock_background_tasks.add_task.assert_called_once()
