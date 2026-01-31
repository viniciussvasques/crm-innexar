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
from app.models.chat_session import ChatSession, ChatMessage
from app.models.contact import Contact
from app.api.ai import call_ai_api, get_active_ai_config
from app.api.helena_prompts import get_helena_prompt
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import uuid
import re
from datetime import datetime
from app.core.ai_tools import AITool

router = APIRouter(tags=["ai-public"])


# === FUNÇÕES AUXILIARES PARA CAPTURA DE LEADS ===

async def extract_lead_from_conversation(session_id: str, db: AsyncSession) -> Optional[Dict[str, str]]:
    """Extrai nome e email das mensagens do usuário na conversa."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id, ChatMessage.role == "user")
        .order_by(ChatMessage.timestamp)
    )
    user_messages = result.scalars().all()
    
    # Juntar todas as mensagens do usuário
    full_text = " ".join([msg.content for msg in user_messages])
    
    # Regex para email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    email_match = re.search(email_pattern, full_text)
    
    if not email_match:
        return None
    
    email = email_match.group()
    
    # Tentar extrair nome (palavras antes do email ou padrões comuns)
    name = None
    
    # Padrão: "meu nome é X" ou "sou X" ou "me chamo X"
    name_patterns = [
        r'(?:meu nome é|me chamo|sou o|sou a|sou)\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)?)',
        r'(?:my name is|i am|i\'m)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
        r'(?:mi nombre es|soy)\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)?)',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip().title()
            break
    
    # Se não encontrou padrão, pegar primeira palavra capitalizada antes do email
    if not name:
        # Procurar por nomes próprios (palavras com primeira letra maiúscula)
        words = full_text.split()
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^A-Za-zÀ-ÿ]', '', word)
            if clean_word and clean_word[0].isupper() and len(clean_word) > 2:
                # Verificar se não é início de frase comum
                if clean_word.lower() not in ['olá', 'ola', 'oi', 'bom', 'boa', 'quero', 'preciso', 'hello', 'hi']:
                    name = clean_word
                    # Tentar pegar sobrenome
                    if i + 1 < len(words):
                        next_word = re.sub(r'[^A-Za-zÀ-ÿ]', '', words[i + 1])
                        if next_word and next_word[0].isupper():
                            name = f"{clean_word} {next_word}"
                    break
    
    # Extrair empresa (padrões: "empresa X", "company X", "da/de X")
    company = None
    company_patterns = [
        r'(?:empresa|company|companhia|negócio|negocio)\s+([A-Za-zÀ-ÿ0-9]+(?:\s+[A-Za-zÀ-ÿ0-9]+)?)',
        r'(?:da|de|do|from|at)\s+([A-Z][A-Za-zÀ-ÿ0-9]+(?:\s+[A-Za-zÀ-ÿ0-9]+)?)',
    ]
    for pattern in company_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Evitar palavras comuns
            if candidate.lower() not in ['minha', 'meu', 'logística', 'logistica', 'seguros', 'app', 'site']:
                company = candidate.title()
                break
    
    # Detectar tipo de projeto
    project_keywords = {
        'app': ['app', 'aplicativo', 'aplicação', 'mobile', 'android', 'ios'],
        'site': ['site', 'website', 'landing', 'página', 'pagina', 'web'],
        'plataforma': ['plataforma', 'platform', 'saas', 'sistema', 'erp'],
        'ecommerce': ['ecommerce', 'e-commerce', 'loja', 'marketplace', 'vendas online'],
    }
    
    project_type = None
    full_text_lower = full_text.lower()
    for ptype, keywords in project_keywords.items():
        if any(kw in full_text_lower for kw in keywords):
            project_type = ptype
            break
    
    # Resumo da conversa (primeiras 500 chars de cada mensagem do usuário)
    conversation_summary = "\n".join([f"- {msg.content[:200]}" for msg in user_messages[:10]])
    
    return {
        "name": name or "Lead do Chat", 
        "email": email,
        "company": company,
        "project_type": project_type,
        "conversation_summary": conversation_summary
    }


async def create_lead_from_chat(lead_data: Dict[str, str], session: ChatSession, db: AsyncSession):
    """Cria contato no CRM a partir dos dados extraídos."""
    try:
        # Verificar se email já existe
        existing = await db.execute(
            select(Contact).where(Contact.email == lead_data["email"]).limit(1)
        )
        existing_contact = existing.scalar_one_or_none()
        
        if existing_contact:
            # Atualizar notas
            existing_contact.notes = (existing_contact.notes or "") + f"\n\n--- Nova conversa Helena ({datetime.utcnow().isoformat()}) ---\nSessão: {session.id}"
            session.lead_captured = True
            session.contact_id = existing_contact.id
            await db.commit()
            return existing_contact
        
        # Buscar admin para atribuir
        admin_result = await db.execute(
            select(User).where(User.role == "admin", User.is_active == True).limit(1)
        )
        admin = admin_result.scalar_one_or_none()
        
        if not admin:
            return None
        
        # Criar novo contato com todos os dados extraídos
        conversation_notes = f"""Lead capturado automaticamente via chat com Helena.
