from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
from datetime import datetime

router = APIRouter(prefix="/templates", tags=["templates"])

# Função auxiliar para listar templates
def get_template_types_data():
    """Retorna tipos de templates disponíveis"""
    return {
        "types": [
            {
                "id": "proposal",
                "name": "Proposta Comercial",
                "description": "Template completo de proposta comercial",
                "variables": ["company_name", "contact_name", "project_description", "total_value", "delivery_time"]
            },
            {
                "id": "email_followup",
                "name": "Email de Follow-up",
                "description": "Template para email de acompanhamento",
                "variables": ["contact_name", "project_name", "decision_questions", "seller_name"]
            },
            {
                "id": "contract_summary",
                "name": "Resumo de Contrato",
                "description": "Template simplificado de contrato",
                "variables": ["client_name", "contract_value", "start_date", "end_date"]
            }
        ]
    }

class TemplateRequest(BaseModel):
    template_type: str  # proposal, contract, email, quote
    data: Dict[str, Any]
    language: str = "pt"  # pt, en, es

class TemplateResponse(BaseModel):
    template_type: str
    content: str
    language: str
    generated_at: datetime
    variables_used: Dict[str, Any]

# Templates base em português
TEMPLATES = {
    "proposal": """
# Proposta Comercial - {company_name}

## Introdução

Prezado(a) {contact_name},

Somos a Innexar, especializada em desenvolvimento de software sob medida. Temos o prazer de apresentar esta proposta para {project_description}.

## Escopo do Projeto

### Objetivos
{project_objectives}

### Funcionalidades Principais
{project_features}

### Tecnologias
{project_technologies}

## Benefícios

### Para seu negócio
{business_benefits}

### ROI Esperado
{expected_roi}

## Cronograma

### Fase 1: {phase1_name}
- Duração: {phase1_duration}
- Entregáveis: {phase1_deliverables}

### Fase 2: {phase2_name}
- Duração: {phase2_duration}
- Entregáveis: {phase2_deliverables}

### Fase 3: {phase3_name}
- Duração: {phase3_duration}
- Entregáveis: {phase3_deliverables}

## Investimento

### Valor Total: R$ {total_value}
### Forma de Pagamento: {payment_terms}
### Prazo de Entrega: {delivery_time}

## Próximos Passos

1. Aprovação desta proposta
2. Assinatura do contrato
3. Kickoff do projeto
4. Desenvolvimento e entregas

Atenciosamente,
{seller_name}
Innexar - Desenvolvimento de Software
""",
    "email_followup": """
Assunto: Acompanhamento - Proposta {project_name}

Olá {contact_name},

Espero que esta mensagem o(a) encontre bem.

Gostaria de saber se você teve a oportunidade de analisar a proposta que enviamos para o projeto {project_name}.

Algumas questões que podem ajudar na sua decisão:

{decision_questions}

Estamos à disposição para esclarecer qualquer dúvida e discutir os próximos passos.

Atenciosamente,
{seller_name}
Innexar
{contact_info}
""",
    "contract_summary": """
# Contrato de Prestação de Serviços

## Partes Envolvidas

**Contratante:** {client_name}
**Contratado:** Innexar Tecnologia Ltda

## Objeto do Contrato

O presente contrato tem por objeto a prestação de serviços de desenvolvimento de software conforme especificado na proposta comercial anexa.

## Valor e Forma de Pagamento

- Valor Total: R$ {contract_value}
- Forma de Pagamento: {payment_method}
- Cronograma: {payment_schedule}

## Prazo de Execução

- Início: {start_date}
- Término: {end_date}
- Prazo Total: {total_duration}

## Responsabilidades

### Innexar
{innexar_responsibilities}

### Cliente
{client_responsibilities}

## Propriedade Intelectual

{intellectual_property_terms}

## Confidencialidade

{confidentiality_terms}

## Rescisão

{termination_terms}

## Foro

{legal_jurisdiction}

São Paulo, {contract_date}

___________________________                ___________________________
{seller_name}                                    {client_representative}
Innexar Tecnologia Ltda                        {client_name}
"""
}

@router.post("/generate", response_model=TemplateResponse)
async def generate_template(
    request: TemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Gera documento baseado em template"""
    try:
        if request.template_type not in TEMPLATES:
            raise HTTPException(status_code=400, detail=f"Template {request.template_type} não encontrado")

        template = TEMPLATES[request.template_type]

        # Substitui variáveis no template
        content = template
        variables_used = {}

        for key, value in request.data.items():
            placeholder = f"{{{key}}}"
            if placeholder in content:
                content = content.replace(placeholder, str(value))
                variables_used[key] = value

        # Remove placeholders não preenchidos
        import re
        content = re.sub(r'\{[^}]+\}', '[PENDENTE]', content)

        return TemplateResponse(
            template_type=request.template_type,
            content=content,
            language=request.language,
            generated_at=datetime.utcnow(),
            variables_used=variables_used
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar template: {str(e)}")

@router.get("/")
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista tipos de templates disponíveis"""
    return get_template_types_data()

@router.get("/types")
async def get_template_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna tipos de templates disponíveis (alias para /)"""
    return get_template_types_data()
