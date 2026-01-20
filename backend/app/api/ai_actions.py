"""
Sistema de ações que a IA pode executar no CRM
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.models.contact import Contact
from app.models.opportunity import Opportunity
from app.models.activity import Activity
from app.api.dependencies import get_current_user, get_user_role_str
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

router = APIRouter(prefix="/ai/actions", tags=["ai-actions"])

class AICreateContactRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: str = "lead"
    notes: Optional[str] = None

class AIUpdateContactRequest(BaseModel):
    contact_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class AICreateOpportunityRequest(BaseModel):
    name: str
    contact_id: Optional[int] = None
    contact_name: Optional[str] = None  # Se não tiver contact_id, pode criar ou buscar por nome
    value: Optional[float] = None
    stage: str = "qualificacao"
    probability: int = 50
    expected_close_date: Optional[str] = None
    notes: Optional[str] = None

class AIUpdateOpportunityRequest(BaseModel):
    opportunity_id: int
    name: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    expected_close_date: Optional[str] = None
    notes: Optional[str] = None

class AICreateActivityRequest(BaseModel):
    type: str  # task, call, meeting, note
    subject: str
    contact_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    due_date: Optional[str] = None
    description: Optional[str] = None

class AIActionResponse(BaseModel):
    success: bool
    action_type: str
    message: str
    data: Optional[Dict[str, Any]] = None

@router.post("/create-contact", response_model=AIActionResponse)
async def ai_create_contact(
    request: AICreateContactRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Permite à IA criar um contato"""
    try:
        # Verificar se email já existe
        if request.email:
            result = await db.execute(
                select(Contact).where(Contact.email == request.email)
            )
            existing = result.scalar_one_or_none()
            if existing:
                return AIActionResponse(
                    success=False,
                    action_type="create_contact",
                    message=f"Contato com email {request.email} já existe (ID: {existing.id})",
                    data={"contact_id": existing.id}
                )
        
        contact = Contact(
            name=request.name,
            email=request.email,
            phone=request.phone,
            company=request.company,
            status=request.status,
            notes=request.notes,
            owner_id=current_user.id
        )
        
        db.add(contact)
        await db.commit()
        await db.refresh(contact)
        
        # Se for um lead (status="lead"), iniciar análise automática em background
        if contact.status == "lead":
            from app.api.lead_analysis import analyze_lead_background
            if background_tasks:
                background_tasks.add_task(analyze_lead_background, contact.id)
            else:
                # Se não tiver background_tasks, usar asyncio
                import asyncio
                asyncio.create_task(analyze_lead_background(contact.id))
        
        return AIActionResponse(
            success=True,
            action_type="create_contact",
            message=f"Contato '{contact.name}' criado com sucesso" + (" e análise iniciada" if contact.status == "lead" else ""),
            data={
                "contact_id": contact.id,
                "name": contact.name,
                "email": contact.email,
                "company": contact.company
            }
        )
    except Exception as e:
        await db.rollback()
        return AIActionResponse(
            success=False,
            action_type="create_contact",
            message=f"Erro ao criar contato: {str(e)}"
        )

