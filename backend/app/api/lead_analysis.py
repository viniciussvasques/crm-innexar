"""
API para análise automática de leads pela IA
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.models.contact import Contact
from app.models.lead_analysis import LeadAnalysis
from app.models.ai_config import AIConfig, AIModelStatus
from app.api.dependencies import get_current_user, get_user_role_str
from app.api.ai import call_ai_api, get_active_ai_config
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
import json
import re

router = APIRouter(prefix="/lead-analysis", tags=["lead-analysis"])

class LeadAnalysisResponse(BaseModel):
    id: int
    contact_id: int
    company_info: Optional[str] = None
    market_analysis: Optional[str] = None
    financial_insights: Optional[str] = None
    recommendations: Optional[str] = None
    risk_assessment: Optional[str] = None
    opportunity_score: Optional[int] = None
    analysis_metadata: Optional[Dict[str, Any]] = None
    analysis_status: str
    created_at: datetime
    analyzed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

async def analyze_lead_background(contact_id: int):
    """Função de background para analisar lead"""
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db_session:
        try:
            # Buscar contato
            result = await db_session.execute(select(Contact).where(Contact.id == contact_id))
            contact = result.scalar_one_or_none()
            
            if not contact:
                return
            
            # Verificar se já existe análise
            result = await db_session.execute(select(LeadAnalysis).where(LeadAnalysis.contact_id == contact_id))
            existing_analysis = result.scalar_one_or_none()
            
            if existing_analysis and existing_analysis.analysis_status == "completed":
                return  # Já analisado
            
            # Criar ou atualizar análise
            if not existing_analysis:
                analysis = LeadAnalysis(
                    contact_id=contact_id,
                    analysis_status="pending"
                )
                db_session.add(analysis)
            else:
                analysis = existing_analysis
                analysis.analysis_status = "pending"
            
            await db_session.commit()
            await db_session.refresh(analysis)
            
            # Buscar configuração de IA ativa
            ai_config = await get_active_ai_config(db_session)
            if not ai_config:
                analysis.analysis_status = "error"
                analysis.error_message = "Nenhuma configuração de IA ativa encontrada"
                await db_session.commit()
                return
            
            # Preparar dados do lead para análise
            lead_data = {
                "name": contact.name,
                "email": contact.email,
                "phone": contact.phone,
                "company": contact.company,
                "status": contact.status,
                "notes": contact.notes,
                "created_at": contact.created_at.isoformat() if contact.created_at else None
            }
            
            # Criar prompt para análise
            analysis_prompt = f"""Você é um especialista em análise de leads e prospecção comercial. Sua tarefa é criar um relatório COMPLETO e ESTRUTURADO sobre este lead.

DADOS DO LEAD:
- Nome: {contact.name}
- Email: {contact.email or 'Não informado'}
- Telefone: {contact.phone or 'Não informado'}
- Empresa: {contact.company or 'Não informado'}
- Status: {contact.status}
- Notas: {contact.notes or 'Nenhuma nota'}
- Data de criação: {contact.created_at.strftime('%d/%m/%Y') if contact.created_at else 'N/A'}

INSTRUÇÕES IMPORTANTES:
1. Pesquise TUDO sobre a empresa "{contact.company}" (se informada):
   - Site oficial
   - Redes sociais (LinkedIn, Facebook, Instagram, Twitter)
   - Faturamento anual estimado
   - Número de funcionários
   - Localização/sede
   - Setor de atuação
   - Principais produtos/serviços
   - Clientes conhecidos
   - Notícias recentes

2. Analise o perfil do lead:
   - Cargo/função (se possível identificar)
   - Nível de decisão
   - Urgência da necessidade
   - Budget estimado

3. Avalie o potencial:
   - Score de oportunidade (0-100)
   - Probabilidade de fechamento
   - Valor potencial estimado
   - Prazo estimado para fechamento

4. Forneça recomendações práticas e acionáveis

RESPONDA APENAS EM TEXTO ESTRUTURADO (NÃO JSON), no seguinte formato:

=== INFORMAÇÕES DA EMPRESA ===
[Nome da empresa, setor, tamanho, localização, faturamento anual estimado, número de funcionários]

=== PRESENÇA DIGITAL ===
[Site: URL se encontrado]
[LinkedIn: URL se encontrado]
[Outras redes sociais relevantes]

=== ANÁLISE DE MERCADO ===
[Posicionamento no mercado, concorrentes, diferenciais, tendências do setor]

=== INSIGHTS FINANCEIROS ===
[Faturamento anual estimado, capacidade de investimento, histórico de investimentos em tecnologia/serviços similares]

=== PERFIL DO LEAD ===
[Cargo/função, nível de decisão, urgência, necessidade identificada]

=== POTENCIAL DE NEGÓCIO ===
[Score de oportunidade: X/100]
[Valor potencial estimado: R$ X]
[Prazo estimado para fechamento: X meses]
[Probabilidade de fechamento: X%]

