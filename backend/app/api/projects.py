from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.project import Project, ProjectStatus, ProjectType
from app.models.user import User, UserRole
from typing import List, Optional
from app.models.contact import Contact
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from app.api.dependencies import get_current_user, get_user_role_str, is_user_role
from datetime import datetime

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("", response_model=List[ProjectListResponse])
async def list_projects(
    status_filter: Optional[ProjectStatus] = None,
    project_type: Optional[ProjectType] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista projetos - vendedores veem apenas os seus, admin vê todos"""
    query = select(Project).options(
        selectinload(Project.contact),
        selectinload(Project.owner),
        selectinload(Project.planning_owner),
        selectinload(Project.dev_owner)
    )
    
    # Filtros de permissão
    user_role = get_user_role_str(current_user)
    if user_role == "vendedor":
        query = query.where(Project.owner_id == current_user.id)
    elif user_role == "planejamento":
        # Planejamento vê projetos atribuídos a eles
        query = query.where(Project.planning_owner_id == current_user.id)
    elif user_role == "dev":
        # Dev vê projetos atribuídos a eles
        query = query.where(Project.dev_owner_id == current_user.id)
    # Admin vê todos (sem filtro adicional)
    
    # Filtros opcionais
    if status_filter:
        query = query.where(Project.status == status_filter)
    if project_type:
        query = query.where(Project.project_type == project_type)
    
    query = query.order_by(Project.created_at.desc())
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    return [
        ProjectListResponse(
            id=p.id,
            name=p.name,
            status=p.status,
            project_type=p.project_type,
            contact_name=p.contact.name if p.contact else "",
            owner_name=p.owner.name if p.owner else "",
            planning_owner_name=p.planning_owner.name if p.planning_owner else None,
            dev_owner_name=p.dev_owner.name if p.dev_owner else None,
            estimated_value=p.estimated_value,
            expected_delivery_date=p.expected_delivery_date,
            created_at=p.created_at
        )
        for p in projects
    ]

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtém detalhes de um projeto"""
    query = select(Project).options(
        selectinload(Project.contact),
        selectinload(Project.owner),
        selectinload(Project.planning_owner),
        selectinload(Project.dev_owner)
    ).where(Project.id == project_id)
    
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Verificar permissões
    user_role = get_user_role_str(current_user)
    if user_role == "vendedor" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para acessar este projeto")
    if user_role == "planejamento" and project.planning_owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para acessar este projeto")
    if user_role == "dev" and project.dev_owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para acessar este projeto")
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        contact_id=project.contact_id,
        opportunity_id=project.opportunity_id,
        project_type=project.project_type,
        status=project.status,
        owner_id=project.owner_id,
        planning_owner_id=project.planning_owner_id,
        dev_owner_id=project.dev_owner_id,
        estimated_value=project.estimated_value,
        approved_value=project.approved_value,
        start_date=project.start_date,
        expected_delivery_date=project.expected_delivery_date,
        actual_delivery_date=project.actual_delivery_date,
        technical_requirements=project.technical_requirements,
        tech_stack=project.tech_stack,
        repository_url=project.repository_url,
        deployment_url=project.deployment_url,
        created_at=project.created_at,
        updated_at=project.updated_at,
        sent_to_planning_at=project.sent_to_planning_at,
        sent_to_dev_at=project.sent_to_dev_at,
        contact_name=project.contact.name if project.contact else "",
        owner_name=project.owner.name if project.owner else "",
        planning_owner_name=project.planning_owner.name if project.planning_owner else None,
        dev_owner_name=project.dev_owner.name if project.dev_owner else None
    )

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cria um novo projeto"""
    # Verificar se o contato existe
    contact = await db.get(Contact, project_data.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    
    # Verificar se a oportunidade existe (se fornecida)
    if project_data.opportunity_id:
        from app.models.opportunity import Opportunity
        opportunity = await db.get(Opportunity, project_data.opportunity_id)
        if not opportunity:
            raise HTTPException(status_code=404, detail="Oportunidade não encontrada")
    
    # Criar projeto
    project = Project(
        name=project_data.name,
        description=project_data.description,
        contact_id=project_data.contact_id,
        opportunity_id=project_data.opportunity_id,
        owner_id=current_user.id,
        project_type=project_data.project_type,
        status=ProjectStatus.LEAD,
        estimated_value=project_data.estimated_value,
        technical_requirements=project_data.technical_requirements,
        tech_stack=project_data.tech_stack
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    # Carregar relacionamentos
    await db.refresh(project, ["contact", "owner", "planning_owner", "dev_owner"])
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        contact_id=project.contact_id,
        opportunity_id=project.opportunity_id,
        project_type=project.project_type,
        status=project.status,
        owner_id=project.owner_id,
        planning_owner_id=project.planning_owner_id,
        dev_owner_id=project.dev_owner_id,
        estimated_value=project.estimated_value,
        approved_value=project.approved_value,
        start_date=project.start_date,
        expected_delivery_date=project.expected_delivery_date,
        actual_delivery_date=project.actual_delivery_date,
        technical_requirements=project.technical_requirements,
        tech_stack=project.tech_stack,
        repository_url=project.repository_url,
        deployment_url=project.deployment_url,
        created_at=project.created_at,
        updated_at=project.updated_at,
        sent_to_planning_at=project.sent_to_planning_at,
        sent_to_dev_at=project.sent_to_dev_at,
        contact_name=project.contact.name if project.contact else "",
        owner_name=project.owner.name if project.owner else "",
        planning_owner_name=project.planning_owner.name if project.planning_owner else None,
        dev_owner_name=project.dev_owner.name if project.dev_owner else None
    )

@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza um projeto"""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Verificar permissões
    user_role = get_user_role_str(current_user)
    if user_role == "vendedor" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para editar este projeto")
    if user_role == "planejamento" and project.planning_owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para editar este projeto")
    if user_role == "dev" and project.dev_owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para editar este projeto")
    
    # Atualizar campos
    update_data = project_data.model_dump(exclude_unset=True)
    
    # Se mudando status para EM_PLANEJAMENTO e tem planejamento, registrar data
    if update_data.get("status") == ProjectStatus.EM_PLANEJAMENTO and project.planning_owner_id:
        if not project.sent_to_planning_at:
            update_data["sent_to_planning_at"] = datetime.utcnow()
    
    # Se mudando status para EM_DESENVOLVIMENTO e tem dev, registrar data
    if update_data.get("status") == ProjectStatus.EM_DESENVOLVIMENTO and project.dev_owner_id:
        if not project.sent_to_dev_at:
            update_data["sent_to_dev_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(project)
    await db.refresh(project, ["contact", "owner", "planning_owner", "dev_owner"])
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        contact_id=project.contact_id,
        opportunity_id=project.opportunity_id,
        project_type=project.project_type,
        status=project.status,
        owner_id=project.owner_id,
        planning_owner_id=project.planning_owner_id,
        dev_owner_id=project.dev_owner_id,
        estimated_value=project.estimated_value,
        approved_value=project.approved_value,
        start_date=project.start_date,
        expected_delivery_date=project.expected_delivery_date,
        actual_delivery_date=project.actual_delivery_date,
        technical_requirements=project.technical_requirements,
        tech_stack=project.tech_stack,
        repository_url=project.repository_url,
        deployment_url=project.deployment_url,
        created_at=project.created_at,
        updated_at=project.updated_at,
        sent_to_planning_at=project.sent_to_planning_at,
        sent_to_dev_at=project.sent_to_dev_at,
        contact_name=project.contact.name if project.contact else "",
        owner_name=project.owner.name if project.owner else "",
        planning_owner_name=project.planning_owner.name if project.planning_owner else None,
        dev_owner_name=project.dev_owner.name if project.dev_owner else None
    )

