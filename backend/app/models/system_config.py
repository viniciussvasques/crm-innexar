from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import json


class SystemConfig(Base):
    """
    System-wide configuration stored in database.
    Replaces environment variables for configurable settings.
    """
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    value_type = Column(String, default="string")  # string, json, boolean, number
    category = Column(String, index=True)  # stripe, email, site, general
    description = Column(Text, nullable=True)
    is_secret = Column(Boolean, default=False)  # If true, value is masked in responses
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_value(self):
        """Get the properly typed value"""
        if self.value is None:
            return None
        
        if self.value_type == "boolean":
            return self.value.lower() in ("true", "1", "yes")
        elif self.value_type == "number":
            try:
                return float(self.value) if "." in self.value else int(self.value)
            except ValueError:
                return 0
        elif self.value_type == "json":
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return {}
        return self.value

    def get_masked_value(self):
        """Get value with masking for secrets"""
        if self.is_secret and self.value:
            if len(self.value) > 8:
                return self.value[:4] + "****" + self.value[-4:]
            return "****"
        return self.value


# Default configurations to seed
DEFAULT_CONFIGS = [
    # Stripe
    {"key": "stripe_secret_key", "category": "stripe", "description": "Stripe Secret Key (sk_...)", "is_secret": True},
    {"key": "stripe_publishable_key", "category": "stripe", "description": "Stripe Publishable Key (pk_...)", "is_secret": False},
    {"key": "stripe_webhook_secret", "category": "stripe", "description": "Stripe Webhook Secret (whsec_...)", "is_secret": True},
    {"key": "stripe_enabled", "category": "stripe", "value_type": "boolean", "value": "false", "description": "Enable Stripe payments"},
    {"key": "stripe_hosting_price_id", "category": "stripe", "description": "Stripe Price ID for hosting subscription ($9.99/month)", "is_secret": False},
    {"key": "hosting_trial_days", "category": "stripe", "value": "90", "value_type": "number", "description": "Free trial days for hosting (default: 90 = 3 months)"},
    
    # Dynadot
    {"key": "dynadot_api_key", "category": "dynadot", "description": "Dynadot API Key", "is_secret": True},
    {"key": "dynadot_api_secret", "category": "dynadot", "description": "Dynadot API Secret", "is_secret": True},
    {"key": "dynadot_max_domain_price", "category": "dynadot", "value": "15.00", "value_type": "number", "description": "Maximum domain price for free domain offer ($)"},
    
    # Email
    {"key": "email_provider", "category": "email", "value": "smtp", "description": "Email provider: smtp, resend, mailgun"},
    {"key": "smtp_host", "category": "email", "description": "SMTP server host"},
    {"key": "smtp_port", "category": "email", "value": "587", "value_type": "number", "description": "SMTP server port"},
    {"key": "smtp_user", "category": "email", "description": "SMTP username/email"},
    {"key": "smtp_password", "category": "email", "description": "SMTP password", "is_secret": True},
    {"key": "smtp_from_email", "category": "email", "description": "From email address"},
    {"key": "smtp_from_name", "category": "email", "value": "Innexar", "description": "From name"},
    
    # Site Sales Settings
    {"key": "site_base_price", "category": "site", "value": "399", "value_type": "number", "description": "Base price for Launch Site ($)"},
    {"key": "site_delivery_days", "category": "site", "value": "5", "value_type": "number", "description": "Default delivery days"},
    {"key": "site_revisions_included", "category": "site", "value": "2", "value_type": "number", "description": "Revisions included in base price"},
    
    # General
    {"key": "company_name", "category": "general", "value": "Innexar", "description": "Company name"},
    {"key": "support_email", "category": "general", "description": "Support email address"},
    {"key": "notification_email", "category": "general", "description": "Internal notification email"},
    
    # Marketing & Analytics
    {"key": "google_analytics_id", "category": "marketing", "description": "Google Analytics 4 ID (G-XXXXXXXX)"},
    {"key": "google_ads_id", "category": "marketing", "description": "Google Ads Conversion ID (AW-XXXXXXXX)"},
    {"key": "meta_pixel_id", "category": "marketing", "description": "Meta Pixel ID"},
]
