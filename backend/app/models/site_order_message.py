from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class SiteOrderMessage(Base):
    """Mensagens de comunicação entre equipe e cliente durante o pipeline"""
    __tablename__ = "site_order_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("site_orders.id"), nullable=False, index=True)
    
    # Remetente
    sender_type = Column(String, nullable=False)  # "admin" ou "client"
    sender_id = Column(Integer, nullable=True)  # user_id (se admin) ou customer_id (se client)
    sender_name = Column(String, nullable=True)  # Nome para exibição
    
    # Conteúdo
    message = Column(Text, nullable=True)  # Mensagem de texto (opcional se tiver apenas arquivos/links)
    message_type = Column(String, default="message")  # "message", "file", "link", "status_update"
    
    # Arquivos (array de URLs ou paths)
    files = Column(JSON, nullable=True)  # [{"name": "logo.png", "url": "...", "size": 1234}, ...]
    
    # Links
    links = Column(JSON, nullable=True)  # [{"title": "Preview", "url": "...", "description": "..."}, ...]
    
    # Metadados
    is_read = Column(Boolean, default=False)  # Cliente leu?
    is_important = Column(Boolean, default=False)  # Mensagem importante/pinada
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    order = relationship("SiteOrder", back_populates="messages")
