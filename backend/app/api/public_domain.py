"""
Public Domain Check API - No auth required for domain availability checking and purchase
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.services.dynadot_service import DynadotService

router = APIRouter(prefix="/public-domain", tags=["public-domain"])


class DomainCheckRequest(BaseModel):
    domain: str


class DomainPurchaseRequest(BaseModel):
    domain: str
    duration_years: int = 1
    order_id: str  # Order identifier to link purchase


@router.post("/check")
async def check_domain_availability(
    request: DomainCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Check domain availability (public endpoint, no auth required).
    Used by onboarding form to verify domain in real-time.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if not request.domain or not request.domain.strip():
            raise HTTPException(status_code=400, detail="Domain is required")
        
        domain = request.domain.strip()
        logger.info(f"[Domain Check] Starting check for domain: {domain}")
        
        try:
            dynadot_service = DynadotService(db)
            logger.info(f"[Domain Check] Loading Dynadot configuration...")
            await dynadot_service._load_config()
            
            if not dynadot_service.api_key:
                logger.warning("[Domain Check] Dynadot API key not configured")
                return {
                    "success": False,
                    "error": "Dynadot API not configured. Please contact support.",
                    "result": {
                        "available": False,
                        "error": "Dynadot API not configured",
                        "domain": domain
                    }
                }
            
            logger.info(f"[Domain Check] API key loaded, calling check_domain_availability...")
            result = await dynadot_service.check_domain_availability(domain)
            
            # If domain is not available or has an error, generate suggestions
            suggestions = []
            if not result.get("available") or result.get("error"):
                logger.info(f"[Domain Check] Domain not available or invalid, generating suggestions...")
                
                # Extract SLD (name without extension)
                parts = domain.split(".")
                if len(parts) > 1:
                    sld = parts[0]
                else:
                    sld = domain
                
                # Common TLDs to check
                common_tlds = [
                    "com", "net", "org", "co", "info", "biz", 
                    "me", "online", "site", "store", "tech", "io"
                ]
                
                # Generate candidates (excluding the one we just checked if it was valid)
                candidates = []
                for tld in common_tlds:
                    candidate = f"{sld}.{tld}"
                    if candidate != domain:
                        candidates.append(candidate)
                
                # Check candidates in batch
                if candidates:
                    logger.info(f"[Domain Check] Checking {len(candidates)} suggestions...")
                    batch_results = await dynadot_service.check_multiple_domains(candidates)
                    
                    # Filter for available and affordable ones
                    for domain_name, data in batch_results.items():
                        if data.get("available") and data.get("is_free", False):
                            suggestions.append(data)
                            
                    # Sort by price (cheapest first)
                    suggestions.sort(key=lambda x: x.get("price", 999999))
                    logger.info(f"[Domain Check] Found {len(suggestions)} valid suggestions")

            result["suggestions"] = suggestions
            
            logger.info(f"[Domain Check] Result for {domain}: available={result.get('available', False)}, error={result.get('error', 'None')}")
            
            return {
                "success": True,
                "result": result
            }
        except ValueError as ve:
            # API not configured
            logger.warning(f"Dynadot configuration error: {ve}")
            return {
                "success": False,
                "error": str(ve),
                "result": {
                    "available": False,
                    "error": str(ve),
                    "domain": domain,
                    "suggestions": []
                }
            }
    except ValueError as e:
        logger.error(f"ValueError checking domain: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking domain: {e}", exc_info=True)
        # Return error in result instead of raising exception to avoid frontend hanging
        return {
            "success": False,
            "error": str(e),
            "result": {
                "available": False,
                "error": str(e),
                "domain": request.domain.strip() if request.domain else None,
                "suggestions": []
            }
        }


@router.post("/purchase")
async def purchase_domain(
    request: DomainPurchaseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Purchase a domain via Dynadot (public endpoint, no auth required).
    Used by onboarding form to purchase domain.
    """
    try:
        if not request.domain or not request.domain.strip():
            raise HTTPException(status_code=400, detail="Domain is required")
        
        # Verify order exists
        from app.repositories.order_repository import OrderRepository
        repo = OrderRepository(db)
        order = await repo.find_by_identifier(request.order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        dynadot_service = DynadotService(db)
        
        # First check availability
        availability = await dynadot_service.check_domain_availability(request.domain.strip())
        if not availability.get("available"):
            return {
                "success": False,
                "error": "Domain is not available",
                "availability": availability
            }
        
        # Register domain
        result = await dynadot_service.register_domain(
            request.domain.strip(),
            request.duration_years
        )
        
        if result.get("success"):
            # Update order onboarding with purchase info
            if order.onboarding:
                order.onboarding.domain_to_purchase = request.domain.strip()
                order.onboarding.domain_purchased = True
                order.onboarding.domain_purchase_status = "purchased"
                await db.commit()
            
            # Notify admins
            try:
                from app.api.notifications import notify_all_admins
                await notify_all_admins(
                    db,
                    title=f"Domínio Comprado - Pedido #{order.id}",
                    message=f"Domínio {request.domain.strip()} foi comprado com sucesso\nCliente: {order.customer_name}",
                    notification_type="success",
                    related_entity_type="site_order",
                    related_entity_id=order.id
                )
            except Exception as e:
                print(f"Failed to notify admins: {e}")
        
        return {
            "success": result.get("success", False),
            "result": result,
            "order_id": order.id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao comprar domínio: {str(e)}")
