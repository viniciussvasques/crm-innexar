from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.models.user import User
from app.models.ai_config import AIConfig, AIModelStatus
from app.models.ai_chat import AIChatMessage
from app.api.dependencies import get_current_user, get_user_role_str
from pydantic import BaseModel
from typing import Dict, Any, Optional
import httpx
import json
import os
import re
from datetime import datetime

router = APIRouter(prefix="/ai", tags=["ai"])

class AIRequest(BaseModel):
    prompt: str
    context: Optional[Dict[str, Any]] = None
    max_tokens: int = 1000

class GenerateProposalRequest(BaseModel):
    opportunity_id: int
    company_info: str
    requirements: str
    budget: Optional[float] = None

class AnalyzeOpportunityRequest(BaseModel):
    opportunity_data: Dict[str, Any]

class GenerateQuoteRequest(BaseModel):
    project_data: Dict[str, Any]
    requirements: str
    estimated_hours: int

async def get_active_ai_config(db: AsyncSession) -> Optional[AIConfig]:
    """Busca a configuração de IA ativa e padrão"""
    # Primeiro tenta buscar o padrão ativo
    result = await db.execute(
        select(AIConfig).where(
            and_(
                AIConfig.is_default == True,
                AIConfig.is_active == True,
                AIConfig.status == AIModelStatus.ACTIVE.value
            )
        ).order_by(AIConfig.priority.desc())
    )
    config = result.scalar_one_or_none()
    
    # Se não encontrar padrão, busca qualquer ativo
    if not config:
        result = await db.execute(
            select(AIConfig).where(
                and_(
                    AIConfig.is_active == True,
                    AIConfig.status == AIModelStatus.ACTIVE.value
                )
            ).order_by(AIConfig.priority.desc(), AIConfig.is_default.desc())
        )
        config = result.scalar_one_or_none()
    
    return config

async def call_ai_api(prompt: str, max_tokens: int = 1000, db: Optional[AsyncSession] = None, config: Optional[AIConfig] = None) -> str:
    """Chama a API de IA baseado na configuração"""
    # Se não tiver config, buscar do banco
    if not config and db:
        config = await get_active_ai_config(db)
    
    # Fallback para variável de ambiente (compatibilidade)
    if not config:
        api_key = os.getenv("GROK_API_KEY")
        if api_key:
            config = None  # Usar função antiga
            return await _call_grok_api_legacy(prompt, max_tokens, api_key)
        else:
            raise HTTPException(
                status_code=500, 
                detail="Nenhuma configuração de IA ativa encontrada. Acesse 'Configuração IA' no menu admin, crie uma configuração e marque como 'Ativo' e 'Padrão'."
            )
    
    if not config.api_key and config.provider != "ollama":
        raise HTTPException(status_code=500, detail=f"API key não configurada para {config.provider}")
    
    try:
        if config.provider == "grok":
            return await _call_grok_api(prompt, max_tokens, config)
        elif config.provider == "openai":
            return await _call_openai_api(prompt, max_tokens, config)
        elif config.provider == "anthropic":
            return await _call_anthropic_api(prompt, max_tokens, config)
        elif config.provider == "ollama":
            return await _call_ollama_api(prompt, max_tokens, config)
        elif config.provider == "google":
            return await _call_google_api(prompt, max_tokens, config)
        elif config.provider == "mistral":
            return await _call_mistral_api(prompt, max_tokens, config)
        elif config.provider == "cohere":
            return await _call_cohere_api(prompt, max_tokens, config)
        elif config.provider == "cloudflare":
            return await _call_cloudflare_api(prompt, max_tokens, config)
        else:
            raise HTTPException(status_code=500, detail=f"Provider '{config.provider}' não suportado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao chamar API de IA: {str(e)}")

