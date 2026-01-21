from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum


class SiteOrderStatus(str, enum.Enum):
    """Status do pedido de site"""
    PENDING_PAYMENT = "pending_payment"  # Aguardando pagamento
    PAID = "paid"  # Pago, aguardando onboarding
    ONBOARDING_PENDING = "onboarding_pending"  # Aguardando cliente preencher
    BUILDING = "building"  # Em construção
    REVIEW = "review"  # Em revisão pelo cliente
    DELIVERED = "delivered"  # Entregue
    CANCELLED = "cancelled"  # Cancelado/Reembolsado


class SiteNiche(str, enum.Enum):
    """Nichos de template disponíveis"""
    RESTAURANT = "restaurant"
    LAWYER = "lawyer"
    DENTIST = "dentist"
    REAL_ESTATE = "real_estate"
    GENERAL = "general"
    PLUMBER = "plumber"
    ELECTRICIAN = "electrician"
    LANDSCAPING = "landscaping"
    CLEANING = "cleaning"
    OTHER = "other"


class SiteTone(str, enum.Enum):
    """Tom do site"""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    PREMIUM = "premium"


class SiteCTA(str, enum.Enum):
    """Call to action principal"""
    CALL = "call"
    WHATSAPP = "whatsapp"
    FORM = "form"
    BOOK_ONLINE = "book_online"


class SiteOrder(Base):
    """Pedido de site - tabela principal"""
    __tablename__ = "site_orders"

    id = Column(Integer, primary_key=True, index=True)
    
    # Stripe
    stripe_session_id = Column(String, unique=True, index=True)
    stripe_customer_id = Column(String, index=True)
    stripe_payment_intent_id = Column(String, nullable=True)
    
    # Cliente
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False, index=True)
    customer_phone = Column(String, nullable=True)
    
    # Pedido
    status = Column(SQLEnum(SiteOrderStatus), default=SiteOrderStatus.PENDING_PAYMENT, index=True)
    base_price = Column(Float, default=399.0)
    total_price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    
    # Prazos
    delivery_days = Column(Integer, default=5)
    expected_delivery_date = Column(DateTime, nullable=True)
    actual_delivery_date = Column(DateTime, nullable=True)
    
    # Revisões
    revisions_included = Column(Integer, default=2)
    revisions_used = Column(Integer, default=0)
    
    # Resultado
    site_url = Column(String, nullable=True)
    repository_url = Column(String, nullable=True)
    
    # Notas
    admin_notes = Column(Text, nullable=True)
    
    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    onboarding_completed_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Relationships
    onboarding = relationship("SiteOnboarding", back_populates="order", uselist=False)
    addons = relationship("SiteOrderAddon", back_populates="order")


class SiteOnboarding(Base):
    """Dados do onboarding preenchidos pelo cliente"""
    __tablename__ = "site_onboardings"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("site_orders.id"), nullable=False, unique=True)
    
    # ============ STEP 1: Business Identity ============
    business_name = Column(String, nullable=False)
    business_email = Column(String, nullable=False)
    business_phone = Column(String, nullable=False)
    has_whatsapp = Column(Boolean, default=False)
    business_address = Column(String, nullable=True)
    
    # ============ STEP 2: Niche & Location ============
    niche = Column(SQLEnum(SiteNiche), nullable=False)
    custom_niche = Column(String, nullable=True)  # Custom niche when 'other' is selected
    primary_city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    service_areas = Column(JSON, nullable=True)  # ["City 1", "City 2", ...]
    
    # ============ STEP 3: Services ============
    services = Column(JSON, nullable=False)  # ["service1", "service2", ...]
    primary_service = Column(String, nullable=False)
    service_descriptions = Column(JSON, nullable=True)  # {"service1": "desc", ...}
    
    # ============ STEP 4: Site Objective & Pages ============
    site_objective = Column(String, nullable=True)  # generate_leads, show_portfolio, sell_products, inform
    site_description = Column(Text, nullable=True)  # Brief about the business
    
    # Pages selection
    selected_pages = Column(JSON, nullable=True)  # ["home", "about", "services", "contact", "gallery", "testimonials", "faq", "pricing"]
    total_pages = Column(Integer, default=5)  # Number of pages included
    
    # Content preferences
    tone = Column(SQLEnum(SiteTone), default=SiteTone.PROFESSIONAL)
    primary_cta = Column(SQLEnum(SiteCTA), default=SiteCTA.CALL)
    cta_text = Column(String, nullable=True)  # Custom CTA text like "Get Free Quote"
    
    # ============ STEP 5: Design & Colors ============
    primary_color = Column(String, nullable=True)  # Hex color
    secondary_color = Column(String, nullable=True)
    accent_color = Column(String, nullable=True)
    
    logo_url = Column(String, nullable=True)  # Uploaded logo
    has_existing_logo = Column(Boolean, default=False)
    brand_fonts = Column(String, nullable=True)  # Preferred font family
    
    # Reference/Inspiration
    reference_sites = Column(JSON, nullable=True)  # ["https://...", ...]
    design_notes = Column(Text, nullable=True)  # Additional design preferences
    
    # ============ STEP 6: Business Details ============
    business_hours = Column(JSON, nullable=True)  # {"mon": "9am-5pm", ...}
    
    # Social Media
    social_facebook = Column(String, nullable=True)
    social_instagram = Column(String, nullable=True)
    social_linkedin = Column(String, nullable=True)
    social_youtube = Column(String, nullable=True)
    social_tiktok = Column(String, nullable=True)
    
    # ============ STEP 7: Testimonials ============
    testimonials = Column(JSON, nullable=True)  # [{"name": "John", "text": "Great!", "role": "Customer"}, ...]
    google_reviews_link = Column(String, nullable=True)  # Link to Google reviews
    
    # About content
    about_owner = Column(Text, nullable=True)  # Story about the owner/business
    years_in_business = Column(Integer, nullable=True)
    team_members = Column(JSON, nullable=True)  # [{"name": "John", "role": "Manager", "photo": "url"}, ...]
    
    # ============ SEO ============
    meta_title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    target_keywords = Column(JSON, nullable=True)  # ["keyword1", "keyword2", ...]
    
    # ============ Metadata ============
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_steps = Column(Integer, default=0)  # Track progress
    is_complete = Column(Boolean, default=False)
    
    # Relationships
    order = relationship("SiteOrder", back_populates="onboarding")



class SiteAddon(Base):
    """Add-ons disponíveis para venda"""
    __tablename__ = "site_addons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    is_subscription = Column(Boolean, default=False)
    subscription_interval = Column(String, nullable=True)  # 'month', 'year'
    stripe_price_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class SiteOrderAddon(Base):
    """Add-ons comprados em um pedido"""
    __tablename__ = "site_order_addons"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("site_orders.id"), nullable=False)
    addon_id = Column(Integer, ForeignKey("site_addons.id"), nullable=False)
    price_paid = Column(Float, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("SiteOrder", back_populates="addons")
    addon = relationship("SiteAddon")


class SiteTemplate(Base):
    """Templates de site disponíveis"""
    __tablename__ = "site_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True)
    niche = Column(SQLEnum(SiteNiche), nullable=False, index=True)
    description = Column(Text, nullable=True)
    preview_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    
    # Configurações padrão
    default_colors = Column(JSON, nullable=True)  # {"primary": "#hex", "secondary": "#hex"}
    default_sections = Column(JSON, nullable=True)  # ["hero", "services", "about", ...]
    
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