=== RECOMENDAÇÕES ESTRATÉGICAS ===
[Abordagem recomendada, pontos-chave para abordagem, timing ideal, próximos passos sugeridos]

=== AVALIAÇÃO DE RISCOS ===
[Riscos identificados, pontos de atenção, fatores que podem impedir o fechamento]

=== FONTES DE PESQUISA ===
[Lista de fontes utilizadas: sites, redes sociais, notícias, etc.]

Seja EXTREMAMENTE detalhado e use informações REAIS quando possível. Se não encontrar informações específicas, indique claramente."""

            try:
                # Chamar IA para análise
                ai_response = await call_ai_api(analysis_prompt, max_tokens=4000, db=db_session, config=ai_config)
                
                # Processar resposta estruturada (não JSON)
                full_analysis = ai_response.strip()
                
                # Remover markdown code blocks se houver
                if full_analysis.startswith("```"):
                    # Encontrar o fim do bloco de código
                    lines = full_analysis.split('\n')
                    start_idx = 0
                    end_idx = len(lines)
                    for i, line in enumerate(lines):
                        if line.strip().startswith("```") and i > 0:
                            if start_idx == 0:
                                start_idx = i + 1
                            else:
                                end_idx = i
                                break
                    full_analysis = '\n'.join(lines[start_idx:end_idx]).strip()
                
                # Extrair seções da análise estruturada
                sections = {
                    "company_info": "",
                    "digital_presence": "",
                    "market_analysis": "",
                    "financial_insights": "",
                    "lead_profile": "",
                    "business_potential": "",
                    "recommendations": "",
                    "risk_assessment": "",
                    "sources": ""
                }
                
                # Extrair score de oportunidade (ex: "Score de oportunidade: 75/100" ou "Score: 75")
                opportunity_score = None
                score_patterns = [
                    r'Score de oportunidade[:\s]+(\d+)',
                    r'Score[:\s]+(\d+)',
                    r'opportunity_score[:\s]+(\d+)',
                    r'pontuação[:\s]+(\d+)'
                ]
                for pattern in score_patterns:
                    score_match = re.search(pattern, full_analysis, re.IGNORECASE)
                    if score_match:
                        opportunity_score = int(score_match.group(1))
                        break
                
                # Extrair valor potencial (ex: "Valor potencial estimado: R$ 50000")
                potential_value = None
                value_patterns = [
                    r'Valor potencial estimado[:\s]+R\$\s*([\d.,]+)',
                    r'Valor estimado[:\s]+R\$\s*([\d.,]+)',
                    r'potential_value[:\s]+R\$\s*([\d.,]+)',
                    r'R\$\s*([\d.,]+)'
                ]
                for pattern in value_patterns:
                    value_match = re.search(pattern, full_analysis, re.IGNORECASE)
                    if value_match:
                        value_str = value_match.group(1).replace('.', '').replace(',', '.')
                        try:
                            potential_value = float(value_str)
                            break
                        except:
                            pass
                
                # Dividir análise em seções usando padrões de título
                section_patterns = {
                    "company_info": [
                        r"=== INFORMAÇÕES DA EMPRESA ===\s*\n(.*?)(?=\n===|\n==|\Z)",
                        r"INFORMAÇÕES DA EMPRESA[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)",
                        r"Empresa[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)"
                    ],
                    "digital_presence": [
                        r"=== PRESENÇA DIGITAL ===\s*\n(.*?)(?=\n===|\n==|\Z)",
                        r"PRESENÇA DIGITAL[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)",
                        r"Digital[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)"
                    ],
                    "market_analysis": [
                        r"=== ANÁLISE DE MERCADO ===\s*\n(.*?)(?=\n===|\n==|\Z)",
                        r"ANÁLISE DE MERCADO[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)",
                        r"Mercado[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)"
                    ],
                    "financial_insights": [
                        r"=== INSIGHTS FINANCEIROS ===\s*\n(.*?)(?=\n===|\n==|\Z)",
                        r"INSIGHTS FINANCEIROS[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)",
                        r"Financeiro[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)"
                    ],
                    "lead_profile": [
                        r"=== PERFIL DO LEAD ===\s*\n(.*?)(?=\n===|\n==|\Z)",
                        r"PERFIL DO LEAD[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)",
                        r"Perfil[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)"
                    ],
                    "business_potential": [
                        r"=== POTENCIAL DE NEGÓCIO ===\s*\n(.*?)(?=\n===|\n==|\Z)",
                        r"POTENCIAL DE NEGÓCIO[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)",
                        r"Potencial[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)"
                    ],
                    "recommendations": [
                        r"=== RECOMENDAÇÕES ESTRATÉGICAS ===\s*\n(.*?)(?=\n===|\n==|\Z)",
                        r"RECOMENDAÇÕES[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)",
                        r"Recomendações[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)"
                    ],
                    "risk_assessment": [
                        r"=== AVALIAÇÃO DE RISCOS ===\s*\n(.*?)(?=\n===|\n==|\Z)",
                        r"AVALIAÇÃO DE RISCOS[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)",
                        r"Riscos[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)"
                    ],
                    "sources": [
                        r"=== FONTES DE PESQUISA ===\s*\n(.*?)(?=\n===|\n==|\Z)",
                        r"FONTES[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)",
                        r"Fontes[:\n]+(.*?)(?=\n[A-ZÁÊÔÇ]{3,}|==|\Z)"
                    ]
                }
                
                for section_name, patterns in section_patterns.items():
                    for pattern in patterns:
                        match = re.search(pattern, full_analysis, re.DOTALL | re.IGNORECASE | re.MULTILINE)
                        if match:
                            sections[section_name] = match.group(1).strip()
                            break
                
                # Se não encontrou seções estruturadas, usar a resposta completa como company_info
                if not any(sections.values()):
                    sections["company_info"] = full_analysis
                
                # Atualizar análise
                analysis.company_info = sections["company_info"] or (sections["digital_presence"] if sections["digital_presence"] else full_analysis[:500])
                analysis.market_analysis = sections["market_analysis"]
                analysis.financial_insights = sections["financial_insights"]
                analysis.recommendations = sections["recommendations"]
                analysis.risk_assessment = sections["risk_assessment"]
                analysis.opportunity_score = opportunity_score
                analysis.analysis_metadata = {
                    "digital_presence": sections["digital_presence"],
                    "lead_profile": sections["lead_profile"],
                    "business_potential": sections["business_potential"],
                    "sources": sections["sources"],
                    "potential_value": potential_value,
                    "full_analysis": full_analysis,
                    "ai_model": ai_config.model_name,
                    "provider": ai_config.provider
                }
                analysis.ai_model_used = f"{ai_config.provider}/{ai_config.model_name}"
                analysis.analysis_status = "completed"
                analysis.analyzed_at = datetime.utcnow()
                
                await db_session.commit()
                
            except Exception as e:
                analysis.analysis_status = "error"
                analysis.error_message = str(e)
                await db_session.commit()
                print(f"Erro ao analisar lead {contact_id}: {str(e)}")
        
        except Exception as e:
            print(f"Erro na análise de lead: {str(e)}")

@router.post("/analyze/{contact_id}")
async def trigger_lead_analysis(
    contact_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dispara análise de lead (apenas admin ou dono do contato)"""
    # Verificar permissões
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    
    role_str = get_user_role_str(current_user)
    if role_str != "admin" and contact.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você não tem permissão para analisar este lead")
    
    # Adicionar tarefa de background
    background_tasks.add_task(analyze_lead_background, contact_id)
    
    return {"message": "Análise iniciada em background", "contact_id": contact_id}

