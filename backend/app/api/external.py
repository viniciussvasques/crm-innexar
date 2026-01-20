"""
APIs Externas - Para integração com formulários do site e outros sistemas
Estas APIs podem ser acessadas sem autenticação (com token de API ou validação específica)
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.contact import Contact
from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus, ProjectType
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import os

router = APIRouter(prefix="/external", tags=["external"])

from app.core.config import settings

# Token de API para validação
EXTERNAL_API_TOKEN = settings.EXTERNAL_API_TOKEN

class WebToLeadRequest(BaseModel):
    """Request para web-to-lead do site"""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = "website"  # Origem do lead
    project_type: Optional[str] = None  # Tipo de projeto de interesse

class WebToLeadResponse(BaseModel):
    """Response do web-to-lead"""
    success: bool
    contact_id: Optional[int] = None
    message: str

def verify_api_token(x_api_token: str = Header(...)):
    """Verifica token de API externa"""
    if x_api_token != EXTERNAL_API_TOKEN:
        raise HTTPException(status_code=401, detail="Token de API inválido")
    return x_api_token

@router.post("/web-to-lead", response_model=WebToLeadResponse)
async def web_to_lead(
    lead_data: WebToLeadRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(verify_api_token)
):
    """
    API Externa: Web-to-Lead
    Recebe leads do formulário do site e cria contato automaticamente
    """
    try:
        # Verificar se o contato já existe (deduplicação por email)
        existing_contact = await db.scalar(
            select(Contact).where(Contact.email == lead_data.email)
        )
        
        if existing_contact:
            # Contato já existe, atualizar informações se necessário
            if lead_data.phone and not existing_contact.phone:
                existing_contact.phone = lead_data.phone
            if lead_data.company and not existing_contact.company:
                existing_contact.company = lead_data.company
            if lead_data.message:
                existing_contact.notes = (existing_contact.notes or "") + f"\n\nNovo lead de {lead_data.source} em {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}:\n{lead_data.message}"
            
            existing_contact.updated_at = datetime.utcnow()
            await db.commit()
            
            return WebToLeadResponse(
                success=True,
                contact_id=existing_contact.id,
                message="Lead atualizado (contato já existia)"
            )
        
        # Buscar vendedor para atribuição (round-robin ou primeiro disponível)
        # Por enquanto, atribuir ao primeiro vendedor ativo
        vendedor = await db.scalar(
            select(User).where(
                User.role == UserRole.VENDEDOR,
                User.is_active == True
            ).limit(1)
        )
        
        if not vendedor:
            # Se não houver vendedor, criar sem owner (admin pode atribuir depois)
            # Ou criar um vendedor padrão
            raise HTTPException(
                status_code=500,
                detail="Nenhum vendedor disponível. Configure pelo menos um vendedor no sistema."
            )
        
        # Criar novo contato
        new_contact = Contact(
            name=lead_data.name,
            email=lead_data.email,
            phone=lead_data.phone,
            company=lead_data.company,
            status="lead",
            notes=f"Lead captado de {lead_data.source} em {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}" + (f"\n\nMensagem: {lead_data.message}" if lead_data.message else ""),
            owner_id=vendedor.id
        )
        
        db.add(new_contact)
        await db.commit()
        await db.refresh(new_contact)
        
        # Opcional: Criar projeto automaticamente se project_type for fornecido
        project = None
        if lead_data.project_type:
            try:
                project_type = ProjectType(lead_data.project_type)
                project = Project(
                    name=f"Projeto {lead_data.name} - {lead_data.project_type}",
                    description=lead_data.message or f"Projeto de {lead_data.project_type} para {lead_data.name}",
                    contact_id=new_contact.id,
                    owner_id=vendedor.id,
                    project_type=project_type,
                    status=ProjectStatus.LEAD,
                    estimated_value=None,
                    technical_requirements=lead_data.message
                )
                db.add(project)
                await db.commit()
                await db.refresh(project)
            except (ValueError, AttributeError):
                # project_type inválido, ignorar
                pass
        
        return WebToLeadResponse(
            success=True,
            contact_id=new_contact.id,
            message=f"Lead criado com sucesso e atribuído a {vendedor.name}" + (f". Projeto criado (ID: {project.id})" if project else "")
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao processar lead: {str(e)}")

@router.get("/health")
async def external_health():
    """Health check para APIs externas"""
    return {
        "status": "ok",
        "service": "external-api",
        "endpoints": [
            "/external/web-to-lead"
        ]
    }

