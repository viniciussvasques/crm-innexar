from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, users, contacts, opportunities, activities, dashboard, projects, external, commissions, quote_requests, notifications, ai, templates, goals, ai_actions, ai_config, ai_chat, lead_analysis, webhooks, ai_public, site_orders, system_config, public_config, emails


# Criar tabelas
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI(
    title="Innexar CRM API",
    description="API para CRM interno da Innexar",
    version="1.0.0"
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


@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/")
async def root():
    return {"message": "Innexar CRM API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

