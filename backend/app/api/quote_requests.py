from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.commission import QuoteRequest
from app.models.project import Project
from app.api.dependencies import get_current_user, get_user_role_str, is_user_role
from app.api.ai import call_ai_api
import json
import os
import httpx

router = APIRouter(prefix="/quote-requests", tags=["quote-requests"])


# Schemas
class QuoteRequestCreate(BaseModel):
    project_id: int
    seller_notes: Optional[str] = None

class StageInfo(BaseModel):
    name: str
    duration_days: int
    start_date: Optional[str] = None
    description: Optional[str] = None

class QuoteRequestUpdate(BaseModel):
    technical_details: Optional[str] = None
    technologies: Optional[str] = None
    stages: Optional[str] = None
    deadlines: Optional[str] = None
    estimated_hours: Optional[int] = None
    estimated_deadline: Optional[str] = None
    technical_specs: Optional[str] = None
    estimated_value: Optional[str] = None
    breakdown: Optional[dict] = None
    ai_generated: Optional[bool] = False

class QuoteRequestResponse(BaseModel):
    id: int
    project_id: int
    project_name: Optional[str] = None
    seller_id: int
    seller_name: Optional[str] = None
    planning_owner_id: Optional[int] = None
    planning_owner_name: Optional[str] = None
    status: str
    seller_notes: Optional[str] = None
    technologies: Optional[List[str]] = None
    stages: Optional[List[dict]] = None
    estimated_deadline: Optional[datetime] = None
    estimated_hours: Optional[int] = None
    technical_specs: Optional[str] = None
    estimated_value: Optional[str] = None
    breakdown: Optional[dict] = None
    ai_generated: bool
    seller_notified_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=QuoteRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_quote_request(
    request_data: QuoteRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vendedor solicita orçamento para um projeto"""
    user_role = get_user_role_str(current_user)
    if user_role != "vendedor" and user_role != "admin":
        raise HTTPException(status_code=403, detail="Apenas vendedores podem solicitar orçamentos")
    
    # Verificar se projeto existe e pertence ao vendedor
    result = await db.execute(select(Project).where(Project.id == request_data.project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    if user_role == "vendedor" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você não é o dono deste projeto")
    
    # Verificar se já existe solicitação pendente
    result = await db.execute(
        select(QuoteRequest).where(
            QuoteRequest.project_id == request_data.project_id,
            QuoteRequest.status.in_(["pending", "in_progress"])
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Já existe uma solicitação de orçamento pendente para este projeto")
    
    quote_request = QuoteRequest(
        project_id=request_data.project_id,
        seller_id=current_user.id,
        seller_notes=request_data.seller_notes,
        status="pending"
    )
    
    db.add(quote_request)
    await db.commit()
    await db.refresh(quote_request)
    
    # Carregar relacionamentos
    await db.refresh(quote_request, ["project", "seller"])
    
    return QuoteRequestResponse(
        id=quote_request.id,
        project_id=quote_request.project_id,
        project_name=quote_request.project.name if quote_request.project else None,
        seller_id=quote_request.seller_id,
        seller_name=quote_request.seller.name if quote_request.seller else None,
        planning_owner_id=quote_request.planning_owner_id,
        planning_owner_name=quote_request.planning_owner.name if quote_request.planning_owner else None,
        status=quote_request.status,
        seller_notes=quote_request.seller_notes,
        technologies=quote_request.technologies,
        stages=quote_request.stages,
        estimated_deadline=quote_request.estimated_deadline,
        estimated_hours=quote_request.estimated_hours,
        technical_specs=quote_request.technical_specs,
        estimated_value=quote_request.estimated_value,
        breakdown=quote_request.breakdown,
        ai_generated=quote_request.ai_generated,
        seller_notified_at=quote_request.seller_notified_at,
        completed_at=quote_request.completed_at,
        created_at=quote_request.created_at
    )


@router.get("/", response_model=List[QuoteRequestResponse])
async def list_quote_requests(
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista solicitações de orçamento"""
    query = select(QuoteRequest).options(
        selectinload(QuoteRequest.project),
        selectinload(QuoteRequest.seller),
        selectinload(QuoteRequest.planning_owner)
    )
    
    # Filtros por role
    user_role = get_user_role_str(current_user)
    if user_role == "vendedor":
        query = query.where(QuoteRequest.seller_id == current_user.id)
    elif user_role == "planejamento":
        query = query.where(
            (QuoteRequest.planning_owner_id == current_user.id) |
            (QuoteRequest.planning_owner_id.is_(None))
        )
    
    if status_filter:
        query = query.where(QuoteRequest.status == status_filter)
    
    result = await db.execute(query)
    requests = result.scalars().all()
    
    return [
        QuoteRequestResponse(
            id=req.id,
            project_id=req.project_id,
            project_name=req.project.name if req.project else None,
            seller_id=req.seller_id,
            seller_name=req.seller.name if req.seller else None,
            planning_owner_id=req.planning_owner_id,
            planning_owner_name=req.planning_owner.name if req.planning_owner else None,
            status=req.status,
            seller_notes=req.seller_notes,
            technologies=req.technologies,
            stages=req.stages,
            estimated_deadline=req.estimated_deadline,
            technical_specs=req.technical_specs,
            estimated_value=req.estimated_value,
            breakdown=req.breakdown,
            ai_generated=req.ai_generated,
            seller_notified_at=req.seller_notified_at,
            completed_at=req.completed_at,
            created_at=req.created_at
        )
        for req in requests
    ]


@router.put("/{request_id}", response_model=QuoteRequestResponse)
async def update_quote_request(
    request_id: int,
    update_data: QuoteRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza solicitação de orçamento - apenas planejamento"""
    user_role = get_user_role_str(current_user)
    if user_role != "planejamento" and user_role != "admin":
        raise HTTPException(status_code=403, detail="Apenas equipe de planejamento pode atualizar orçamentos")
    
    result = await db.execute(
        select(QuoteRequest).where(QuoteRequest.id == request_id)
    )
    quote_request = result.scalar_one_or_none()
    
    if not quote_request:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    # Atualizar campos
    update_dict = update_data.dict(exclude_unset=True)
    
    if "estimated_deadline" in update_dict and update_dict["estimated_deadline"]:
        update_dict["estimated_deadline"] = datetime.fromisoformat(update_dict["estimated_deadline"])
    
    # Mapear campos do frontend para o modelo
    if "technical_details" in update_dict:
        quote_request.technical_specs = update_dict["technical_details"]
    if "technologies" in update_dict:
        # Se for string, converter para lista
        if isinstance(update_dict["technologies"], str):
            quote_request.technologies = [t.strip() for t in update_dict["technologies"].split(",") if t.strip()]
        else:
            quote_request.technologies = update_dict["technologies"]
    if "stages" in update_dict:
        quote_request.stages = update_dict["stages"]
    if "deadlines" in update_dict:
        quote_request.estimated_deadline = datetime.fromisoformat(update_dict["deadlines"]) if update_dict["deadlines"] else None
    if "estimated_hours" in update_dict:
        quote_request.estimated_hours = update_dict["estimated_hours"]
    
    # Outros campos
    for key in ["estimated_value", "breakdown", "ai_generated"]:
        if key in update_dict:
            setattr(quote_request, key, update_dict[key])
    
    quote_request.planning_owner_id = current_user.id
    quote_request.status = "in_progress"
    
    await db.commit()
    await db.refresh(quote_request)
    await db.refresh(quote_request, ["project", "seller", "planning_owner"])
    
    return QuoteRequestResponse(
        id=quote_request.id,
        project_id=quote_request.project_id,
        project_name=quote_request.project.name if quote_request.project else None,
        seller_id=quote_request.seller_id,
        seller_name=quote_request.seller.name if quote_request.seller else None,
        planning_owner_id=quote_request.planning_owner_id,
        planning_owner_name=quote_request.planning_owner.name if quote_request.planning_owner else None,
        status=quote_request.status,
        seller_notes=quote_request.seller_notes,
        technologies=quote_request.technologies,
        stages=quote_request.stages,
        estimated_deadline=quote_request.estimated_deadline,
        estimated_hours=quote_request.estimated_hours,
        technical_specs=quote_request.technical_specs,
        estimated_value=quote_request.estimated_value,
        breakdown=quote_request.breakdown,
        ai_generated=quote_request.ai_generated,
        seller_notified_at=quote_request.seller_notified_at,
        completed_at=quote_request.completed_at,
        created_at=quote_request.created_at
    )


@router.post("/{request_id}/generate-with-ai")
async def generate_quote_with_ai(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Gera orçamento automaticamente usando IA"""
    user_role = get_user_role_str(current_user)
    if user_role != "planejamento" and user_role != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    result = await db.execute(
        select(QuoteRequest).options(
            selectinload(QuoteRequest.project),
            selectinload(QuoteRequest.seller)
        ).where(QuoteRequest.id == request_id)
    )
    quote_request = result.scalar_one_or_none()
    
    if not quote_request:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    if not quote_request.project:
        raise HTTPException(status_code=400, detail="Projeto não encontrado")
    
    project = quote_request.project
    
    # Preparar dados do projeto para a IA
    project_data = {
        "name": project.name,
        "description": project.description or "",
        "project_type": project.project_type.value if project.project_type else "custom_development",
        "estimated_value": project.estimated_value or "",
        "technical_requirements": project.technical_requirements or "",
        "seller_notes": quote_request.seller_notes or ""
    }
    
    # Criar prompt para a IA
    prompt = f"""
    Você é um especialista em planejamento de projetos da Innexar, empresa de desenvolvimento de software.

    Analise este projeto e gere um orçamento técnico detalhado:

    NOME DO PROJETO: {project.name}
    DESCRIÇÃO: {project.description or 'Não informado'}
    TIPO: {project.project_type.value if project.project_type else 'Desenvolvimento Customizado'}
    VALOR ESTIMADO: {project.estimated_value or 'A definir'}
    REQUISITOS TÉCNICOS: {project.technical_requirements or 'Não especificado'}
    NOTAS DO VENDEDOR: {quote_request.seller_notes or 'Nenhuma nota adicional'}

    GERE UM ORÇAMENTO TÉCNICO COMPLETO COM:

    1. ESPECIFICAÇÕES TÉCNICAS DETALHADAS:
       - Arquitetura recomendada
       - Tecnologias sugeridas (lista separada por vírgulas)
       - Requisitos de infraestrutura
       - Considerações de segurança e performance

    2. ETAPAS DO PROJETO:
       - Lista de etapas com duração estimada em dias
       - Formato: "Etapa 1: Nome da Etapa - X dias, Etapa 2: ..."
       - Inclua: Planejamento, Desenvolvimento, Testes, Deploy

    3. PRAZOS:
       - Prazo total estimado
       - Marcos importantes (milestones)
       - Formato: "Etapa 1: 2 semanas, Etapa 2: 3 semanas, ..."

    4. HORAS ESTIMADAS:
       - Total de horas de desenvolvimento
       - Breakdown por etapa (opcional)

    IMPORTANTE:
    - Seja realista e profissional
    - Considere a complexidade do projeto
    - Sugira tecnologias modernas e adequadas
    - Forneça estimativas conservadoras mas realistas
    - Responda em formato estruturado e claro

    FORMATO DA RESPOSTA (JSON):
    {{
        "technical_specs": "Especificações técnicas detalhadas...",
        "technologies": "React, Node.js, PostgreSQL, Docker",
        "stages": "Etapa 1: Planejamento e Arquitetura - 5 dias, Etapa 2: Desenvolvimento Frontend - 15 dias, Etapa 3: Desenvolvimento Backend - 20 dias, Etapa 4: Testes e Ajustes - 5 dias, Etapa 5: Deploy e Documentação - 3 dias",
        "deadlines": "Etapa 1: 1 semana, Etapa 2: 2 semanas, Etapa 3: 3 semanas, Etapa 4: 1 semana, Etapa 5: 3 dias",
        "estimated_hours": 320,
        "estimated_value": "R$ 45.000,00 - R$ 55.000,00"
    }}
    """
    
    try:
        # Chamar IA
        ai_response = await call_ai_api(prompt, 2500, db)
        
        # Tentar parsear JSON da resposta
        try:
            # Limpar resposta da IA (pode ter markdown ou texto extra)
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response.replace("```json", "").replace("```", "").strip()
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response.replace("```", "").strip()
            
            quote_data = json.loads(cleaned_response)
        except json.JSONDecodeError:
            # Se não conseguir parsear JSON, extrair informações do texto
            quote_data = {
                "technical_specs": ai_response,
                "technologies": "",
                "stages": "",
                "deadlines": "",
                "estimated_hours": None,
                "estimated_value": project.estimated_value or ""
            }
        
        # Atualizar quote request
        quote_request.technical_specs = quote_data.get("technical_specs", "")
        quote_request.technologies = quote_data.get("technologies", "").split(", ") if quote_data.get("technologies") else []
        quote_request.stages = quote_data.get("stages", "")
        quote_request.estimated_hours = quote_data.get("estimated_hours")
        quote_request.estimated_value = quote_data.get("estimated_value", project.estimated_value or "")
        quote_request.ai_generated = True
        quote_request.status = "in_progress"
        quote_request.planning_owner_id = current_user.id
        
        await db.commit()
        await db.refresh(quote_request, ["project", "seller", "planning_owner"])
        
        return QuoteRequestResponse(
            id=quote_request.id,
            project_id=quote_request.project_id,
            project_name=quote_request.project.name if quote_request.project else None,
            seller_id=quote_request.seller_id,
            seller_name=quote_request.seller.name if quote_request.seller else None,
            planning_owner_id=quote_request.planning_owner_id,
            planning_owner_name=quote_request.planning_owner.name if quote_request.planning_owner else None,
            status=quote_request.status,
            seller_notes=quote_request.seller_notes,
            technologies=quote_request.technologies,
            stages=quote_request.stages,
            estimated_deadline=quote_request.estimated_deadline,
            technical_specs=quote_request.technical_specs,
            estimated_value=quote_request.estimated_value,
            breakdown=quote_request.breakdown,
            ai_generated=quote_request.ai_generated,
            seller_notified_at=quote_request.seller_notified_at,
            completed_at=quote_request.completed_at,
            created_at=quote_request.created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar orçamento com IA: {str(e)}")


@router.put("/{request_id}/complete")
async def complete_quote_request(
    request_id: int,
    update_data: QuoteRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Finaliza orçamento e notifica vendedor"""
    user_role = get_user_role_str(current_user)
    if user_role != "planejamento" and user_role != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    result = await db.execute(
        select(QuoteRequest).where(QuoteRequest.id == request_id)
    )
    quote_request = result.scalar_one_or_none()
    
    if not quote_request:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    # Atualizar campos do formulário
    update_dict = update_data.dict(exclude_unset=True)
    
    # Mapear campos do frontend para o modelo
    if "technical_details" in update_dict:
        quote_request.technical_specs = update_dict["technical_details"]
    if "technologies" in update_dict:
        # Se for string, converter para lista
        if isinstance(update_dict["technologies"], str):
            quote_request.technologies = [t.strip() for t in update_dict["technologies"].split(",") if t.strip()]
        else:
            quote_request.technologies = update_dict["technologies"]
    if "stages" in update_dict:
        quote_request.stages = update_dict["stages"]
    if "deadlines" in update_dict:
        quote_request.estimated_deadline = datetime.fromisoformat(update_dict["deadlines"]) if update_dict["deadlines"] else None
    if "estimated_hours" in update_dict:
        quote_request.estimated_hours = update_dict["estimated_hours"]
    
    # Outros campos
    for key in ["estimated_value", "breakdown", "ai_generated", "technical_specs", "estimated_deadline"]:
        if key in update_dict:
            setattr(quote_request, key, update_dict[key])
    
    quote_request.status = "completed"
    quote_request.completed_at = datetime.utcnow()
    quote_request.seller_notified_at = datetime.utcnow()
    quote_request.planning_owner_id = current_user.id
    
    # Atualizar projeto com informações do orçamento
    result = await db.execute(select(Project).where(Project.id == quote_request.project_id))
    project = result.scalar_one_or_none()
    
    if project:
        if quote_request.estimated_value:
            project.approved_value = quote_request.estimated_value
        if quote_request.technical_specs:
            project.technical_requirements = quote_request.technical_specs
        if quote_request.technologies:
            if isinstance(quote_request.technologies, list):
                project.tech_stack = ", ".join(quote_request.technologies)
            else:
                project.tech_stack = quote_request.technologies
    
    await db.commit()
    await db.refresh(quote_request, ["project", "seller", "planning_owner"])
    
    return {
        "message": "Orçamento finalizado e vendedor notificado",
        "status": "completed",
        "quote_request": QuoteRequestResponse(
            id=quote_request.id,
            project_id=quote_request.project_id,
            project_name=quote_request.project.name if quote_request.project else None,
            seller_id=quote_request.seller_id,
            seller_name=quote_request.seller.name if quote_request.seller else None,
            planning_owner_id=quote_request.planning_owner_id,
            planning_owner_name=quote_request.planning_owner.name if quote_request.planning_owner else None,
            status=quote_request.status,
            seller_notes=quote_request.seller_notes,
            technologies=quote_request.technologies,
            stages=quote_request.stages,
            estimated_deadline=quote_request.estimated_deadline,
            technical_specs=quote_request.technical_specs,
            estimated_value=quote_request.estimated_value,
            breakdown=quote_request.breakdown,
            ai_generated=quote_request.ai_generated,
            seller_notified_at=quote_request.seller_notified_at,
            completed_at=quote_request.completed_at,
            created_at=quote_request.created_at
        )
    }

