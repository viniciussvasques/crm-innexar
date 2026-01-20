"""
API pública para receber formulários do site
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db, AsyncSessionLocal
from app.models.contact import Contact
from app.models.user import User
from app.models.opportunity import Opportunity
from app.models.lead_analysis import LeadAnalysis
from app.api.lead_analysis import analyze_lead_background
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import os
import asyncio

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Token de segurança para webhooks (pode ser configurado via env)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me-in-production")

class WebhookContactRequest(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = "website"  # website, landing_page, etc.
    # Campos do formulário do site
    projectType: Optional[str] = None  # web, saas, mobile, etc.
    budget: Optional[str] = None  # under-10k, 10k-25k, etc.
    timeline: Optional[str] = None  # asap, 1-3months, etc.
    website: Optional[str] = None
    linkedin: Optional[str] = None
    position: Optional[str] = None
    industry: Optional[str] = None
    companySize: Optional[str] = None
    # Checklist form fields
    currentChallenges: Optional[str] = None
    targetAudience: Optional[str] = None
    businessGoals: Optional[str] = None
    technicalRequirements: Optional[str] = None
    budgetRange: Optional[str] = None
    teamSize: Optional[str] = None
    existingTools: Optional[str] = None
    successMetrics: Optional[str] = None
    additionalNotes: Optional[str] = None
    metadata: Optional[dict] = None

class WebhookResponse(BaseModel):
    success: bool
    message: str
    contact_id: Optional[int] = None

def verify_webhook_token(authorization: Optional[str] = Header(None)):
    """Verifica o token de autorização do webhook"""
    if not WEBHOOK_SECRET or WEBHOOK_SECRET == "change-me-in-production":
        # Em desenvolvimento, permitir sem token
        return True
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Token de autorização necessário")
    
    # Formato: Bearer <token>
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de token inválido")
    
    token = authorization.replace("Bearer ", "")
    if token != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Token inválido")
    
    return True

@router.post("/contact", response_model=WebhookResponse)
async def webhook_create_contact(
    request: WebhookContactRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint público para receber contatos de formulários do site
    Não requer autenticação, mas pode usar token de segurança
    """
    # Verificar token se configurado
    verify_webhook_token(authorization)
    
    try:
        # Buscar usuário admin padrão ou primeiro admin disponível
        result = await db.execute(
            select(User).where(User.role == "admin", User.is_active == True).limit(1)
        )
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            raise HTTPException(
                status_code=500,
                detail="Nenhum administrador encontrado para atribuir o contato"
            )
        
        # Verificar se email já existe
        if request.email:
            result = await db.execute(
                select(Contact).where(Contact.email == request.email)
            )
            existing = result.scalar_one_or_none()
            if existing:
                return WebhookResponse(
                    success=True,
                    message="Contato já existe no sistema",
                    contact_id=existing.id
                )
        
        # Preparar notas com todas as informações
        notes_parts = [f"Origem: {request.source}"]
        if request.message:
            notes_parts.append(f"Mensagem: {request.message}")
        
        # Preparar metadata JSON com informações do checklist
        metadata_dict = {}
        if request.currentChallenges:
            metadata_dict["currentChallenges"] = request.currentChallenges
        if request.targetAudience:
            metadata_dict["targetAudience"] = request.targetAudience
        if request.businessGoals:
            metadata_dict["businessGoals"] = request.businessGoals
        if request.technicalRequirements:
            metadata_dict["technicalRequirements"] = request.technicalRequirements
        if request.teamSize:
            metadata_dict["teamSize"] = request.teamSize
        if request.existingTools:
            metadata_dict["existingTools"] = request.existingTools
        if request.successMetrics:
            metadata_dict["successMetrics"] = request.successMetrics
        if request.additionalNotes:
            metadata_dict["additionalNotes"] = request.additionalNotes
        
        import json
        metadata_json = json.dumps(metadata_dict) if metadata_dict else None
        
        # Criar contato como lead
        contact = Contact(
            name=request.name,
            email=request.email,
            phone=request.phone,
            company=request.company,
            status="lead",
            notes="\n".join(notes_parts),
            project_type=request.projectType,
            budget_range=request.budget or request.budgetRange,
            timeline=request.timeline,
            website=request.website,
            linkedin=request.linkedin,
            position=request.position,
            industry=request.industry,
            company_size=request.companySize,
            source=request.source or "website",
            contact_metadata=metadata_json,
            owner_id=admin_user.id
        )
        
        db.add(contact)
        await db.commit()
        await db.refresh(contact)
        
        # Iniciar análise automática em background
        background_tasks.add_task(analyze_lead_background, contact.id)
        
        # Aguardar análise ser concluída (em background) e criar oportunidade automaticamente
        # Isso será feito em uma tarefa separada após a análise
        async def create_opportunity_after_analysis(contact_id: int):
            """Cria oportunidade após análise ser concluída"""
            import asyncio
            from app.models.opportunity import Opportunity
            
            # Aguardar até 60 segundos pela análise
            for attempt in range(12):  # 12 tentativas de 5 segundos = 60 segundos
                await asyncio.sleep(5)
                async with AsyncSessionLocal() as session:
                    try:
                        result = await session.execute(
                            select(LeadAnalysis).where(LeadAnalysis.contact_id == contact_id)
                        )
                        analysis = result.scalar_one_or_none()
                        
                        if analysis and analysis.analysis_status == "completed":
                            # Buscar contato
                            result = await session.execute(select(Contact).where(Contact.id == contact_id))
                            contact_obj = result.scalar_one_or_none()
                            
                            if contact_obj:
                                # Verificar se oportunidade já existe
                                result = await session.execute(
                                    select(Opportunity).where(Opportunity.contact_id == contact_id)
                                )
                                existing_opp = result.scalar_one_or_none()
                                
                                if not existing_opp:
                                    # Criar oportunidade com dados da análise
                                    opportunity_value = None
                                    if analysis.analysis_metadata and "potential_value" in analysis.analysis_metadata:
                                        try:
                                            opportunity_value = float(analysis.analysis_metadata["potential_value"])
                                        except:
                                            pass
                                    
                                    opportunity = Opportunity(
                                        name=f"{contact_obj.company or contact_obj.name} - Oportunidade",
                                        contact_id=contact_id,
                                        owner_id=contact_obj.owner_id,
                                        value=opportunity_value,
                                        stage="qualificacao",
                                        probability=analysis.opportunity_score or 50
                                    )
                                    
                                    session.add(opportunity)
                                    await session.commit()
                            break
                    except Exception as e:
                        print(f"Erro ao criar oportunidade após análise (tentativa {attempt + 1}): {str(e)}")
                        if attempt == 11:  # Última tentativa
                            break
        
        # Iniciar tarefa para criar oportunidade após análise
        background_tasks.add_task(create_opportunity_after_analysis, contact.id)
        
        return WebhookResponse(
            success=True,
            message="Contato criado com sucesso. Análise iniciada e oportunidade será criada automaticamente após análise.",
            contact_id=contact.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar webhook: {str(e)}"
        )

@router.get("/health")
async def webhook_health():
    """Endpoint de health check para webhooks"""
    return {
        "status": "ok",
        "service": "webhooks",
        "timestamp": datetime.utcnow().isoformat()
    }

