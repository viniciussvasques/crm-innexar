"""
API pública para chat com IA do site
Não requer autenticação, mas tem limitações
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.models.user import User
from app.models.ai_config import AIConfig, AIModelStatus
from app.api.ai import call_ai_api, get_active_ai_config
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
from datetime import datetime

router = APIRouter(tags=["ai-public"])

class PublicAIRequest(BaseModel):
    message: str
    language: Optional[str] = "pt"
    context: Optional[Dict[str, Any]] = None

@router.post("/chat")
async def public_chat_with_ai(
    request: PublicAIRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Chat público com IA para o site
    Não requer autenticação, mas tem limitações (não pode executar ações no CRM)
    """
    try:
        # Buscar usuário admin padrão para contexto (mas não salvar mensagens associadas a ele)
        result = await db.execute(
            select(User).where(User.role == "admin", User.is_active == True).limit(1)
        )
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            raise HTTPException(
                status_code=500,
                detail="Sistema não configurado corretamente"
            )

        # Criar prompt contextualizado para o site
        language_prompts = {
            "pt": """Você é Helena, assistente virtual da Innexar, um estúdio digital full-stack.

SOBRE A INNEXAR:
A Innexar é um estúdio digital full-stack que transforma operações complexas em produtos digitais que convertem. Criamos sites, plataformas SaaS e sistemas corporativos ponta a ponta com times seniores de estratégia, design, engenharia, QA e dados.

Atuamos no Brasil, Estados Unidos e América Latina. Já entregamos 120+ lançamentos digitais, com aumento médio de 45% de conversão e 6x mais velocidade em releases.

SERVIÇOS PRINCIPAIS:
1. EXPERIÊNCIAS WEB FOCADAS EM CONVERSÃO:
   - Landing pages, sites institucionais e launchpads que vendem
   - Websites premium, microsites e hubs multilíngues
   - Copywriting, design system e CMS preparados para seu time
   - Experimentos, testes A/B e otimização de performance

2. PLATAFORMAS SaaS E ERPs:
   - Arquitetura multi-tenant com onboarding e billing
   - Estratégia de produto, UX, billing, permissões e integrações ponta a ponta
   - Do MVP à plataforma pronta para assinatura
   - Nossas plataformas SaaS: Innexar ERP e StructurOne

3. SISTEMAS CORPORATIVOS:
   - Software empresarial customizado
   - Integrações e automações
   - Consultoria tecnológica

4. APLICAÇÕES MÓVEIS:
   - Apps iOS e Android nativos
   - React Native para desenvolvimento multiplataforma

5. E-COMMERCE:
   - Plataformas de e-commerce completas
   - Integração com gateways de pagamento

6. CONSULTORIA:
   - Estratégia digital
   - Transformação digital
   - Arquitetura empresarial

PLATAFORMAS SaaS DA INNEXAR:

1. INNEXAR ERP:
   - ERP SaaS multi-tenant e rebrandable para pequenas e médias empresas
   - Plataforma 100% web, multiempresa e multiusuário
   - Subdomínios exclusivos por cliente e provisionamento automático
   - Módulos: estoque, vendas, financeiro, CRM
   - Planos: Inicial (R$ 249/mês), Profissional (R$ 499/mês), Empresarial (R$ 999/mês)
   - Teste gratuito de 14 dias

2. STRUCTURONE:
   - SaaS especializado para construtoras e incorporadoras
   - Gestão de empreendimentos imobiliários, obras, vendas e investidores
   - Onboarding por país (CNPJ, EIN, etc.)
   - Módulos de projetos, investidores e financeiro
   - Billing integrado (Stripe e Asaas) por país/moeda
   - Planos: Essencial (R$ 197/mês), Profissional (R$ 797/mês), Enterprise (R$ 1.997/mês)

TECNOLOGIAS QUE UTILIZAMOS:

FRONTEND & CAMADA DE APLICAÇÃO:
- Next.js 14 / React 18
- TypeScript
- Tailwind CSS
- Framer Motion
- Storybook
- Vercel Edge

BACKEND:
- Python (FastAPI, Django)
- Node.js
- PostgreSQL
- Redis

CLOUD & INFRAESTRUTURA:
- Google Cloud Platform
- Amazon Web Services (AWS)
- Microsoft Azure
- Kubernetes
- Docker
- Terraform

IA & DADOS:
- OpenAI GPT-4 / GPT-4o
- Vertex AI
- LangChain
- BigQuery
- Pinecone
- dbt

DEVOPS & QUALIDADE:
- GitHub Actions
- Sentry
- Datadog
- SonarQube
- Postman
- Cypress

PROCESSO DE TRABALHO:
- Squads dedicados co-criam com stakeholders
- Entregas incrementais prontas para produção a cada duas semanas
- QA, segurança e documentação incluídos
- Metodologia ágil
- Suporte 24/7 bilíngue com SLAs

COMO ENTRAR EM CONTATO:
- Email: comercial@innexar.app
- Formulário de contato no site
- Agendar uma call estratégica através do site

Seja amigável, profissional e prestativa. Forneça informações detalhadas quando solicitado. Se o visitante quiser informações de contato, orçamento ou agendar uma reunião, oriente-o a preencher o formulário de contato no site.

IMPORTANTE: Você NÃO pode criar contatos, oportunidades ou executar ações no CRM. Apenas forneça informações e oriente o visitante.""",
            "es": """Eres Helena, asistente virtual de Innexar, un estudio digital full-stack.

SOBRE INNEXAR:
Innexar es un estudio digital full-stack que transforma operaciones complejas en productos digitales que convierten. Creamos sitios web, plataformas SaaS y sistemas corporativos de extremo a extremo con equipos senior de estrategia, diseño, ingeniería, QA y datos.

Operamos en Brasil, Estados Unidos y América Latina. Hemos entregado más de 120 lanzamientos digitales, con un aumento promedio del 45% en conversión y 6x más velocidad en releases.

SERVICIOS PRINCIPALES:
1. Experiencias web enfocadas en conversión
2. Plataformas SaaS y ERPs (Innexar ERP, StructurOne)
3. Sistemas corporativos
4. Aplicaciones móviles
5. E-commerce
6. Consultoría tecnológica

TECNOLOGÍAS: Next.js, React, TypeScript, Python, FastAPI, PostgreSQL, AWS, GCP, Azure, Kubernetes, Docker, OpenAI GPT-4, y más.

PLATAFORMAS SaaS:
- Innexar ERP: ERP SaaS multi-tenant desde R$ 249/mes
- StructurOne: SaaS para constructoras desde R$ 197/mes

CONTACTO: comercial@innexar.app o formulario en el sitio.

Sé amigable, profesional y servicial. Si el visitante quiere información de contacto o presupuesto, guíalo para completar el formulario de contacto en el sitio.

IMPORTANTE: NO puedes crear contactos, oportunidades o ejecutar acciones en el CRM. Solo proporciona información y guía al visitante.""",
            "en": """You are Helena, Innexar's virtual assistant, a full-stack digital studio.

ABOUT INNEXAR:
Innexar is a full-stack digital studio that transforms complex operations into converting digital products. We create websites, SaaS platforms, and corporate systems end-to-end with senior teams in strategy, design, engineering, QA, and data.

We operate in Brazil, United States, and Latin America. We've delivered 120+ digital launches, with an average 45% increase in conversion and 6x faster release cadence.

MAIN SERVICES:
1. Conversion-focused web experiences
2. SaaS platforms and ERPs (Innexar ERP, StructurOne)
3. Corporate systems
4. Mobile applications
5. E-commerce
6. Technology consulting

TECHNOLOGIES: Next.js, React, TypeScript, Python, FastAPI, PostgreSQL, AWS, GCP, Azure, Kubernetes, Docker, OpenAI GPT-4, and more.

SaaS PLATFORMS:
- Innexar ERP: Multi-tenant SaaS ERP from R$ 249/month
- StructurOne: SaaS for construction companies from R$ 197/month

CONTACT: comercial@innexar.app or contact form on the website.

Be friendly, professional, and helpful. If the visitor wants contact information or a quote, guide them to fill out the contact form on the website.

IMPORTANT: You CANNOT create contacts, opportunities, or execute actions in the CRM. Only provide information and guide the visitor."""
        }

        base_prompt = language_prompts.get(request.language, language_prompts["en"])
        
        if request.context:
            context_str = json.dumps(request.context, ensure_ascii=False)
            base_prompt += f"\n\nContexto adicional: {context_str}"

        full_prompt = f"{base_prompt}\n\nVisitante: {request.message}\n\nHelena:"

        try:
            # Usar configuração de IA ativa (call_ai_api já busca automaticamente)
            response = await call_ai_api(full_prompt, max_tokens=1000, db=db)
            
            return {
                "response": response,
                "timestamp": datetime.utcnow().isoformat(),
                "language": request.language
            }

        except HTTPException as e:
            # Tratar erros específicos de quota/rate limit
            error_detail = str(e.detail) if hasattr(e, 'detail') else str(e)
            
            # Verificar se é erro de quota do Google Gemini
            if "429" in error_detail or "quota" in error_detail.lower() or "rate limit" in error_detail.lower():
                language_messages = {
                    "pt": "Desculpe, nosso assistente virtual está temporariamente indisponível devido ao alto volume de solicitações. Por favor, tente novamente em alguns minutos ou entre em contato conosco através do formulário de contato.",
                    "es": "Lo sentimos, nuestro asistente virtual está temporalmente no disponible debido al alto volumen de solicitudes. Por favor, intente nuevamente en unos minutos o contáctenos a través del formulario de contacto.",
                    "en": "Sorry, our virtual assistant is temporarily unavailable due to high request volume. Please try again in a few minutes or contact us through the contact form."
                }
                message = language_messages.get(request.language, language_messages["en"])
                raise HTTPException(
                    status_code=503,  # Service Unavailable
                    detail=message
                )
            
            # Outros erros HTTP
            raise
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Erro ao chamar API de IA: {str(e)}")
            print(f"Traceback: {error_trace}")
            
            language_messages = {
                "pt": "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente ou entre em contato conosco através do formulário de contato.",
                "es": "Lo sentimos, ocurrió un error al procesar su mensaje. Por favor, intente nuevamente o contáctenos a través del formulario de contacto.",
                "en": "Sorry, an error occurred while processing your message. Please try again or contact us through the contact form."
            }
            message = language_messages.get(request.language, language_messages["en"])
            
            raise HTTPException(
                status_code=500,
                detail=message
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no chat: {str(e)}"
        )