Sessão: {session.id}
Data: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}

=== CONVERSA ===
{lead_data.get('conversation_summary', '')}
"""
        
        new_contact = Contact(
            name=lead_data["name"],
            email=lead_data["email"],
            company=lead_data.get("company"),
            project_type=lead_data.get("project_type"),
            status="lead",
            source="helena_chat",
            notes=conversation_notes,
            owner_id=admin.id
        )
        
        db.add(new_contact)
        await db.flush()
        
        # Marcar sessão como lead capturado
        session.lead_captured = True
        session.contact_id = new_contact.id
        
        await db.commit()
        
        # === ANÁLISE AUTOMÁTICA DE LEAD ===
        # Disparar análise em background após criar o contato
        try:
            from app.api.lead_analysis import analyze_lead_background
            import asyncio
            asyncio.create_task(analyze_lead_background(new_contact.id))
            print(f"[HELENA] Análise automática iniciada para lead {new_contact.id}")
        except Exception as e:
            print(f"[HELENA] Erro ao iniciar análise automática: {e}")
        
        return new_contact
        
    except Exception as e:
        print(f"Erro ao criar lead: {e}")
        return None


class PublicAIRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # ID da sessão para memória
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
- Email: sales@innexar.app
- WhatsApp: +1 407 473-6081
- Formulário de contato: https://innexar.app/pt/contact
- Agendar uma call estratégica: https://innexar.app/pt/contact

REGRAS DE IDIOMA:
1. DETECTE automaticamente o idioma que o usuário está escrevendo
2. RESPONDA SEMPRE no mesmo idioma que o usuário digitou
3. NÃO mude de idioma a menos que o usuário peça explicitamente
4. Se o usuário escrever em português, responda em português
5. Se o usuário escrever em inglês, responda em inglês
6. Se o usuário escrever em espanhol, responda em espanhol

Seja amigável, profissional e prestativa. Forneça informações detalhadas quando solicitado. Se o visitante quiser informações de contato, orçamento ou agendar uma reunião, oriente-o a preencher o formulário de contato no site.

=== FERRAMENTAS DISPONÍVEIS ===
Você pode usar estas ferramentas quando necessário:

1. VERIFICAR PEDIDO/DOMÍNIO:
   - Use: check_order_status(email="email@cliente.com")
   - Use quando o visitante perguntar sobre o status do pedido, site ou domínio.

IMPORTANTE: Para usar, responda APENAS com a chamada da função. Exemplo: check_order_status(email="joao@teste.com")""",
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

CONTACTO:
- Email: sales@innexar.app
- WhatsApp: +1 407 473-6081
- Formulario de contacto: https://innexar.app/es/contact

REGLAS DE IDIOMA:
1. DETECTA automáticamente el idioma en que el usuario escribe
2. RESPONDE SIEMPRE en el mismo idioma que el usuario usó
3. NO cambies de idioma a menos que el usuario lo pida explícitamente

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

CONTACT:
- Email: sales@innexar.app
- WhatsApp: +1 407 473-6081
- Contact form: https://innexar.app/en/contact

LANGUAGE RULES:
1. DETECT automatically the language the user is typing
2. ALWAYS RESPOND in the same language the user used
3. DO NOT switch languages unless the user explicitly asks