@router.post("/{project_id}/send-to-planning", response_model=ProjectResponse)
async def send_to_planning(
    project_id: int,
    planning_owner_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Envia projeto para equipe de planejamento (apenas vendedor/admin)"""
    if current_user.role in [UserRole.PLANEJAMENTO, UserRole.DEV]:
        raise HTTPException(status_code=403, detail="Apenas vendedores e admins podem enviar projetos para planejamento")
    
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Verificar se o usuário de planejamento existe
    planning_user = await db.get(User, planning_owner_id)
    if not planning_user:
        raise HTTPException(status_code=404, detail="Usuário de planejamento não encontrado")
    if get_user_role_str(planning_user) != "planejamento":
        raise HTTPException(status_code=400, detail="Usuário deve ser da equipe de planejamento")
    
    # Verificar permissões
    user_role = get_user_role_str(current_user)
    if user_role == "vendedor" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para enviar este projeto")
    
    # Atualizar projeto
    project.planning_owner_id = planning_owner_id
    project.status = ProjectStatus.EM_PLANEJAMENTO
    project.sent_to_planning_at = datetime.utcnow()
    project.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(project)
    await db.refresh(project, ["contact", "owner", "planning_owner", "dev_owner"])
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        contact_id=project.contact_id,
        opportunity_id=project.opportunity_id,
        project_type=project.project_type,
        status=project.status,
        owner_id=project.owner_id,
        planning_owner_id=project.planning_owner_id,
        dev_owner_id=project.dev_owner_id,
        estimated_value=project.estimated_value,
        approved_value=project.approved_value,
        start_date=project.start_date,
        expected_delivery_date=project.expected_delivery_date,
        actual_delivery_date=project.actual_delivery_date,
        technical_requirements=project.technical_requirements,
        tech_stack=project.tech_stack,
        repository_url=project.repository_url,
        deployment_url=project.deployment_url,
        created_at=project.created_at,
        updated_at=project.updated_at,
        sent_to_planning_at=project.sent_to_planning_at,
        sent_to_dev_at=project.sent_to_dev_at,
        contact_name=project.contact.name if project.contact else "",
        owner_name=project.owner.name if project.owner else "",
        planning_owner_name=project.planning_owner.name if project.planning_owner else None,
        dev_owner_name=project.dev_owner.name if project.dev_owner else None
    )

@router.post("/{project_id}/send-to-dev", response_model=ProjectResponse)
async def send_to_dev(
    project_id: int,
    dev_owner_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Envia projeto para equipe de desenvolvimento (planejamento/admin)"""
    user_role = get_user_role_str(current_user)
    if user_role == "vendedor":
        raise HTTPException(status_code=403, detail="Apenas planejamento e admins podem enviar projetos para desenvolvimento")
    
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Verificar se o dev existe
    dev_user = await db.get(User, dev_owner_id)
    if not dev_user:
        raise HTTPException(status_code=404, detail="Usuário de desenvolvimento não encontrado")
    if get_user_role_str(dev_user) != "dev":
        raise HTTPException(status_code=400, detail="Usuário deve ser da equipe de desenvolvimento")
    
    # Verificar permissões
    if user_role == "planejamento" and project.planning_owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão para enviar este projeto")
    
    # Atualizar projeto
    project.dev_owner_id = dev_owner_id
    if project.status == ProjectStatus.APROVADO:
        project.status = ProjectStatus.EM_DESENVOLVIMENTO
    project.sent_to_dev_at = datetime.utcnow()
    project.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(project)
    await db.refresh(project, ["contact", "owner", "planning_owner", "dev_owner"])
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        contact_id=project.contact_id,
        opportunity_id=project.opportunity_id,
        project_type=project.project_type,
        status=project.status,
        owner_id=project.owner_id,
        planning_owner_id=project.planning_owner_id,
        dev_owner_id=project.dev_owner_id,
        estimated_value=project.estimated_value,
        approved_value=project.approved_value,
        start_date=project.start_date,
        expected_delivery_date=project.expected_delivery_date,
        actual_delivery_date=project.actual_delivery_date,
        technical_requirements=project.technical_requirements,
        tech_stack=project.tech_stack,
        repository_url=project.repository_url,
        deployment_url=project.deployment_url,
        created_at=project.created_at,
        updated_at=project.updated_at,
        sent_to_planning_at=project.sent_to_planning_at,
        sent_to_dev_at=project.sent_to_dev_at,
        contact_name=project.contact.name if project.contact else "",
        owner_name=project.owner.name if project.owner else "",
        planning_owner_name=project.planning_owner.name if project.planning_owner else None,
        dev_owner_name=project.dev_owner.name if project.dev_owner else None
    )

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deleta um projeto (apenas admin)"""
    if get_user_role_str(current_user) != "admin":
        raise HTTPException(status_code=403, detail="Apenas admins podem deletar projetos")
    
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    await db.delete(project)
    await db.commit()
    
    return None

