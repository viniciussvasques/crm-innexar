from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.core.database import get_db
from app.models.contact import Contact
from app.models.user import User
from app.api.dependencies import get_current_user, get_user_role_str
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class ContactBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: str = "lead"
    notes: Optional[str] = None
    # Campos opcionais do formulário
    project_type: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    position: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    source: Optional[str] = None
    contact_metadata: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    project_type: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    position: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    source: Optional[str] = None
    contact_metadata: Optional[str] = None

class ContactResponse(ContactBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[ContactResponse])
async def list_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    # Vendedor vê apenas seus contatos, admin vê todos
    query = select(Contact)
    if get_user_role_str(current_user) == "vendedor":
        query = query.where(Contact.owner_id == current_user.id)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    contacts = result.scalars().all()
    return [ContactResponse.model_validate(contact) for contact in contacts]

@router.post("/", response_model=ContactResponse)
async def create_contact(
    contact_data: ContactCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact = Contact(
        **contact_data.model_dump(),
        owner_id=current_user.id
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    
    # Se for um lead, iniciar análise automática
    if contact.status == "lead":
        from app.api.lead_analysis import analyze_lead_background
        background_tasks.add_task(analyze_lead_background, contact.id)
    
    return ContactResponse.model_validate(contact)

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Contact).where(Contact.id == contact_id)
    if get_user_role_str(current_user) == "vendedor":
        query = query.where(Contact.owner_id == current_user.id)
    
    result = await db.execute(query)
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    
    return ContactResponse.model_validate(contact)

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact_data: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Contact).where(Contact.id == contact_id)
    if get_user_role_str(current_user) == "vendedor":
        query = query.where(Contact.owner_id == current_user.id)
    
    result = await db.execute(query)
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    
    for key, value in contact_data.model_dump(exclude_unset=True).items():
        setattr(contact, key, value)
    
    await db.commit()
    await db.refresh(contact)
    return ContactResponse.model_validate(contact)

@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Contact).where(Contact.id == contact_id)
    if get_user_role_str(current_user) == "vendedor":
        query = query.where(Contact.owner_id == current_user.id)
    
    result = await db.execute(query)
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    
    await db.delete(contact)
    await db.commit()
    return {"message": "Contato deletado"}