Be friendly, professional, and helpful. If the visitor wants contact information or a quote, guide them to fill out the contact form on the website.

IMPORTANT: You CANNOT create contacts, opportunities, or execute actions in the CRM. Only provide information and guide the visitor."""
        }

        # Usar prompt do módulo helena_prompts (com base de conhecimento atualizada)
        base_prompt = get_helena_prompt(request.language)
        
        # === GERENCIAR SESSÃO ===
        session = None
        history_text = ""
        
        if request.session_id:
            # Buscar sessão existente
            result = await db.execute(
                select(ChatSession).where(ChatSession.id == request.session_id)
            )
            session = result.scalar_one_or_none()
        
        if not session:
            # Criar nova sessão
            session = ChatSession(
                id=request.session_id or str(uuid.uuid4()),
                language=request.language or "pt",
                visitor_hash=request.context.get("visitor_hash", "") if request.context else ""
            )
            db.add(session)
            await db.flush()
        else:
            # Atualizar última atividade
            session.last_activity = datetime.utcnow()
        
        # Buscar histórico (últimas 10 mensagens)
        history_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.timestamp.desc())
            .limit(10)
        )
        history_messages = list(reversed(history_result.scalars().all()))
        
        # Formatar histórico para o prompt
        if history_messages:
            history_lines = []
            for msg in history_messages:
                role_label = "Visitante" if msg.role == "user" else "Helena"
                history_lines.append(f"{role_label}: {msg.content}")
            history_text = "\n".join(history_lines)
            base_prompt += f"\n\n=== HISTÓRICO DA CONVERSA ===\n{history_text}\n\n=== REGRAS DE CONTEXTO ===\n1. USE o histórico para manter contexto\n2. NÃO repita informações já dadas\n3. Desenvolva a conversa baseado no que foi falado"
        
        if request.context:
            context_str = json.dumps(request.context, ensure_ascii=False)
            base_prompt += f"\n\nContexto adicional: {context_str}"

        # === INJETAR INSTRUÇÕES DE FERRAMENTAS (CRÍTICO - PRIORIDADE MÁXIMA) ===
        tools_instruction = """
=== PRIORIDADE MÁXIMA: USO DE FERRAMENTAS ===
ANTES de responder como "Helena", verifique se o usuário está pedindo para checar um pedido ou status.
SE SIM, ignore as regras de conversa e responda APENAS com a ferramenta abaixo:

ferramenta: check_order_status(email="...")