async def _call_grok_api_legacy(prompt: str, max_tokens: int, api_key: str) -> str:
    """Função legada para Grok (compatibilidade)"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-1",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7
            },
            timeout=60.0
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Erro na API do Grok: {response.status_code}")
        data = response.json()
        return data["choices"][0]["message"]["content"]

async def _call_grok_api(prompt: str, max_tokens: int, config: AIConfig) -> str:
    """Chama a API do Grok/xAI"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": config.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7
            },
            timeout=60.0
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Erro na API do Grok: {response.status_code}")
        data = response.json()
        return data["choices"][0]["message"]["content"]

async def _call_openai_api(prompt: str, max_tokens: int, config: AIConfig) -> str:
    """Chama a API do OpenAI"""
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
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7
            },
            timeout=60.0
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Erro na API do OpenAI: {response.status_code}")
        data = response.json()
        return data["choices"][0]["message"]["content"]

async def _call_anthropic_api(prompt: str, max_tokens: int, config: AIConfig) -> str:
    """Chama a API do Anthropic (Claude)"""
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
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=60.0
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Erro na API do Anthropic: {response.status_code}")
        data = response.json()
        return data["content"][0]["text"]

async def _call_ollama_api(prompt: str, max_tokens: int, config: AIConfig) -> str:
    """Chama a API do Ollama (local)"""
    base_url = config.base_url or "http://localhost:11434"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/generate",
                json={
                    "model": config.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens
                    }
                },
                timeout=120.0  # Ollama pode ser mais lento
            )
            
            if response.status_code != 200:
                error_text = response.text[:500] if hasattr(response, 'text') else str(response.status_code)
                try:
                    error_data = response.json()
                    error_detail = error_data.get("error", error_text)
                except:
                    error_detail = error_text
                
                # Mensagens mais específicas para erros comuns
                if response.status_code == 404:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Modelo '{config.model_name}' não encontrado no Ollama. Verifique se o modelo está instalado (use 'ollama list' para ver modelos disponíveis). Erro: {error_detail}"
                    )
                elif response.status_code == 400:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Erro na requisição ao Ollama. Verifique se o modelo '{config.model_name}' está correto. Erro: {error_detail}"
                    )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Erro na API do Ollama ({response.status_code}): {error_detail}"
                    )
            
            data = response.json()
            if "response" not in data:
                raise HTTPException(
                    status_code=500,
                    detail=f"Resposta inválida do Ollama. Verifique se o modelo '{config.model_name}' está funcionando corretamente."
                )
            return data.get("response", "")
    
    except httpx.ConnectError:
        raise HTTPException(
            status_code=500,
            detail=f"Não foi possível conectar ao Ollama em {base_url}. Verifique se o Ollama está rodando e se o túnel está ativo."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=500,
            detail=f"Timeout ao conectar com o Ollama. O modelo pode estar demorando muito para responder ou a conexão está lenta."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao chamar API do Ollama: {str(e)}"
        )

