"""Customer Authentication Schemas"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    customer_id: int
    email: str


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class CustomerProfile(BaseModel):
    id: int
    email: str
    email_verified: bool
    order_id: Optional[int]


class OrderSummary(BaseModel):
    id: int
    customer_name: str
    status: str
    total_price: float
    created_at: Optional[str]
    expected_delivery_date: Optional[str]
    site_url: Optional[str]
    onboarding: Optional[dict]
