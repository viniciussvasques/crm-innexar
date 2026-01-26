"""
Schemas for Storage Configuration (S3/R2)
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class StorageConfigBase(BaseModel):
    """Base storage configuration"""
    provider: Literal["cloudflare_r2", "aws_s3"]
    bucket_name: str = Field(..., description="Bucket name")
    access_key_id: str = Field(..., description="Access Key ID (secret)")
    secret_access_key: str = Field(..., description="Secret Access Key (secret)")
    endpoint_url: Optional[str] = Field(None, description="Custom endpoint URL (for R2)")
    region: Optional[str] = Field(None, description="Region (for S3)")

class StorageConfigCreate(StorageConfigBase):
    """Create storage configuration"""
    pass

class StorageConfigUpdate(BaseModel):
    """Update storage configuration"""
    bucket_name: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    region: Optional[str] = None
    is_active: Optional[bool] = None

class StorageConfigResponse(BaseModel):
    """Storage configuration response"""
    id: int
    provider: str
    bucket_name: str
    access_key_id: str  # Masked in actual response
    endpoint_url: Optional[str] = None
    region: Optional[str] = None
    is_active: bool
    last_tested_at: Optional[datetime] = None
    last_test_success: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
