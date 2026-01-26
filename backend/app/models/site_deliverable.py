from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

class DeliverableType(str, enum.Enum):
    """Tipo do entregável"""
    BRIEFING = "briefing"           # Estratégia, Público, Diferenciais
    SITEMAP = "sitemap"             # Arquitetura, UX Flow
    CONTENT_PLAN = "content_plan"   # Estratégia de Conteúdo (SEO, Headlines)
    WIREFRAME = "wireframe"         # (Opcional) Low-fidelity visual
    CODE = "code"                   # O código final (Next.js)

class DeliverableStatus(str, enum.Enum):
    """Status do entregável"""
    PENDING = "pending"         # Na fila
    GENERATING = "generating"   # IA trabalhando
    READY = "ready"             # Pronto para revisão
    APPROVED = "approved"       # Aprovado pelo cliente/admin
    REJECTED = "rejected"       # Rejeitado (precisa regenerar)

class SiteDeliverable(Base):
    """Entregáveis do processo de construção do site"""
    __tablename__ = "site_deliverables"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("site_orders.id"), nullable=False, index=True)
    
    type = Column(SQLEnum(DeliverableType), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)  # Markdown ou JSON stringified
    
    # Metadados opcionais (ex: link para PDF, JSON estruturado extra)
    metadata_json = Column(JSON, nullable=True)
    
    status = Column(SQLEnum(DeliverableStatus), default=DeliverableStatus.PENDING, index=True)
    is_visible_to_client = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = relationship("SiteOrder", back_populates="deliverables")