async def _call_google_api(prompt: str, max_tokens: int, config: AIConfig) -> str:
    """Chama a API do Google Gemini"""
    if not config.api_key:
        raise HTTPException(status_code=500, detail="API key do Google Gemini não configurada")
    
    # Limpar API key (remover espaços)
    api_key = config.api_key.strip()
    
    # Validar formato básico da API key do Google
    if not api_key.startswith("AIza"):
        raise HTTPException(
            status_code=500, 
            detail="API key do Google Gemini inválida. A chave deve começar com 'AIza'"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            # Usar v1 em vez de v1beta (mais estável)
            # Adicionar prefixo "models/" se não tiver
            model_name = config.model_name
            if not model_name.startswith("models/"):
                model_name = f"models/{model_name}"
            
            url = f"https://generativelanguage.googleapis.com/v1/{model_name}:generateContent"
            
            response = await client.post(
                url,
                params={"key": api_key},
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": 0.7
                    }
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                error_text = response.text[:500] if hasattr(response, 'text') else str(response.status_code)
                try:
                    error_data = response.json()
                    error_detail = error_data.get("error", {}).get("message", error_text)
                except:
                    error_detail = error_text
                raise HTTPException(
                    status_code=500, 
                    detail=f"Erro na API do Google Gemini ({response.status_code}): {error_detail}"
                )
            
            data = response.json()
            
            # Verificar estrutura da resposta
            if "candidates" not in data or len(data["candidates"]) == 0:
                raise HTTPException(
                    status_code=500,
                    detail="Resposta inválida da API do Google Gemini: nenhum candidato encontrado"
                )
            
            candidate = data["candidates"][0]
            if "content" not in candidate:
                raise HTTPException(
                    status_code=500,
                    detail="Resposta inválida da API do Google Gemini: conteúdo não encontrado"
                )
            
            if "parts" not in candidate["content"] or len(candidate["content"]["parts"]) == 0:
                raise HTTPException(
                    status_code=500,
                    detail="Resposta inválida da API do Google Gemini: partes não encontradas"
                )
            
            return candidate["content"]["parts"][0]["text"]
            
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=500, detail="Timeout ao chamar API do Google Gemini")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Erro de conexão com API do Google Gemini: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao chamar Google Gemini API: {str(e)}")

async def _call_mistral_api(prompt: str, max_tokens: int, config: AIConfig) -> str:
    """Chama a API do Mistral AI"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": config.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7
            },
            timeout=60.0
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Erro na API do Mistral: {response.status_code}")
        data = response.json()
        return data["choices"][0]["message"]["content"]

async def _call_cohere_api(prompt: str, max_tokens: int, config: AIConfig) -> str:
    """Chama a API do Cohere"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.cohere.ai/v1/generate",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": config.model_name,
                "prompt": prompt,
                "max_tokens": max_tokens
            },
            timeout=60.0
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Erro na API do Cohere: {response.status_code}")
        data = response.json()
        return data["generations"][0]["text"]

