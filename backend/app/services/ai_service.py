"""
AI Service Wrapper
Handles interactions with multiple AI providers (OpenAI, Anthropic, etc.)
using dynamic configuration and task routing.
"""
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ai_config import AITaskRouting, AIConfig
import httpx
import json
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_routing_for_task(self, task_type: str) -> Optional[AITaskRouting]:
        """Get routing rules for a specific task"""
        result = await self.db.execute(select(AITaskRouting).where(AITaskRouting.task_type == task_type))
        return result.scalar_one_or_none()

    async def _get_config(self, config_id: int) -> Optional[AIConfig]:
        return await self.db.get(AIConfig, config_id)

    async def generate(self, task_type: str, prompt: str, system_instruction: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main entry point for generation.
        1. Checks routing for task_type
        2. Selects provider
        3. Calls provider
        """
        routing = await self.get_routing_for_task(task_type)
        if not routing:
            raise ValueError(f"No routing rules defined for task: {task_type}")

        # Try primary
        try:
            return await self._call_provider(routing.primary_config_id, prompt, system_instruction, routing.temperature)
        except Exception as e:
            logger.error(f"Primary provider failed for {task_type}: {e}")
            if routing.fallback_config_id:
                logger.info(f"Retrying with fallback provider for {task_type}")
                return await self._call_provider(routing.fallback_config_id, prompt, system_instruction, routing.temperature)
            raise e

    async def _call_provider(self, config_id: int, prompt: str, system: str, temperature: float) -> Dict[str, Any]:
        """Dispatches the call to the appropriate provider logic."""
        config = await self._get_config(config_id)
        if not config:
            raise ValueError(f"AI Config {config_id} not found")

        if config.provider == "openai":
            return await self._call_openai(config, prompt, system, temperature)
        elif config.provider == "anthropic":
            return await self._call_anthropic(config, prompt, system, temperature)
        elif config.provider == "google":
            return await self._call_google(config, prompt, system, temperature)
        elif config.provider == "grok":
            return await self._call_openai(config, prompt, system, temperature, base_url="https://api.x.ai/v1")
        elif config.provider == "ollama":
            return await self._call_ollama(config, prompt, system, temperature)
        else:
            raise ValueError(f"Provider {config.provider} not implemented in AIService yet.")

    async def _call_openai(self, config, prompt, system, temperature, base_url=None):
        url = (base_url or config.base_url or "https://api.openai.com/v1") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, headers=headers, json={
                "model": config.model_name,
                "messages": messages,
                "temperature": temperature,
                "response_format": {"type": "json_object"} if "json" in (system or "").lower() else None
            })
            resp.raise_for_status()
            data = resp.json()
            return {"content": data["choices"][0]["message"]["content"]}

    async def _call_anthropic(self, config, prompt, system, temperature):
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, headers=headers, json={
                "model": config.model_name,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": 4096
            })
            resp.raise_for_status()
            data = resp.json()
            return {"content": data["content"][0]["text"]}

    async def _call_google(self, config, prompt, system, temperature):
        # Gemini 1.5 style
        api_key = config.api_key
        url = f"https://generativelanguage.googleapis.com/v1/models/{config.model_name}:generateContent?key={api_key}"
        
        contents = []
        if system:
             # Gemini doesn't strictly have "system" role in the same way, but we can prepend
             contents.append({"role": "user", "parts": [{"text": f"System Instruction: {system}"}]})
             contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json={
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "responseMimeType": "application/json"
                }
            })
            resp.raise_for_status()
            data = resp.json()
            return {"content": data["candidates"][0]["content"]["parts"][0]["text"]}

    async def _call_ollama(self, config, prompt, system, temperature):
         url = (config.base_url or "http://localhost:11434") + "/api/generate"
         async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json={
                "model": config.model_name,
                "system": system,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature
                },
                "format": "json"
            })
            resp.raise_for_status()
            data = resp.json()
            return {"content": data["response"]}
