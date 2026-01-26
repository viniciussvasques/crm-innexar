from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import engine, Base
from app.api import (
    auth, users, contacts, opportunities, activities, dashboard, projects, 
    external, commissions, quote_requests, notifications, ai, templates, 
    goals, ai_actions, ai_config, ai_chat, lead_analysis, webhooks, 
    ai_public, site_orders, system_config, public_config, emails, 
    site_customers, site_generator_config, site_files, launch
)


# Criar tabelas
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI(
    title="Innexar CRM API",
    description="API para CRM interno da Innexar",
    version="1.0.0"
)

# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic validation errors as readable strings"""
    errors = exc.errors()
    if errors:
        # Get the first error message
        first_error = errors[0]
        field = '.'.join(str(loc) for loc in first_error.get('loc', []) if loc != 'body')
        message = first_error.get('msg', 'Validation error')
        error_message = f"{field}: {message}" if field else message
        
        # Special handling for missing Authorization header
        if 'authorization' in str(first_error.get('loc', [])).lower() or 'credentials' in str(first_error.get('loc', [])).lower():
            error_message = "Token de autenticação não fornecido ou formato inválido. Use: Authorization: Bearer <token>"
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": error_message, "errors": errors}
            )
    else:
        error_message = "Validation error"
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_message, "errors": errors}
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])
app.include_router(opportunities.router, prefix="/api/opportunities", tags=["opportunities"])
app.include_router(activities.router, prefix="/api/activities", tags=["activities"])
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(external.router, prefix="/api", tags=["external"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(commissions.router, prefix="/api", tags=["commissions"])
app.include_router(quote_requests.router, prefix="/api", tags=["quote-requests"])
app.include_router(notifications.router, prefix="/api", tags=["notifications"])
app.include_router(ai.router, prefix="/api", tags=["ai"])
app.include_router(ai_actions.router, prefix="/api", tags=["ai-actions"])
app.include_router(ai_config.router, prefix="/api", tags=["ai-config"])
app.include_router(ai_chat.router, prefix="/api", tags=["ai-chat"])
app.include_router(lead_analysis.router, prefix="/api", tags=["lead-analysis"])
app.include_router(webhooks.router, prefix="/api", tags=["webhooks"])
app.include_router(ai_public.router, prefix="/api/ai/public", tags=["ai-public"])
app.include_router(templates.router, prefix="/api", tags=["templates"])
app.include_router(goals.router, prefix="/api", tags=["goals"])
app.include_router(site_orders.router, prefix="/api", tags=["site-orders"])
app.include_router(system_config.router, prefix="/api", tags=["system-config"])
app.include_router(public_config.router, prefix="/api", tags=["public-config"])
app.include_router(emails.router, tags=["emails"])
app.include_router(site_customers.router, prefix="/api", tags=["site-customers"])
app.include_router(site_generator_config.router, prefix="/api", tags=["site-generator-config"])
app.include_router(site_files.router, prefix="/api", tags=["site-files"])
app.include_router(launch.router, prefix="/api", tags=["launch"])

# New clean customer auth module
from app.api.customer_auth import router as customer_auth_router
app.include_router(customer_auth_router, prefix="/api", tags=["customer-auth"])

# Support Tickets (customer-facing, uses customer-auth prefix)
from app.api.support_tickets import router as support_tickets_router
app.include_router(support_tickets_router, prefix="/api/customer-auth", tags=["support-tickets"])

# Admin Tickets (workspace, requires staff auth)
from app.api.admin_tickets import router as admin_tickets_router
app.include_router(admin_tickets_router, prefix="/api/tickets", tags=["admin-tickets"])


@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/")
async def root():
    return {"message": "Innexar CRM API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

