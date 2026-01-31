"""
Test endpoints for Stripe and Dynadot integrations
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import Request as FastAPIRequest
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import require_admin
from app.services.dynadot_service import DynadotService
from app.services.stripe_service import StripeService
from app.api.notifications import notify_all_admins

router = APIRouter(prefix="/test-integrations", tags=["test-integrations"])


class TestDomainRequest(BaseModel):
    domain: str


class TestStripeWebhookRequest(BaseModel):
    test_order_id: Optional[int] = None


@router.post("/dynadot/check-domain")
async def test_dynadot_check_domain(
    request: TestDomainRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Test Dynadot domain availability check.
    Admin only.
    """
    try:
        dynadot_service = DynadotService(db)
        result = await dynadot_service.check_domain_availability(request.domain)
        
        # Create notification about the test
        try:
            await notify_all_admins(
                db,
                title="Teste Dynadot - Verificação de Domínio",
                message=f"Domínio testado: {request.domain}\nDisponível: {result.get('available', False)}\nPreço: ${result.get('price', 0):.2f}",
                notification_type="info" if result.get("available") else "warning",
                related_entity_type="test",
                related_entity_id=None
            )
        except Exception as e:
            print(f"Failed to create notification: {e}")
        
        return {
            "success": True,
            "result": result,
            "message": f"Domínio {request.domain} {'disponível' if result.get('available') else 'indisponível'}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar domínio: {str(e)}")


@router.post("/dynadot/check-multiple")
async def test_dynadot_check_multiple(
    domains: list[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Test Dynadot multiple domain availability check.
    Admin only.
    Expects JSON body: ["domain1.com", "domain2.com", ...]
    """
    try:
        body = await request.json()
        # Handle both array and object with 'domains' key
        if isinstance(body, list):
            domains_list = body
        elif isinstance(body, dict) and 'domains' in body:
            domains_list = body['domains']
        else:
            raise HTTPException(status_code=400, detail="Expected array of domains or object with 'domains' key")
        
        dynadot_service = DynadotService(db)
        results = await dynadot_service.check_multiple_domains(domains_list)
        
        available_count = sum(1 for r in results.values() if r.get("available"))
        
        # Create notification about the test
        try:
            await notify_all_admins(
                db,
                title="Teste Dynadot - Múltiplos Domínios",
                message=f"Domínios testados: {len(domains_list)}\nDisponíveis: {available_count}",
                notification_type="info",
                related_entity_type="test",
                related_entity_id=None
            )
        except Exception as e:
            print(f"Failed to create notification: {e}")
        
        return {
            "success": True,
            "results": results,
            "summary": {
                "total": len(domains),
                "available": available_count,
                "unavailable": len(domains_list) - available_count
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar domínios: {str(e)}")


@router.get("/dynadot/config")
async def test_dynadot_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Check Dynadot configuration status.
    Admin only.
    """
    try:
        dynadot_service = DynadotService(db)
        await dynadot_service._load_config()
        
        # Get raw values from database to check for whitespace issues
        from app.models.system_config import SystemConfig
        from sqlalchemy import select
        
        result = await db.execute(
            select(SystemConfig).where(
                SystemConfig.key.in_(["dynadot_api_key", "dynadot_api_secret"])
            )
        )
        configs = {row.key: row for row in result.scalars().all()}
        
        api_key_raw = configs.get("dynadot_api_key").value if configs.get("dynadot_api_key") else None
        api_secret_raw = configs.get("dynadot_api_secret").value if configs.get("dynadot_api_secret") else None
        
        return {
            "api_key_configured": bool(dynadot_service.api_key),
            "api_secret_configured": bool(dynadot_service.api_secret),
            "max_domain_price": dynadot_service.max_domain_price,
            "ready": dynadot_service.api_key is not None,
            "api_key_length": len(dynadot_service.api_key) if dynadot_service.api_key else 0,
            "api_key_preview": f"{dynadot_service.api_key[:8]}...{dynadot_service.api_key[-4:]}" if dynadot_service.api_key and len(dynadot_service.api_key) > 12 else (dynadot_service.api_key[:12] if dynadot_service.api_key else None),
            "api_key_has_whitespace": (api_key_raw and api_key_raw != api_key_raw.strip()) if api_key_raw else False,
            "raw_api_key_length": len(api_key_raw) if api_key_raw else 0,
            "cleaned_api_key_length": len(dynadot_service.api_key) if dynadot_service.api_key else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar configuração: {str(e)}")


@router.get("/stripe/config")
async def test_stripe_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Check Stripe configuration status.
    Admin only.
    """
    try:
        stripe_service = StripeService(db)
        await stripe_service._load_config()
        
        return {
            "api_key_configured": stripe_service.api_key is not None,
            "webhook_secret_configured": stripe_service.webhook_secret is not None,
            "ready": stripe_service.api_key is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar configuração: {str(e)}")


@router.post("/stripe/test-webhook")
async def test_stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Test Stripe webhook endpoint (simulates webhook call).
    Admin only.
    Note: This creates a test notification to verify the notification system works.
    """
    try:
        # Create a test notification to verify notifications are working
        await notify_all_admins(
            db,
            title="Teste Stripe Webhook",
            message="Webhook de teste do Stripe executado com sucesso",
            notification_type="success",
            related_entity_type="test",
            related_entity_id=None
        )
        
        return {
            "success": True,
            "message": "Notificação de teste criada. Verifique se aparece no sistema de notificações.",
            "note": "Este endpoint apenas testa o sistema de notificações. Para testar webhooks reais, use o Stripe CLI ou Dashboard."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao testar webhook: {str(e)}")


@router.post("/notifications/test")
async def test_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Test notification system by creating a test notification.
    Admin only.
    """
    try:
        await notify_all_admins(
            db,
            title="Teste de Notificações",
            message="Esta é uma notificação de teste. Se você está vendo isso, o sistema de notificações está funcionando!",
            notification_type="info",
            related_entity_type="test",
            related_entity_id=None
        )
        
        return {
            "success": True,
            "message": "Notificação de teste criada. Verifique se aparece no sistema de notificações."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar notificação de teste: {str(e)}")
