"""
API para gerenciar configurações de IA
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.models.user import User
from app.models.ai_config import AIConfig, AIModelProvider, AIModelStatus
from app.api.dependencies import get_current_user, get_user_role_str
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
import json

router = APIRouter(prefix="/ai-config", tags=["ai-config"])

class AIConfigCreate(BaseModel):
    name: str
    provider: str  # grok, openai, anthropic, ollama, google, mistral, cohere
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: bool = False
    is_default: bool = False
    priority: int = 0
    config: Optional[Dict[str, Any]] = None

class AIConfigUpdate(BaseModel):
    name: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = None
    config: Optional[Dict[str, Any]] = None

class AIConfigResponse(BaseModel):
    id: int
    name: str
    provider: str
    model_name: str
    base_url: Optional[str] = None
    is_active: bool
    is_default: bool
    status: str
    priority: int
    config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    last_tested_at: Optional[datetime] = None
    last_error: Optional[str] = None
    
    class Config:
        from_attributes = True

# Modelos disponíveis por provider
AVAILABLE_MODELS = {
    "grok": [
        {"name": "grok-1", "display": "Grok-1"},
        {"name": "grok-beta", "display": "Grok Beta"},
        {"name": "grok-2", "display": "Grok-2 (se disponível)"}
    ],
    "openai": [
        {"name": "gpt-4o", "display": "GPT-4o"},
        {"name": "gpt-4-turbo", "display": "GPT-4 Turbo"},
        {"name": "gpt-4", "display": "GPT-4"},
        {"name": "gpt-3.5-turbo", "display": "GPT-3.5 Turbo"},
        {"name": "gpt-4o-mini", "display": "GPT-4o Mini"}
    ],
    "anthropic": [
        {"name": "claude-3-5-sonnet-20241022", "display": "Claude 3.5 Sonnet"},
        {"name": "claude-3-opus-20240229", "display": "Claude 3 Opus"},
        {"name": "claude-3-sonnet-20240229", "display": "Claude 3 Sonnet"},
        {"name": "claude-3-haiku-20240307", "display": "Claude 3 Haiku"}
    ],
    "ollama": [
        {"name": "llama3", "display": "Llama 3"},
        {"name": "llama3:70b", "display": "Llama 3 70B"},
        {"name": "mistral", "display": "Mistral"},
        {"name": "mixtral", "display": "Mixtral"},
        {"name": "codellama", "display": "CodeLlama"},
        {"name": "phi", "display": "Phi"},
        {"name": "neural-chat", "display": "Neural Chat"}
    ],
    "google": [
        {"name": "gemini-2.5-flash", "display": "Gemini 2.5 Flash (Recomendado - Rápido)"},
        {"name": "gemini-2.5-pro", "display": "Gemini 2.5 Pro (Mais Poderoso)"},
        {"name": "gemini-2.5-flash-lite", "display": "Gemini 2.5 Flash Lite (Leve)"},
        {"name": "gemini-2.0-flash", "display": "Gemini 2.0 Flash"},
        {"name": "gemini-2.0-flash-001", "display": "Gemini 2.0 Flash 001"},
        {"name": "gemini-2.0-flash-lite", "display": "Gemini 2.0 Flash Lite"},
        {"name": "gemini-2.0-flash-lite-001", "display": "Gemini 2.0 Flash Lite 001"}
    ],
    "mistral": [
        {"name": "mistral-large-latest", "display": "Mistral Large"},
        {"name": "mistral-medium-latest", "display": "Mistral Medium"},
        {"name": "mistral-small-latest", "display": "Mistral Small"}
    ],
    "cohere": [
        {"name": "command", "display": "Command"},
        {"name": "command-light", "display": "Command Light"},
        {"name": "command-r", "display": "Command R"},
        {"name": "command-r-plus", "display": "Command R Plus"}
    ],
    "cloudflare": [
        {"name": "@cf/meta/llama-3.1-8b-instruct", "display": "Llama 3.1 8B Instruct (Recomendado)"},
        {"name": "@cf/meta/llama-3.2-3b-instruct", "display": "Llama 3.2 3B Instruct (Rápido)"},
        {"name": "@cf/meta/llama-3.2-1b-instruct", "display": "Llama 3.2 1B Instruct (Ultra Rápido)"},
        {"name": "@cf/mistral/mistral-7b-instruct-v0.2", "display": "Mistral 7B Instruct v0.2"},
        {"name": "@cf/qwen/qwen1.5-14b-chat-awq", "display": "Qwen 1.5 14B Chat"},
        {"name": "@cf/google/gemma-7b-it-lora", "display": "Gemma 7B IT"},
        {"name": "@hf/thebloke/deepseek-coder-6.7b-instruct-awq", "display": "DeepSeek Coder 6.7B"}
    ]
}

@router.get("/models", response_model=Dict[str, List[Dict[str, str]]])
async def get_available_models(
    current_user: User = Depends(get_current_user)
):
    """Retorna modelos disponíveis por provider"""
    role_str = get_user_role_str(current_user)
    if role_str.lower() != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem acessar")
    
    return AVAILABLE_MODELS

@router.get("/google/list-models")
async def list_google_models(
    api_key: str,
    current_user: User = Depends(get_current_user)
):
    """Lista modelos disponíveis do Google Gemini dinamicamente - apenas admin"""
    role_str = get_user_role_str(current_user)
    if role_str.lower() != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem acessar")
    
    if not api_key or not api_key.strip().startswith("AIza"):
        raise HTTPException(status_code=400, detail="API key inválida")
    
    api_key = api_key.strip()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://generativelanguage.googleapis.com/v1/models",
                params={"key": api_key},
                timeout=10.0
            )
            
            if response.status_code != 200:
                error_text = response.text[:500] if hasattr(response, 'text') else str(response.status_code)
                try:
                    error_data = response.json()
                    error_detail = error_data.get("error", {}).get("message", error_text)
                except:
                    error_detail = error_text
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Erro ao listar modelos: {error_detail}"
                )
            
            data = response.json()
            models = []
            
            if "models" in data:
                for model in data["models"]:
                    name = model.get("name", "")
                    # Filtrar apenas modelos que suportam generateContent
                    supported_methods = model.get("supportedGenerationMethods", [])
                    if "generateContent" in supported_methods:
                        display_name = model.get("displayName", name)
                        # Remover prefixo "models/" se existir
                        if name.startswith("models/"):
                            name = name.replace("models/", "")
                        models.append({
                            "name": name,
                            "display": display_name
                        })
            
            return {"models": models}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar modelos: {str(e)}")

@router.get("/", response_model=List[AIConfigResponse])
async def list_ai_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todas as configurações de IA - apenas admin"""
    role_str = get_user_role_str(current_user)
    if role_str.lower() != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem acessar")
    
    result = await db.execute(select(AIConfig).order_by(AIConfig.priority.desc(), AIConfig.created_at.desc()))
    configs = result.scalars().all()
    
    return [
        AIConfigResponse(
            id=c.id,
            name=c.name,
            provider=c.provider,
            model_name=c.model_name,
            base_url=c.base_url,
            is_active=c.is_active,
            is_default=c.is_default,
            status=c.status,
            priority=c.priority,
            config=c.config,
            created_at=c.created_at,
            updated_at=c.updated_at,
            last_tested_at=c.last_tested_at,
            last_error=c.last_error
        )
        for c in configs
    ]

