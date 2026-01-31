from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.models.site_order import SiteOrder, SiteOrderStatus
from app.models.site_contract import SiteContract

router = APIRouter(prefix="/site-contracts", tags=["site-contracts"])

class ContractCreate(BaseModel):
    order_id: int
    content: str
    signed_name: str
    signed_email: Optional[str] = None
    language: str = "pt"

class ContractResponse(BaseModel):
    id: int
    order_id: int
    signed_name: str
    signed_at: datetime
    language: str
    
    class Config:
        from_attributes = True

@router.get("/order/{order_id}")
async def get_contract_by_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get signed contract for an order"""
    result = await db.execute(
        select(SiteContract).where(SiteContract.order_id == order_id)
    )
    contract = result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
        
    return {
        "id": contract.id,
        "order_id": contract.order_id,
        "content": contract.content,
        "signed_name": contract.signed_name,
        "signed_at": contract.signed_at,
        "language": contract.language
    }

@router.post("/sign")
async def sign_contract(
    contract_data: ContractCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Sign a contract for a site order"""
    # Check if order exists
    result = await db.execute(
        select(SiteOrder).where(SiteOrder.id == contract_data.order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # Check if already signed
    result = await db.execute(
        select(SiteContract).where(SiteContract.order_id == contract_data.order_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return {"message": "Contract already signed", "id": existing.id}
        
    # Create contract
    contract = SiteContract(
        order_id=contract_data.order_id,
        content=contract_data.content,
        signed_name=contract_data.signed_name,
        signed_email=contract_data.signed_email or order.customer_email,
        language=contract_data.language,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        signed_at=datetime.utcnow()
    )
    
    db.add(contract)
    
    # Update order status if it was in onboarding
    # We might want to keep it in onboarding until the very end, 
    # but signing is usually the last step.
    
    await db.commit()
    await db.refresh(contract)
    
    return {"message": "Contract signed successfully", "id": contract.id}