@router.post("/update-contact", response_model=AIActionResponse)
async def ai_update_contact(
    request: AIUpdateContactRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Permite à IA atualizar um contato"""
    try:
        result = await db.execute(
            select(Contact).where(Contact.id == request.contact_id)
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            return AIActionResponse(
                success=False,
                action_type="update_contact",
                message=f"Contato com ID {request.contact_id} não encontrado"
            )
        
        # Verificar permissão
        user_role = get_user_role_str(current_user)
        if user_role == "vendedor" and contact.owner_id != current_user.id:
            return AIActionResponse(
                success=False,
                action_type="update_contact",
                message="Sem permissão para editar este contato"
            )
        
        # Atualizar campos
        update_data = request.model_dump(exclude_unset=True, exclude={"contact_id"})
        for key, value in update_data.items():
            if value is not None:
                setattr(contact, key, value)
        
        contact.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(contact)
        
        return AIActionResponse(
            success=True,
            action_type="update_contact",
            message=f"Contato '{contact.name}' atualizado com sucesso",
            data={
                "contact_id": contact.id,
                "name": contact.name,
                "email": contact.email,
                "company": contact.company,
                "status": contact.status
            }
        )
    except Exception as e:
        await db.rollback()
        return AIActionResponse(
            success=False,
            action_type="update_contact",
            message=f"Erro ao atualizar contato: {str(e)}"
        )

@router.post("/create-opportunity", response_model=AIActionResponse)
async def ai_create_opportunity(
    request: AICreateOpportunityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Permite à IA criar uma oportunidade"""
    try:
        contact_id = request.contact_id
        
        # Se não tiver contact_id mas tiver contact_name, buscar ou criar contato
        if not contact_id and request.contact_name:
            result = await db.execute(
                select(Contact).where(Contact.name.ilike(f"%{request.contact_name}%"))
            )
            contact = result.scalar_one_or_none()
            
            if not contact:
                # Criar contato automaticamente
                new_contact = Contact(
                    name=request.contact_name,
                    owner_id=current_user.id,
                    status="lead"
                )
                db.add(new_contact)
                await db.flush()
                contact_id = new_contact.id
            else:
                contact_id = contact.id
        
        if not contact_id:
            return AIActionResponse(
                success=False,
                action_type="create_opportunity",
                message="É necessário fornecer contact_id ou contact_name"
            )
        
        # Verificar se contato existe
        result = await db.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        contact = result.scalar_one_or_none()
        if not contact:
            return AIActionResponse(
                success=False,
                action_type="create_opportunity",
                message=f"Contato com ID {contact_id} não encontrado"
            )
        
        opportunity = Opportunity(
            name=request.name,
            contact_id=contact_id,
            owner_id=current_user.id,
            value=request.value,
            stage=request.stage,
            probability=request.probability,
            notes=request.notes
        )
        
        if request.expected_close_date:
            try:
                opportunity.expected_close_date = datetime.fromisoformat(request.expected_close_date)
            except:
                pass
        
        db.add(opportunity)
        await db.commit()
        await db.refresh(opportunity)
        
        return AIActionResponse(
            success=True,
            action_type="create_opportunity",
            message=f"Oportunidade '{opportunity.name}' criada com sucesso",
            data={
                "opportunity_id": opportunity.id,
                "name": opportunity.name,
                "contact_id": contact_id,
                "contact_name": contact.name,
                "value": float(opportunity.value) if opportunity.value else None,
                "stage": opportunity.stage
            }
        )
    except Exception as e:
        await db.rollback()
        return AIActionResponse(
            success=False,
            action_type="create_opportunity",
            message=f"Erro ao criar oportunidade: {str(e)}"
        )

@router.post("/update-opportunity", response_model=AIActionResponse)
async def ai_update_opportunity(
    request: AIUpdateOpportunityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Permite à IA atualizar uma oportunidade"""
    try:
        result = await db.execute(
            select(Opportunity).where(Opportunity.id == request.opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            return AIActionResponse(
                success=False,
                action_type="update_opportunity",
                message=f"Oportunidade com ID {request.opportunity_id} não encontrada"
            )
        
        # Verificar permissão
        user_role = get_user_role_str(current_user)
        if user_role == "vendedor" and opportunity.owner_id != current_user.id:
            return AIActionResponse(
                success=False,
                action_type="update_opportunity",
                message="Sem permissão para editar esta oportunidade"
            )
        
        # Atualizar campos
        update_data = request.model_dump(exclude_unset=True, exclude={"opportunity_id"})
        for key, value in update_data.items():
            if value is not None:
                if key == "expected_close_date":
                    try:
                        setattr(opportunity, key, datetime.fromisoformat(value))
                    except:
                        pass
                else:
                    setattr(opportunity, key, value)
        
        opportunity.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(opportunity)
        
        return AIActionResponse(
            success=True,
            action_type="update_opportunity",
            message=f"Oportunidade '{opportunity.name}' atualizada com sucesso",
            data={
                "opportunity_id": opportunity.id,
                "name": opportunity.name,
                "value": float(opportunity.value) if opportunity.value else None,
                "stage": opportunity.stage,
                "probability": opportunity.probability
            }
        )
    except Exception as e:
        await db.rollback()
        return AIActionResponse(
            success=False,
            action_type="update_opportunity",
            message=f"Erro ao atualizar oportunidade: {str(e)}"
        )

@router.post("/create-activity", response_model=AIActionResponse)
async def ai_create_activity(
    request: AICreateActivityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Permite à IA criar uma atividade"""
    try:
        activity = Activity(
            type=request.type,
            subject=request.subject,
            description=request.description,
            contact_id=request.contact_id,
            opportunity_id=request.opportunity_id,
            owner_id=current_user.id,
            status="pending"
        )
        
        if request.due_date:
            try:
                activity.due_date = datetime.fromisoformat(request.due_date)
            except:
                pass
        
        db.add(activity)
        await db.commit()
        await db.refresh(activity)
        
        return AIActionResponse(
            success=True,
            action_type="create_activity",
            message=f"Atividade '{activity.subject}' criada com sucesso",
            data={
                "activity_id": activity.id,
                "type": activity.type,
                "subject": activity.subject,
                "status": activity.status
            }
        )
    except Exception as e:
        await db.rollback()
        return AIActionResponse(
            success=False,
            action_type="create_activity",
            message=f"Erro ao criar atividade: {str(e)}"
        )

@router.get("/list-contacts")
async def ai_list_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = None,
    limit: int = 10
):
    """Lista contatos para a IA consultar"""
    query = select(Contact)
    
    user_role = get_user_role_str(current_user)
    if user_role == "vendedor":
        query = query.where(Contact.owner_id == current_user.id)
    
    if search:
        query = query.where(
            Contact.name.ilike(f"%{search}%") |
            Contact.email.ilike(f"%{search}%") |
            Contact.company.ilike(f"%{search}%")
        )
    
    query = query.limit(limit)
    result = await db.execute(query)
    contacts = result.scalars().all()
    
    return {
        "contacts": [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "company": c.company,
                "status": c.status
            }
            for c in contacts
        ]
    }

@router.get("/list-opportunities")
async def ai_list_opportunities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = None,
    limit: int = 10
):
    """Lista oportunidades para a IA consultar"""
    query = select(Opportunity)
    
    user_role = get_user_role_str(current_user)
    if user_role == "vendedor":
        query = query.where(Opportunity.owner_id == current_user.id)
    
    if search:
        query = query.where(Opportunity.name.ilike(f"%{search}%"))
    
    query = query.limit(limit)
    result = await db.execute(query)
    opportunities = result.scalars().all()
    
    return {
        "opportunities": [
            {
                "id": o.id,
                "name": o.name,
                "value": float(o.value) if o.value else None,
                "stage": o.stage,
                "probability": o.probability,
                "contact_id": o.contact_id
            }
            for o in opportunities
        ]
    }