@router.post("/", response_model=AIConfigResponse)
async def create_ai_config(
    config_data: AIConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cria nova configuração de IA - apenas admin"""
    role_str = get_user_role_str(current_user)
    if role_str.lower() != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar configurações")
    
    # Se for marcado como padrão, desmarcar outros
    if config_data.is_default:
        result = await db.execute(select(AIConfig).where(AIConfig.is_default == True))
        existing_defaults = result.scalars().all()
        for default in existing_defaults:
            default.is_default = False
    
    config = AIConfig(
        name=config_data.name,
        provider=config_data.provider,
        model_name=config_data.model_name,
        api_key=config_data.api_key,
        base_url=config_data.base_url,
        is_active=config_data.is_active,
        is_default=config_data.is_default,
        priority=config_data.priority,
        config=config_data.config,
        created_by_id=current_user.id,
        status=AIModelStatus.INACTIVE.value
    )
    
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    return AIConfigResponse(
        id=config.id,
        name=config.name,
        provider=config.provider,
        model_name=config.model_name,
        base_url=config.base_url,
        is_active=config.is_active,
        is_default=config.is_default,
        status=config.status,
        priority=config.priority,
        config=config.config,
        created_at=config.created_at,
        updated_at=config.updated_at,
        last_tested_at=config.last_tested_at,
        last_error=config.last_error
    )

@router.put("/{config_id}", response_model=AIConfigResponse)
async def update_ai_config(
    config_id: int,
    config_data: AIConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza configuração de IA - apenas admin"""
    role_str = get_user_role_str(current_user)
    if role_str.lower() != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem atualizar configurações")
    
    result = await db.execute(select(AIConfig).where(AIConfig.id == config_id))
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    # Se for marcado como padrão, desmarcar outros
    if config_data.is_default is True:
        result = await db.execute(select(AIConfig).where(and_(AIConfig.is_default == True, AIConfig.id != config_id)))
        existing_defaults = result.scalars().all()
        for default in existing_defaults:
            default.is_default = False
    
    update_data = config_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    
    config.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(config)
    
    return AIConfigResponse(
        id=config.id,
        name=config.name,
        provider=config.provider,
        model_name=config.model_name,
        base_url=config.base_url,
        is_active=config.is_active,
        is_default=config.is_default,
        status=config.status,
        priority=config.priority,
        config=config.config,
        created_at=config.created_at,
        updated_at=config.updated_at,
        last_tested_at=config.last_tested_at,
        last_error=config.last_error
    )

@router.delete("/{config_id}")
async def delete_ai_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deleta configuração de IA - apenas admin"""
    role_str = get_user_role_str(current_user)
    if role_str.lower() != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem deletar configurações")
    
    result = await db.execute(select(AIConfig).where(AIConfig.id == config_id))
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    await db.delete(config)
    await db.commit()
    
    return {"message": "Configuração deletada com sucesso"}

@router.post("/{config_id}/test")
async def test_ai_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Testa uma configuração de IA - apenas admin"""
    role_str = get_user_role_str(current_user)
    if role_str.lower() != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem testar configurações")
    
    result = await db.execute(select(AIConfig).where(AIConfig.id == config_id))
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    if not config.api_key and config.provider != "ollama":
        raise HTTPException(status_code=400, detail="API key é necessária para este provider")
    
    try:
        # Testar conexão baseado no provider
        test_result = await _test_provider_connection(config)
        
        config.last_tested_at = datetime.utcnow()
        config.status = AIModelStatus.ACTIVE.value if test_result["success"] else AIModelStatus.ERROR.value
        config.last_error = None if test_result["success"] else test_result.get("error", "Erro desconhecido")
        
        await db.commit()
        
        return test_result
        
    except Exception as e:
        config.last_tested_at = datetime.utcnow()
        config.status = AIModelStatus.ERROR.value
        config.last_error = str(e)
        await db.commit()
        
        return {
            "success": False,
            "error": str(e)
        }

async def _test_provider_connection(config: AIConfig) -> Dict[str, Any]:
    """Testa conexão com o provider"""
    test_prompt = "Teste de conexão. Responda apenas 'OK'."
    
    try:
        if config.provider == "grok":
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {config.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": config.model_name,
                        "messages": [{"role": "user", "content": test_prompt}],
                        "max_tokens": 10
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Conexão bem-sucedida"}
                else:
                    return {"success": False, "error": f"Status {response.status_code}: {response.text[:200]}"}
        
        elif config.provider == "openai":
            base_url = config.base_url or "https://api.openai.com/v1"
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {config.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": config.model_name,
                        "messages": [{"role": "user", "content": test_prompt}],
                        "max_tokens": 10
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Conexão bem-sucedida"}
                else:
                    return {"success": False, "error": f"Status {response.status_code}: {response.text[:200]}"}
        
        elif config.provider == "anthropic":
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": config.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": config.model_name,
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": test_prompt}]
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Conexão bem-sucedida"}
                else:
                    return {"success": False, "error": f"Status {response.status_code}: {response.text[:200]}"}
        
        elif config.provider == "ollama":
            base_url = config.base_url or "http://localhost:11434"
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/api/generate",
                    json={
                        "model": config.model_name,
                        "prompt": test_prompt,
                        "stream": False
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Conexão bem-sucedida"}
                else:
                    return {"success": False, "error": f"Status {response.status_code}: {response.text[:200]}"}
        
        elif config.provider == "google":
            if not config.api_key:
                return {"success": False, "error": "API key é necessária para Google Gemini"}
            
            # Limpar API key (remover espaços)
            api_key = config.api_key.strip()
            
            # Validar formato básico
            if not api_key.startswith("AIza"):
                return {
                    "success": False, 
                    "error": "API key inválida. A chave do Google Gemini deve começar com 'AIza'. Verifique se copiou a chave completa."
                }
            
            async with httpx.AsyncClient() as client:
                try:
                    # Primeiro, verificar se o modelo existe listando os modelos disponíveis
                    list_response = await client.get(
                        "https://generativelanguage.googleapis.com/v1/models",
                        params={"key": api_key},
                        timeout=5.0
                    )
                    
                    available_models = []
                    if list_response.status_code == 200:
                        list_data = list_response.json()
                        if "models" in list_data:
                            for model in list_data["models"]:
                                model_name_clean = model.get("name", "").replace("models/", "")
                                supported_methods = model.get("supportedGenerationMethods", [])
                                if "generateContent" in supported_methods:
                                    available_models.append(model_name_clean)
                    
                    # Adicionar prefixo "models/" se não tiver
                    model_name = config.model_name
                    if not model_name.startswith("models/"):
                        model_name = f"models/{model_name}"
                    
                    # Verificar se o modelo está disponível
                    model_name_clean = config.model_name
                    if available_models and model_name_clean not in available_models:
                        # Tentar encontrar modelo similar
                        similar = [m for m in available_models if model_name_clean.lower() in m.lower() or m.lower() in model_name_clean.lower()]
                        if not similar:
                            error_msg = f"Modelo '{config.model_name}' não encontrado.\n\nModelos disponíveis:\n{', '.join(available_models[:10])}"
                            if len(available_models) > 10:
                                error_msg += f"\n... e mais {len(available_models) - 10} modelos"
                            return {"success": False, "error": error_msg}
                    
                    response = await client.post(
                        f"https://generativelanguage.googleapis.com/v1/{model_name}:generateContent",
                        params={"key": api_key},
                        json={
                            "contents": [{
                                "parts": [{"text": test_prompt}]
                            }],
                            "generationConfig": {
                                "maxOutputTokens": 10
                            }
                        },
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if "candidates" in data and len(data["candidates"]) > 0:
                            return {"success": True, "message": "Conexão bem-sucedida"}
                        else:
                            return {"success": False, "error": "Resposta inválida da API"}
                    else:
                        error_text = response.text[:200] if hasattr(response, 'text') else str(response.status_code)
                        try:
                            error_data = response.json()
                            error_detail = error_data.get("error", {}).get("message", error_text)
                            # Mensagem mais amigável para erro de API key
                            if "API key" in error_detail or "api key" in error_detail.lower():
                                error_detail = "API key inválida. Verifique:\n1. Se a chave está completa (começa com 'AIza')\n2. Se não há espaços extras\n3. Se a API 'Generative Language API' está ativada no Google Cloud\n4. Se a chave não tem restrições que bloqueiam o uso"
                            elif "not found" in error_detail.lower() or "404" in error_text:
                                if available_models:
                                    error_detail = f"Modelo não encontrado.\n\nModelos disponíveis:\n{', '.join(available_models[:10])}"
                                    if len(available_models) > 10:
                                        error_detail += f"\n... e mais {len(available_models) - 10} modelos"
                                else:
                                    error_detail = "Modelo não encontrado. Use o botão 'Buscar modelos disponíveis' para ver os modelos suportados."
                        except:
                            error_detail = error_text
                        return {"success": False, "error": f"Status {response.status_code}: {error_detail}"}
                except httpx.TimeoutException:
                    return {"success": False, "error": "Timeout ao conectar com o provider"}
                except Exception as e:
                    return {"success": False, "error": str(e)}
        
        elif config.provider == "mistral":
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {config.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": config.model_name,
                        "messages": [{"role": "user", "content": test_prompt}],
                        "max_tokens": 10
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Conexão bem-sucedida"}
                else:
                    return {"success": False, "error": f"Status {response.status_code}: {response.text[:200]}"}
        
        elif config.provider == "cohere":
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.cohere.ai/v1/generate",
                    headers={
                        "Authorization": f"Bearer {config.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": config.model_name,
                        "prompt": test_prompt,
                        "max_tokens": 10
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Conexão bem-sucedida"}
                else:
                    return {"success": False, "error": f"Status {response.status_code}: {response.text[:200]}"}
        
        elif config.provider == "cloudflare":
            # Cloudflare Workers AI requires account_id in base_url
            if not config.base_url:
                return {"success": False, "error": "Base URL é necessária. Formato: https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run"}
            
            if not config.api_key:
                return {"success": False, "error": "API Token é necessário"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config.base_url}/{config.model_name}",
                    headers={
                        "Authorization": f"Bearer {config.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messages": [{"role": "user", "content": test_prompt}],
                        "max_tokens": 10
                    },
                    timeout=15.0
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Conexão bem-sucedida com Cloudflare Workers AI"}
                else:
                    error_detail = response.text[:300]
                    try:
                        error_data = response.json()
                        if "errors" in error_data:
                            error_detail = str(error_data["errors"])
                    except:
                        pass
                    return {"success": False, "error": f"Status {response.status_code}: {error_detail}"}
        
        else:
            return {"success": False, "error": f"Provider '{config.provider}' não suportado"}
    
    except httpx.TimeoutException:
        return {"success": False, "error": "Timeout ao conectar com o provider"}
    except Exception as e:
        return {"success": False, "error": str(e)}

