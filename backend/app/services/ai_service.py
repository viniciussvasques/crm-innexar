"""
AI Service Wrapper
Handles interactions with multiple AI providers (OpenAI, Anthropic, etc.)
using the ConfigService for dynamic credential retrieval.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.config_service import ConfigService
from app.models.configuration import IntegrationType
from app.models.ai_config import AITaskRouting, AIConfig

class AIService:
    def __init__(self, db: Session):
        self.db = db
        self.config_service = ConfigService(db)

    def _get_provider_client(self, config_id: int):
        """
        Factory to get the authenticated client (OpenAI/Anthropic) 
        based on the stored config configuration.
        """
        ai_config = self.db.get(AIConfig, config_id)
        if not ai_config:
            raise ValueError(f"AI Configuration {config_id} not found")
        
        # In a real impl, we would use self.config_service.decrypt_value if api_key was stored encrypted 
        # inside AIConfig.api_key (if we change AIConfig to use encryption).
        # Currently AIConfig structure assumes api_key column.
        # If we migrate AIConfig to use ConfigService's patterns, we would decrypt here.
        # For now assuming AIConfig.api_key might be plain or handled elsewhere, 
        # BUT ConfigService is for IntegrationConfig table.
        
        # If the user wants "separate configurations", we might prefer using IntegrationConfig 
        # or adapting AIConfig to be encrypted. 
        # Let's assume we retrieve the key here.
        
        api_key = ai_config.api_key
        # TODO: Decrypt if we decide to encrypt AIConfig keys
        
        if ai_config.provider == "openai":
            # return OpenAI(api_key=api_key)
            pass
        elif ai_config.provider == "anthropic":
            # return Anthropic(api_key=api_key)
            pass
            
        return None

    def get_routing_for_task(self, task_type: str) -> Optional[AITaskRouting]:
        """Get routing rules for a specific task"""
        return self.db.query(AITaskRouting).filter(AITaskRouting.task_type == task_type).first()

    async def generate(self, task_type: str, prompt: str, context: Dict[str, Any] = None):
        """
        Main entry point for generation.
        1. Checks routing for task_type
        2. Selects provider
        3. Calls provider
        """
        routing = self.get_routing_for_task(task_type)
        if not routing:
            # Fallback to a default system-wide provider or raise error
            raise ValueError(f"No routing defined for task {task_type}")

        # Try primary
        try:
            # client = self._get_provider_client(routing.primary_config_id)
            # return await client.generate(...)
            return {"mock": f"Generated content for {task_type} using primary provider"}
        except Exception as e:
            if routing.fallback_config_id:
                # Try fallback
                # client = self._get_provider_client(routing.fallback_config_id)
                # return await client.generate(...)
                return {"mock": f"Generated content for {task_type} using fallback provider"}
            raise e