EXEMPLOS OBRIGATÓRIOS:
User: "ver meu pedido teste@email.com" -> Helena: check_order_status(email="teste@email.com")
User: "status do pedido" -> Helena: Qual é o email do pedido para eu verificar?
User: "meu email é x@y.com" (se contexto for verificar pedido) -> Helena: check_order_status(email="x@y.com")
"""
        full_prompt = f"{base_prompt}\n{tools_instruction}\n\nVisitante: {request.message}\n\nHelena:"

        


        try:
            with open("/tmp/debug_helena.txt", "a") as f:
                f.write(f"\n\n=== REQUEST {datetime.utcnow()} ===\n")
                f.write(f"SESSION: {session.id}\n")
                f.write(f"HISTORY COUNT: {len(history_messages)}\n")
                f.write(f"PROMPT:\n{full_prompt}\n")
                f.write("==============================\n")
        except Exception as e:

            print(f"Error writing debug file: {e}")

        try:
            # === FERRAMENTAS NATIVAS (NOVA ARQUITETURA) ===
            check_order_tool = AITool(
                name="check_order_status",
                description="Verifica o status atual de um pedido de site ou aplicativo usando o email do cliente.",
                parameters={
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "O email do cliente para verificar o pedido. Ex: cliente@email.com"
                        }
                    },
                    "required": ["email"]
                }
            )
            
            # Remover instruções manuais antigas do prompt (se houver) para evitar conflito
            # A API nativa injeta suas próprias descrições
            
            # Chamar API com tools
            response = await call_ai_api(full_prompt, max_tokens=1000, db=db, tools=[check_order_tool])
            
            # === LIMPEZA DE ALUCINAÇÕES E RACIOCÍNIO ===
            # 1. Remove tags <think>...</think>
            response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
            
            # 2. Remove raciocínio de modelos como GPT-OSS e DeepSeek R1
            # Esses modelos frequentemente outputam: "reasoning... assistantfinal RESPOSTA"
            reasoning_markers = ['assistantfinal', 'assistant_final', 'FINAL:', 'Final answer:', 'Final:']
            for marker in reasoning_markers:
                if marker.lower() in response.lower():
                    idx = response.lower().find(marker.lower())
                    response = response[idx + len(marker):].strip()
                    break
            
            # 3. Remove frases típicas de raciocínio no início
            reasoning_patterns = [
                r'^.*?(?:We need to respond|Let\'s craft|We should|I need to|Ok\.|Okay\.).*?\n+',
                r'^.*?(?:The user says|The user asks|They are asking).*?\n+',
                r'^.*?(?:Keep it short|End with question|No mention of).*?\n+',
            ]
            for pattern in reasoning_patterns:
                response = re.sub(pattern, '', response, flags=re.IGNORECASE | re.DOTALL)
            
            # 4. Helena: prefix cleanup
            if "Helena:" in response:
                parts = response.split("Helena:", 1)
                if len(parts) > 1 and len(parts[1].strip()) > 0:
                    response = parts[1].strip()
            
            # 5. Stop markers
            stop_markers = ["Visitante:", "User:", "Usuario:", "Cliente:"]
            for marker in stop_markers:
                if marker in response:
                    response = response.split(marker)[0].strip()
            
            response = response.strip()

            # === DETECTAR E EXECUTAR AÇÕES (NATIVO E LEGADO) ===
            action_executed = False
            action_result = None
            final_response = response
            
            # Verificar se a resposta é uma chamada de função (Formato unificado do ai.py: "func(args)")
            # Regex robusto para pegar func(args) vindo do backend
            tool_match = re.match(r'^\s*check_order_status\s*\((.*)\)\s*$', response, re.DOTALL)
            
            if tool_match:
                # É uma chamada de ferramenta PURA!
                action_string = response
                try:
                    action_result = await _execute_public_action(action_string, db)
                    action_executed = True
                    final_response = action_result
                except Exception as e:
                    print(f"Erro ao executar ação pública nativa: {str(e)}")
                    final_response = "Desculpe, tive um erro técnico ao verificar essa informação."
            
            else:
                # Fallback: Tenta achar no meio do texto (caso o modelo ignore o tool_choice e fale junto)
                # Padrões de ação pública (Legado/Fallback)
                action_patterns = [
                    r'check_order_status\s*\([^)]*\)'
                ]
                
                for pattern in action_patterns:
                    match = re.search(pattern, response, re.IGNORECASE)
                    if match:
                        action_call = match.group(0)
                        try:
                            action_result = await _execute_public_action(action_call, db)
                            action_executed = True
                            final_response = action_result
                        except Exception as e:
                            print(f"Erro ao executar ação pública (fallback): {str(e)}")
                            final_response = "Desculpe, tive um erro técnico ao verificar essa informação."
                        break


            # Salvar mensagem do usuário
            user_message = ChatMessage(
                session_id=session.id,
                role="user",
                content=request.message
            )
            db.add(user_message)
            
            # Salvar resposta da Helena
            assistant_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=final_response
            )
            db.add(assistant_message)
            
            await db.commit()
            
            # === CAPTURA AUTOMÁTICA DE LEADS ===
            # Verificar se já capturou lead nesta sessão
            if not session.lead_captured:
                lead_data = await extract_lead_from_conversation(session.id, db)
                if lead_data and lead_data.get("email"):
                    await create_lead_from_chat(lead_data, session, db)
            
            return {
                "response": final_response,
                "session_id": session.id,
                "timestamp": datetime.utcnow().isoformat(),
                "language": request.language
            }

        except HTTPException as e:
            # ... (rest of exception handling) ...
            pass
            raise e

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro no chat: {str(e)}"
        )

async def _execute_public_action(action_string: str, db: AsyncSession) -> str:
    """Executa ações públicas seguras"""
    try:
        match = re.match(r"(\w+)\s*\((.*)\)", action_string)
        if not match:
            return "Comando inválido."
            
        func_name = match.group(1)
        args_str = match.group(2)
        
        args = {}
        if args_str:
            # Parse simples de argumentos (key="value")
            arg_pairs = re.findall(r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')', args_str)
            for key, val1, val2 in arg_pairs:
                args[key] = val1 or val2
                
        if func_name == "check_order_status":
            email = args.get("email")
            if not email:
                return "Preciso do email para verificar o pedido."
            
            # Buscar pedido
            from app.models.site_order import SiteOrder
            result = await db.execute(
                select(SiteOrder)
                .where(SiteOrder.customer_email.ilike(email))
                .order_by(desc(SiteOrder.created_at))
                .limit(1)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                return f"Não encontrei nenhum pedido recente para o email {email}. Verifique se digitou corretamente."
            
            # Formatar resposta amigável
            status_map = {
                "pending_payment": "Aguardando Pagamento",
                "paid": "Pago - Aguardando Início",
                "onboarding": "Em Onboarding",
                "building": "Em Construção (IA Trabalhando)",
                "generating": "Gerando Arquivos",
                "review": "Em Revisão",
                "completed": "Concluído",
                "cancelled": "Cancelado"
            }
            status_text = status_map.get(str(order.status).split('.')[-1].lower(), str(order.status))
            
            return f"Encontrei seu pedido! 🎉\n\n🆔 Pedido: #{order.id}\n📅 Data: {order.created_at.strftime('%d/%m/%Y')}\n📊 Status: *{status_text}*\n\nSe precisar de mais detalhes, pode me perguntar!"
            
        return "Função não reconhecida."
        
    except Exception as e:
        print(f"Erro na execução da ação pública: {e}")
        return "Desculpe, não consegui verificar as informações no momento."


# ============ CAPTURA DE LEADS ============

class LeadCaptureRequest(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    interest: Optional[str] = None
    conversation_summary: Optional[str] = None
    language: Optional[str] = "pt"

@router.post("/lead")
async def capture_lead_from_chat(
    request: LeadCaptureRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Captura lead a partir de conversa com Helena.
    Cria contato no CRM automaticamente.
    """
    from app.models.contact import Contact
    
    try:
        # Buscar admin para atribuir o contato
        result = await db.execute(
            select(User).where(User.role == "admin", User.is_active == True).limit(1)
        )
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            raise HTTPException(status_code=500, detail="Sistema não configurado")
        
        # Verificar se já existe contato com esse email
        existing = await db.execute(
            select(Contact).where(Contact.email == request.email).limit(1)
        )
        existing_contact = existing.scalar_one_or_none()
        
        if existing_contact:
            # Atualizar notas do contato existente
            existing_contact.notes = (existing_contact.notes or "") + f"\n\n--- Chat com Helena ({datetime.utcnow().isoformat()}) ---\n{request.conversation_summary or request.interest or ''}"
            await db.commit()
            
            return {
                "success": True,
                "message": "Contato atualizado com nova conversa",
                "contact_id": existing_contact.id,
                "is_new": False
            }
        
        # Criar novo contato
        new_contact = Contact(
            name=request.name,
            email=request.email,
            phone=request.phone,
            status="lead",
            source="helena_chat",
            notes=f"Interesse: {request.interest or 'Não especificado'}\n\nConversa:\n{request.conversation_summary or ''}",
            owner_id=admin_user.id
        )
        
        db.add(new_contact)
        await db.commit()
        await db.refresh(new_contact)
        
        # === ANÁLISE AUTOMÁTICA DE LEAD ===
        try:
            from app.api.lead_analysis import analyze_lead_background
            import asyncio
            asyncio.create_task(analyze_lead_background(new_contact.id))
            print(f"[HELENA] Análise automática iniciada para lead {new_contact.id}")
        except Exception as e:
            print(f"[HELENA] Erro ao iniciar análise automática: {e}")
        
        return {
            "success": True,
            "message": "Lead capturado com sucesso!",
            "contact_id": new_contact.id,
            "is_new": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao capturar lead: {str(e)}"
        )
