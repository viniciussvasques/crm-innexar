"""
Configuration Service
Handles encryption/decryption and management of dynamic configurations.
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from cryptography.fernet import Fernet
import os
import json
from app.models.configuration import IntegrationConfig, DeployServer, IntegrationType, ServerType
from app.core.config import settings
from datetime import datetime

class ConfigService:
    def __init__(self, db: Session):
        self.db = db
        # Use SECRET_KEY or specific ENCRYPTION_KEY from env
        key = os.getenv("ENCRYPTION_KEY", os.getenv("SECRET_KEY"))
        # Ensure key is 32 url-safe base64-encoded bytes for Fernet
        # This is a naive implementation; in prod use a proper key management
        if not key:
            raise ValueError("ENCRYPTION_KEY or SECRET_KEY must be set")
            
        # Pad or cut key to 32 bytes for Fernet safety if needed (just for dev stability)
        # In real scenario, we expect a valid base64 key. 
        # For now, we assume settings.SECRET_KEY is usable or we generate one.
        try:
           self.cipher = Fernet(key)
        except Exception:
           # If key is not valid fernet, generating a temp one (NOT FOR PROD persistence across restarts if key changes)
           # Ideally we rely on a proper key.
           # STARTUP WARNING: This might break if key changes.
           import base64
           # Create a 32-byte key from the secret
           k = base64.urlsafe_b64encode(key.encode()[:32].ljust(32, b'x'))
           self.cipher = Fernet(k)

    def encrypt_value(self, value: str) -> str:
        """Encrypt a value"""
        if not value:
            return value
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a value"""
        if not encrypted_value:
            return encrypted_value
        try:
            return self.cipher.decrypt(encrypted_value.encode()).decode()
        except Exception:
            return "[Error Decrypting]"

    def set_config(self, type: IntegrationType, key: str, value: str, is_secret: bool = False, description: str = None) -> IntegrationConfig:
        """Set a configuration value"""
        stmt = select(IntegrationConfig).where(
            IntegrationConfig.integration_type == type,
            IntegrationConfig.key == key
        )
        config = self.db.execute(stmt).scalar_one_or_none()
        
        final_value = self.encrypt_value(value) if is_secret else value
        
        if config:
            config.value = final_value
            config.is_secret = is_secret
            if description:
                config.description = description
            config.updated_at = datetime.utcnow()
        else:
            config = IntegrationConfig(
                integration_type=type,
                key=key,
                value=final_value,
                is_secret=is_secret,
                description=description
            )
            self.db.add(config)
            
        self.db.commit()
        self.db.refresh(config)
        return config

    def get_config(self, type: IntegrationType, key: str) -> Optional[str]:
        """Get a single config value (decrypted)"""
        stmt = select(IntegrationConfig).where(
            IntegrationConfig.integration_type == type,
            IntegrationConfig.key == key,
            IntegrationConfig.is_active == True
        )
        config = self.db.execute(stmt).scalar_one_or_none()
        
        if not config:
            return None
            
        if config.is_secret:
            return self.decrypt_value(config.value)
        return config.value

    def get_all_by_type(self, type: IntegrationType) -> Dict[str, Any]:
        """Get all configs for a type as a dict"""
        stmt = select(IntegrationConfig).where(
            IntegrationConfig.integration_type == type,
            IntegrationConfig.is_active == True
        )
        configs = self.db.execute(stmt).scalars().all()
        
        result = {}
        for c in configs:
            val = self.decrypt_value(c.value) if c.is_secret else c.value
            result[c.key] = val
        return result

    # --- Deploy Server Management ---
    
    def create_deploy_server(self, name: str, type: ServerType, **kwargs) -> DeployServer:
        """Create a new deploy server"""
        # Encrypt sensitive fields
        if 'password' in kwargs:
            kwargs['password_encrypted'] = self.encrypt_value(kwargs.pop('password'))
        if 'ssh_key' in kwargs:
            kwargs['ssh_key_encrypted'] = self.encrypt_value(kwargs.pop('ssh_key'))
            
        server = DeployServer(name=name, server_type=type, **kwargs)
        self.db.add(server)
        self.db.commit()
        self.db.refresh(server)
        return server

    def get_deploy_server_credentials(self, server_id: int) -> Dict[str, str]:
        """Get decrypted credentials for a server"""
        server = self.db.get(DeployServer, server_id)
        if not server:
            return None
            
        creds = {
            "host": server.host,
            "username": server.username,
        }
        if server.password_encrypted:
            creds["password"] = self.decrypt_value(server.password_encrypted)
        if server.ssh_key_encrypted:
            creds["ssh_key"] = self.decrypt_value(server.ssh_key_encrypted)
            
        return creds
