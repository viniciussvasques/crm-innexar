"""
Site Customer Authentication API
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt

from app.core.database import get_db
from app.core.config import settings
from app.models.site_customer import SiteCustomer
from app.models.site_order import SiteOrder
from app.services.email_service import email_service

router = APIRouter(prefix="/site-customers", tags=["site-customers"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7  # 1 week


# ============== Schemas ==============

class CustomerLogin(BaseModel):
    email: EmailStr
    password: str


class CustomerToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer_id: int
    email: str


class CustomerCreate(BaseModel):
    order_id: int
    email: EmailStr
    password: str


class CustomerResponse(BaseModel):
    id: int
    email: str
    email_verified: bool
    created_at: datetime
    order_id: int
    
    class Config:
        from_attributes = True


class PasswordReset(BaseModel):
    token: str
    new_password: str


# ============== Helper Functions ==============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_customer_token(customer_id: int, email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(customer_id),
        "email": email,
        "type": "customer",
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_customer_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "customer":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ============== Endpoints ==============

@router.post("/login", response_model=CustomerToken)
async def customer_login(
    credentials: CustomerLogin,
    db: AsyncSession = Depends(get_db)
):
    """Customer login - returns JWT token"""
    result = await db.execute(
        select(SiteCustomer).where(SiteCustomer.email == credentials.email.lower())
    )
    customer = result.scalar_one_or_none()
    
    if not customer or not verify_password(credentials.password, customer.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not customer.email_verified:
        raise HTTPException(status_code=403, detail="Email not verified. Please check your inbox.")
    
    # Update last login
    customer.last_login = datetime.utcnow()
    await db.commit()
    
    token = create_customer_token(customer.id, customer.email)
    
    return CustomerToken(
        access_token=token,
        customer_id=customer.id,
        email=customer.email
    )


@router.post("/verify/{token}")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify customer email with token"""
    result = await db.execute(
        select(SiteCustomer).where(SiteCustomer.verification_token == token)
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Invalid verification token")
    
    if customer.email_verified:
        return {"message": "Email already verified"}
    
    customer.email_verified = True
    customer.verified_at = datetime.utcnow()
    customer.verification_token = None
    await db.commit()
    
    return {"message": "Email verified successfully! You can now login."}


@router.get("/me", response_model=CustomerResponse)
async def get_current_customer(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Get current customer info from token"""
    payload = decode_customer_token(token)
    customer_id = int(payload["sub"])
    
    customer = await db.get(SiteCustomer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer


@router.post("/reset-password")
async def reset_password(
    data: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """Reset password with token"""
    result = await db.execute(
        select(SiteCustomer).where(SiteCustomer.reset_token == data.token)
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Invalid reset token")
    
    if customer.reset_token_expires and customer.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token expired")
    
    customer.password_hash = hash_password(data.new_password)
    customer.reset_token = None
    customer.reset_token_expires = None
    await db.commit()
    
    return {"message": "Password reset successfully. You can now login."}


@router.get("/check-email")
async def check_email_exists(
    email: EmailStr,
    db: AsyncSession = Depends(get_db)
):
    """Verifica se um email já está cadastrado no portal"""
    result = await db.execute(
        select(SiteCustomer).where(SiteCustomer.email == email.lower())
    )
    customer = result.scalar_one_or_none()
    return {"exists": customer is not None}


@router.post("/forgot-password")
async def forgot_password(
    email: EmailStr,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset and send email"""
    result = await db.execute(
        select(SiteCustomer).options(selectinload(SiteCustomer.order)).where(SiteCustomer.email == email.lower())
    )
    customer = result.scalar_one_or_none()
    
    # Always return success to prevent email enumeration
    if not customer:
        return {"message": "If an account exists with this email, a reset link will be sent."}
    
    # Generate reset token
    reset_token = SiteCustomer.generate_verification_token()
    customer.reset_token = reset_token
    customer.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    await db.commit()
    
    # Send password reset email
    customer_name = customer.order.customer_name if customer.order else "Cliente"
    background_tasks.add_task(
        email_service.send_password_reset_email,
        customer_name=customer_name,
        to_email=customer.email,
        reset_token=reset_token
    )
    
    return {"message": "If an account exists with this email, a reset link will be sent."}


@router.post("/resend-verification")
async def resend_verification(
    email: EmailStr,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Reenviar email de verificação"""
    result = await db.execute(
        select(SiteCustomer).options(selectinload(SiteCustomer.order)).where(SiteCustomer.email == email.lower())
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if customer.email_verified:
        return {"message": "Email already verified"}
    
    # Check if a verification was sent recently (debounce)
    if customer.verification_sent_at and (datetime.utcnow() - customer.verification_sent_at).seconds < 60:
         raise HTTPException(status_code=429, detail="Please wait a minute before requesting another email")

    # Generate new token and temp password if needed
    verification_token = SiteCustomer.generate_verification_token()
    customer.verification_token = verification_token
    customer.verification_sent_at = datetime.utcnow()
    
    # We don't change the password here by default, but we could generate a new temp one if they lost it
    temp_password = "sua senha cadastrada" # Generic message as we don't store plain text
    
    await db.commit()
    
    customer_name = customer.order.customer_name if customer.order else "Cliente"
    background_tasks.add_task(
        email_service.send_verification_email,
        customer_name=customer_name,
        to_email=customer.email,
        temp_password=temp_password,
        verification_token=verification_token
    )
    
    return {"message": "Verification email resent"}


# ============== Internal Functions (called from onboarding) ==============

async def create_customer_account(
    db: AsyncSession,
    order_id: int,
    email: str,
    password: Optional[str] = None
) -> tuple[SiteCustomer, str]:
    """
    Create a customer account for an order.
    Returns (customer, password_used)
    """
    # Check if customer already exists
    result = await db.execute(
        select(SiteCustomer).where(SiteCustomer.order_id == order_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Customer account already exists for this order")
    
    # Generate credentials if not provided
    actual_password = password or SiteCustomer.generate_temp_password()
    verification_token = SiteCustomer.generate_verification_token()
    
    customer = SiteCustomer(
        order_id=order_id,
        email=email.lower(),
        password_hash=hash_password(actual_password),
        email_verified=False,
        verification_token=verification_token,
        verification_sent_at=datetime.utcnow()
    )
    
    db.add(customer)
    await db.flush()
    
    return customer, actual_password