@router.get("/{contact_id}", response_model=LeadAnalysisResponse)
async def get_lead_analysis(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna análise de lead (apenas admin ou dono do contato)"""
    # Verificar permissões
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    
    role_str = get_user_role_str(current_user)
    if role_str != "admin" and contact.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você não tem permissão para ver esta análise")
    
    # Buscar análise
    result = await db.execute(select(LeadAnalysis).where(LeadAnalysis.contact_id == contact_id))
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Análise não encontrada. Use POST para iniciar análise.")
    
    return LeadAnalysisResponse(
        id=analysis.id,
        contact_id=analysis.contact_id,
        company_info=analysis.company_info,
        market_analysis=analysis.market_analysis,
        financial_insights=analysis.financial_insights,
        recommendations=analysis.recommendations,
        risk_assessment=analysis.risk_assessment,
        opportunity_score=analysis.opportunity_score,
        analysis_metadata=analysis.analysis_metadata,
        analysis_status=analysis.analysis_status,
        created_at=analysis.created_at,
        analyzed_at=analysis.analyzed_at
    )

@router.get("/", response_model=list[LeadAnalysisResponse])
async def list_lead_analyses(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista análises de leads (admin vê todas, vendedor vê apenas suas)"""
    role_str = get_user_role_str(current_user)
    
    query = select(LeadAnalysis)
    
    if role_str == "vendedor":
        # Vendedor vê apenas análises de seus contatos
        query = query.join(Contact).where(Contact.owner_id == current_user.id)
    
    query = query.offset(skip).limit(limit).order_by(LeadAnalysis.created_at.desc())
    
    result = await db.execute(query)
    analyses = result.scalars().all()
    
    return [
        LeadAnalysisResponse(
            id=a.id,
            contact_id=a.contact_id,
            company_info=a.company_info,
            market_analysis=a.market_analysis,
            financial_insights=a.financial_insights,
            recommendations=a.recommendations,
            risk_assessment=a.risk_assessment,
            opportunity_score=a.opportunity_score,
            analysis_metadata=a.analysis_metadata,
            analysis_status=a.analysis_status,
            created_at=a.created_at,
            analyzed_at=a.analyzed_at
        )
        for a in analyses
    ]