async def _call_cloudflare_api(prompt: str, max_tokens: int, config: AIConfig) -> str:
    """Chama a API do Cloudflare Workers AI"""
    if not config.base_url:
        raise HTTPException(
            status_code=500, 
            detail="Base URL é necessária para Cloudflare. Formato: https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run"
        )
    
    if not config.api_key:
        raise HTTPException(status_code=500, detail="API Token do Cloudflare não configurado")
    
    try:
        # Clean up base_url and model_name to avoid double slashes
        base_url = config.base_url.rstrip('/')
        model_name = config.model_name.lstrip('/')
        
        # Build the full URL
        full_url = f"{base_url}/{model_name}"
        
        # For instruct models, use messages format; for others use prompt
        is_instruct_model = 'instruct' in model_name.lower()
        
        if is_instruct_model:
            request_body = {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens
            }
        else:
            request_body = {
                "prompt": prompt,
                "max_tokens": max_tokens
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                full_url,
                headers={
                    "Authorization": f"Bearer {config.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_body,
                timeout=60.0
            )
            
            if response.status_code != 200:
                error_text = response.text[:500]
                try:
                    error_data = response.json()
                    if "errors" in error_data:
                        error_text = str(error_data["errors"])
                except:
                    pass
                raise HTTPException(
                    status_code=500, 
                    detail=f"Erro na API do Cloudflare ({response.status_code}): {error_text}"
                )
            
            data = response.json()
            
            # Cloudflare Workers AI response format
            if "result" in data:
                result = data["result"]
                if "response" in result:
                    return result["response"]
                elif "content" in result:
                    return result["content"]
                elif isinstance(result, str):
                    return result
            
            # Fallback for different response formats
            raise HTTPException(
                status_code=500,
                detail=f"Formato de resposta inesperado do Cloudflare: {str(data)[:200]}"
            )
    
    except httpx.TimeoutException:
        raise HTTPException(status_code=500, detail="Timeout ao chamar API do Cloudflare Workers AI")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Erro de conexão com Cloudflare: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao chamar Cloudflare API: {str(e)}")

@router.post("/chat")
async def chat_with_ai(
    request: AIRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Chat geral com IA com suporte a ações"""
    try:
        # Adicionar contexto do usuário e ferramentas disponíveis
        tools_description = """
FERRAMENTAS DISPONÍVEIS (você pode executar ações no sistema):

1. CRIAR CONTATO:
   - Quando o usuário pedir para criar/adicionar um contato/cliente
   - Use: create_contact(name, email?, phone?, company?, status?, notes?)
   - Exemplo: "Crie um contato para João Silva, email joao@empresa.com"

2. ATUALIZAR CONTATO:
   - Quando o usuário pedir para editar/atualizar um contato
   - Use: update_contact(contact_id, name?, email?, phone?, company?, status?, notes?)
   - Exemplo: "Atualize o email do contato ID 5 para novo@email.com"

3. CRIAR OPORTUNIDADE:
   - Quando o usuário pedir para criar uma oportunidade/deal
   - Use: create_opportunity(name, contact_id?, contact_name?, value?, stage?, probability?, expected_close_date?, notes?)
   - Exemplo: "Crie uma oportunidade de R$ 50.000 para o contato João Silva"

4. ATUALIZAR OPORTUNIDADE:
   - Quando o usuário pedir para editar/atualizar uma oportunidade
   - Use: update_opportunity(opportunity_id, name?, value?, stage?, probability?, expected_close_date?, notes?)
   - Exemplo: "Mude o estágio da oportunidade 3 para 'proposta'"

5. CRIAR ATIVIDADE:
   - Quando o usuário pedir para criar uma tarefa/lembrete/reunião
   - Use: create_activity(type, subject, contact_id?, opportunity_id?, due_date?, description?)
   - Exemplo: "Crie uma tarefa para ligar para o cliente amanhã"

6. LISTAR CONTATOS:
   - Quando precisar buscar informações sobre contatos
   - Use: list_contacts(search?, limit?)
   - Exemplo: "Liste os contatos que têm 'Silva' no nome"

7. LISTAR OPORTUNIDADES:
   - Quando precisar buscar informações sobre oportunidades
   - Use: list_opportunities(search?, limit?)
   - Exemplo: "Mostre as oportunidades em estágio 'qualificacao'"

INSTRUÇÕES IMPORTANTES:
- Quando o usuário pedir para criar/editar algo, você DEVE responder APENAS com a chamada da função no formato exato:
  create_contact(name="Nome", email="email@exemplo.com")
  create_opportunity(name="Nome", value=50000)
  create_activity(type="task", subject="Assunto")
  list_contacts(search="nome")
  list_opportunities(search="nome")

- NÃO mostre código Python, NÃO explique como fazer, apenas execute a função diretamente
- Se precisar de mais informações, pergunte ao usuário antes de executar
- Após executar, confirme o que foi feito de forma clara e amigável
"""
        
        context_prompt = f"""Você é Helena, uma assistente de CRM inteligente e amigável para a empresa Innexar. 
Seu nome é Helena e você deve sempre se apresentar como Helena.
O usuário atual é {current_user.name} com papel de {get_user_role_str(current_user)}.

{tools_description}

IMPORTANTE: Quando o usuário pedir para criar, editar ou atualizar algo no sistema, você DEVE usar as ferramentas disponíveis.
Responda de forma natural e amigável, mas seja proativo em executar ações quando solicitado.

"""

        if request.context:
            context_prompt += f"Contexto adicional: {json.dumps(request.context, ensure_ascii=False)}\n\n"

        # Adicionar histórico de conversa se disponível
        if request.context and "conversation_history" in request.context:
            history = request.context["conversation_history"]
            if history:
                context_prompt += "Histórico da conversa:\n"
                for msg in history[-5:]:  # Últimas 5 mensagens
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    context_prompt += f"{'Usuário' if role == 'user' else 'Assistente'}: {content}\n"
                context_prompt += "\n"

        full_prompt = context_prompt + f"Usuário: {request.prompt}\n\nAssistente:"

        # Salvar mensagem do usuário
        user_message = AIChatMessage(
            user_id=current_user.id,
            role="user",
            content=request.prompt
        )
        db.add(user_message)
        await db.flush()

        try:
            response = await call_ai_api(full_prompt, request.max_tokens, db)
        except HTTPException as e:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            # Log detalhes do erro para debug
            import traceback
            error_trace = traceback.format_exc()
            print(f"Erro ao chamar API de IA: {str(e)}")
            print(f"Traceback: {error_trace}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao processar requisição com IA: {str(e)}"
            )

        # Detectar e executar ações na resposta da IA
        action_executed = False
        action_result = None
        final_response = response
        
        # Verificar se a resposta contém uma chamada de função
        action_patterns = [
            r'create_contact\s*\([^)]*\)',
            r'update_contact\s*\([^)]*\)',
            r'create_opportunity\s*\([^)]*\)',
            r'update_opportunity\s*\([^)]*\)',
            r'create_activity\s*\([^)]*\)',
            r'list_contacts\s*\([^)]*\)',
            r'list_opportunities\s*\([^)]*\)'
        ]
        
        for pattern in action_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                action_call = match.group(0)
                try:
                    action_result = await _execute_ai_action(action_call, db, current_user)
                    action_executed = True
                    # Substituir a chamada de função pelo resultado
                    final_response = response.replace(action_call, action_result)
                    break
                except Exception as e:
                    print(f"Erro ao executar ação: {str(e)}")
                    action_result = f"Erro ao executar ação: {str(e)}"
                    final_response = response.replace(action_call, action_result)
                    break

        # Salvar resposta da IA
        ai_message = AIChatMessage(
            user_id=current_user.id,
            role="assistant",
            content=final_response,
            message_metadata={
                "action_executed": action_executed,
                "action_result": action_result,
                "original_response": response
            } if action_executed else None
        )
        db.add(ai_message)
        await db.commit()

        return {
            "response": final_response,
            "timestamp": datetime.utcnow().isoformat(),
            "action_executed": action_executed,
            "action_result": action_result
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro no chat com IA: {str(e)}")

async def _execute_ai_action(action_string: str, db: AsyncSession, current_user: User) -> str:
    """Executa uma ação da IA baseada na string gerada pelo modelo"""
    try:
        # Extrair nome da função e argumentos
        match = re.match(r"(\w+)\s*\((.*)\)", action_string)
        if not match:
            return f"Formato de ação inválido: {action_string}"

        func_name = match.group(1)
        args_str = match.group(2)

        # Parsear argumentos
        args = {}
        if args_str:
            # Usar regex para dividir argumentos, considerando strings entre aspas
            arg_pairs = re.findall(r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|(\w+\.?\w*))', args_str)
            for key, val1, val2, val3 in arg_pairs:
                value = val1 or val2 or val3
                # Tentar converter para tipos Python
                if value.lower() == 'true':
                    args[key] = True
                elif value.lower() == 'false':
                    args[key] = False
                elif value.replace('.', '', 1).isdigit():
                    if '.' in value:
                        args[key] = float(value)
                    else:
                        # Keep phone as string
                        if key == 'phone':
                            args[key] = value
                        else:
                            args[key] = int(value)
                else:
                    args[key] = value

        # Importar funções de ação
        from app.api.ai_actions import (
            ai_create_contact, ai_update_contact,
            ai_create_opportunity, ai_update_opportunity,
            ai_create_activity,
            ai_list_contacts, ai_list_opportunities
        )
        from app.api.ai_actions import (
            AICreateContactRequest, AIUpdateContactRequest,
            AICreateOpportunityRequest, AIUpdateOpportunityRequest,
            AICreateActivityRequest
        )

        # Executar ação baseada no nome da função
        if func_name == "create_contact":
            from fastapi import BackgroundTasks
            # Criar BackgroundTasks vazio (não podemos passar do contexto atual)
            # A análise será iniciada no próprio endpoint ai_create_contact
            request = AICreateContactRequest(**args)
            result = await ai_create_contact(request, db, current_user, background_tasks=None)
            return result.message if hasattr(result, 'message') else str(result)
        
        elif func_name == "update_contact":
            request = AIUpdateContactRequest(**args)
            result = await ai_update_contact(request, db, current_user)
            return result.message if hasattr(result, 'message') else str(result)
        
        elif func_name == "create_opportunity":
            request = AICreateOpportunityRequest(**args)
            result = await ai_create_opportunity(request, db, current_user)
            return result.message if hasattr(result, 'message') else str(result)
        
        elif func_name == "update_opportunity":
            request = AIUpdateOpportunityRequest(**args)
            result = await ai_update_opportunity(request, db, current_user)
            return result.message if hasattr(result, 'message') else str(result)
        
        elif func_name == "create_activity":
            request = AICreateActivityRequest(**args)
            result = await ai_create_activity(request, db, current_user)
            return result.message if hasattr(result, 'message') else str(result)
        
        elif func_name == "list_contacts":
            result = await ai_list_contacts(
                db=db,
                current_user=current_user,
                search=args.get("search"),
                limit=args.get("limit", 10)
            )
            if result.get("contacts"):
                contacts_str = "\n".join([f"- {c['name']} ({c['email'] or 'sem email'})" for c in result["contacts"]])
                return f"Contatos encontrados:\n{contacts_str}"
            return "Nenhum contato encontrado."
        
        elif func_name == "list_opportunities":
            result = await ai_list_opportunities(
                db=db,
                current_user=current_user,
                search=args.get("search"),
                limit=args.get("limit", 10)
            )
            if result.get("opportunities"):
                opps_str = "\n".join([f"- {o['name']} (R$ {o['value'] or 0:.2f}, {o['stage']})" for o in result["opportunities"]])
                return f"Oportunidades encontradas:\n{opps_str}"
            return "Nenhuma oportunidade encontrada."
        
        else:
            return f"Ação '{func_name}' não reconhecida."

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Erro ao executar ação: {error_trace}")
        return f"Erro ao executar ação: {str(e)}"

def _detect_suggested_actions(user_prompt: str, ai_response: str) -> list:
    """Detecta ações sugeridas na resposta da IA"""
    actions = []
    prompt_lower = user_prompt.lower()
    
    # Detectar intenções de criar contato
    if any(word in prompt_lower for word in ["criar contato", "adicionar contato", "novo cliente", "cadastrar contato"]):
        actions.append({
            "type": "create_contact",
            "description": "Criar um novo contato no sistema"
        })
    
    # Detectar intenções de criar oportunidade
    if any(word in prompt_lower for word in ["criar oportunidade", "nova oportunidade", "criar deal", "nova venda"]):
        actions.append({
            "type": "create_opportunity",
            "description": "Criar uma nova oportunidade"
        })
    
    # Detectar intenções de criar atividade
    if any(word in prompt_lower for word in ["criar tarefa", "lembrar", "agendar", "criar atividade"]):
        actions.append({
            "type": "create_activity",
            "description": "Criar uma nova atividade/tarefa"
        })
    
    return actions

@router.post("/generate-proposal")
async def generate_proposal(
    request: GenerateProposalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Gera proposta comercial usando IA"""
    try:
        prompt = f"""
        Você é um especialista em vendas e propostas comerciais para a Innexar, empresa de desenvolvimento de software.

        Crie uma proposta comercial profissional baseada nas seguintes informações:

        EMPRESA DO CLIENTE: {request.company_info}

        REQUISITOS DO PROJETO: {request.requirements}

        ORÇAMENTO ESTIMADO: {f"R$ {request.budget:,.2f}" if request.budget else "A definir"}

        INSTRUÇÕES:
        1. Estrutura profissional com introdução, escopo, benefícios, timeline e preços
        2. Destaque os diferenciais da Innexar
        3. Seja persuasivo mas realista
        4. Use linguagem profissional em português
        5. Inclua seções claras e objetivas
        6. Termine com chamada para ação

        FORMATO ESPERADO:
        - Título atrativo
        - Introdução personalizada
        - Escopo detalhado
        - Benefícios e ROI
        - Timeline estimada
        - Investimento
        - Próximos passos
        """

        response = await call_ai_api(prompt, 2000, db)

        return {
            "proposal": response,
            "generated_at": datetime.utcnow().isoformat(),
            "opportunity_id": request.opportunity_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar proposta: {str(e)}")

@router.post("/analyze-opportunity")
async def analyze_opportunity(
    request: AnalyzeOpportunityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Análise de oportunidade usando IA"""
    try:
        opp_data = request.opportunity_data

        prompt = f"""
        Você é um analista de vendas experiente. Analise esta oportunidade e forneça insights estratégicos.

        DADOS DA OPORTUNIDADE:
        {json.dumps(opp_data, ensure_ascii=False, indent=2)}

        FORNEÇA:
        1. Avaliação da qualidade do lead (Alta/Média/Baixa)
        2. Pontos fortes da oportunidade
        3. Riscos identificados
        4. Estratégia recomendada
        5. Probabilidade de fechamento estimada
        6. Próximos passos sugeridos

        Seja objetivo e forneça recomendações acionáveis.
        """

        analysis = await call_ai_api(prompt, 1500, db)

        return {
            "analysis": analysis,
            "opportunity_data": opp_data,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")

@router.post("/generate-quote")
async def generate_quote(
    request: GenerateQuoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Gera orçamento técnico usando IA"""
    try:
        prompt = f"""
        Você é um gerente de projetos experiente da Innexar. Crie um orçamento técnico detalhado.

        DADOS DO PROJETO:
        {json.dumps(request.project_data, ensure_ascii=False, indent=2)}

        REQUISITOS TÉCNICOS:
        {request.requirements}

        HORAS ESTIMADAS: {request.estimated_hours}

        INSTRUÇÕES:
        1. Quebre o projeto em fases/módulos
        2. Estime tempo realista para cada parte
        3. Considere complexidade e tecnologias
        4. Inclua margens para imprevistos
        5. Forneça justificativa técnica
        6. Sugira tecnologias apropriadas

        FORMATO:
        - Resumo executivo
        - Breakdown detalhado por fase
        - Tecnologias recomendadas
        - Timeline estimada
        - Custos detalhados
        - Riscos e mitigações
        """

        quote = await call_ai_api(prompt, 2000, db)

        return {
            "quote": quote,
            "project_data": request.project_data,
            "estimated_hours": request.estimated_hours,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar orçamento: {str(e)}")

@router.post("/suggest-next-steps")
async def suggest_next_steps(
    opportunity_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sugere próximos passos para uma oportunidade"""
    try:
        prompt = f"""
        Com base nesta oportunidade, sugira os próximos passos estratégicos.

        DADOS ATUAIS:
        {json.dumps(opportunity_data, ensure_ascii=False, indent=2)}

        CONSIDERE:
        - Estágio atual do funil
        - Tempo desde último contato
        - Ações já realizadas
        - Perfil do cliente

        SUGIRA:
        1. Ação imediata prioritária
        2. Sequência de passos para os próximos 7 dias
        3. Estratégias de follow-up
        4. Possíveis objeções e como contorná-las
        """

        suggestions = await call_ai_api(prompt, 1000, db)

        return {
            "suggestions": suggestions,
            "opportunity_data": opportunity_data,
            "suggested_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro nas sugestões: {str(e)}")
