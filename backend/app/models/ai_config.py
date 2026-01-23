"""
Modelo para configurações de IA
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

class AIModelProvider(str, enum.Enum):
    GROK = "grok"  # xAI Grok
    OPENAI = "openai"  # OpenAI GPT
    ANTHROPIC = "anthropic"  # Claude
    OLLAMA = "ollama"  # Ollama (local)
    GOOGLE = "google"  # Google Gemini
    MISTRAL = "mistral"  # Mistral AI
    COHERE = "cohere"  # Cohere

class AIModelStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class AIConfig(Base):
    """Configuração de modelos de IA"""
    __tablename__ = "ai_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Nome amigável (ex: "Helena - Grok")
    provider = Column(String(50), nullable=False)  # grok, openai, anthropic, ollama, etc.
    model_name = Column(String(100), nullable=False)  # Nome do modelo específico
    api_key = Column(Text, nullable=True)  # API key (criptografado em produção)
    base_url = Column(String(500), nullable=True)  # URL base (para Ollama local, etc.)
    is_active = Column(Boolean, default=False)  # Se está ativo
    is_default = Column(Boolean, default=False)  # Se é o modelo padrão
    status = Column(String(20), default=AIModelStatus.INACTIVE.value)  # active, inactive, error
    priority = Column(Integer, default=0)  # Prioridade (maior = mais prioritário)
    
    # Configurações adicionais (JSON)
    config = Column(JSON, nullable=True)  # Configurações específicas do modelo
    
    # Metadados
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_tested_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])


class AITaskRouting(Base):
    """Routing rules for AI tasks to specific models"""
    __tablename__ = "ai_task_routing"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), unique=True, nullable=False)  # code_generation, content_generation, analysis
    
    # Primary Provider
    primary_config_id = Column(Integer, ForeignKey("ai_configs.id"), nullable=False)
    
    # Fallback Provider
    fallback_config_id = Column(Integer, ForeignKey("ai_configs.id"), nullable=True)
    
    # Settings override
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4000)
    
    # Relationships
    primary_config = relationship("AIConfig", foreign_keys=[primary_config_id])
    fallback_config = relationship("AIConfig", foreign_keys=[fallback_config_id])

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


