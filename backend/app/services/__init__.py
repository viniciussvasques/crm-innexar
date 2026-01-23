"""Services module for Innexar CRM."""
from .email_service import EmailService, email_service
from .config_service import ConfigService

__all__ = ["EmailService", "email_service", "ConfigService"]
