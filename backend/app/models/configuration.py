"""
Models for System Configuration and Integrations
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

class IntegrationType(str, enum.Enum):
    GITHUB = "github"
    CLOUDFLARE = "cloudflare"
    STRIPE = "stripe"
    MAILCOW = "mailcow"
    OLLAMA = "ollama"
    OTHER = "other"

class ServerType(str, enum.Enum):
    SSH = "ssh"
    FTP = "ftp"
    API = "api"
    CLOUDFLARE_PAGES = "cloudflare_pages"

class IntegrationConfig(Base):
    """Generic configuration for external integrations"""
    __tablename__ = "integration_configs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Identification
    integration_type = Column(String(50), nullable=False)  # github, cloudflare, etc
    key = Column(String(100), nullable=False)  # e.g. 'api_token', 'webhook_secret'
    
    # Value (Encrypted if is_secret is True)
    value = Column(Text, nullable=False)
    is_secret = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    
    # Metadata
    last_tested_at = Column(DateTime, nullable=True)
    last_test_success = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('integration_type', 'key', name='uix_integration_key'),
    )

class DeployServer(Base):
    """Dedicated servers or platforms for deployment"""
    __tablename__ = "deploy_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    server_type = Column(String(50), default=ServerType.SSH)
    
    # Connection Details
    host = Column(String(255), nullable=True)
    port = Column(Integer, default=22)
    username = Column(String(100), nullable=True)
    
    # Credentials (Encrypted)
    password_encrypted = Column(Text, nullable=True)
    ssh_key_encrypted = Column(Text, nullable=True)
    
    # Paths
    deploy_path = Column(String(500), nullable=True)
    
    # Config
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Metrics
    disk_total_gb = Column(Integer, nullable=True)
    disk_used_gb = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
