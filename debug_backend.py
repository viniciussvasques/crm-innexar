import sys
import os
import asyncio
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.database import engine
from app.api.site_generator_config import router as site_router
from app.main import app

async def check_db():
    print("Checking database connection and tables...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"Found tables: {tables}")
            
            required = ['integration_configs', 'deploy_servers', 'system_configs', 'ai_configs']
            missing = [t for t in required if t not in tables]
            
            if missing:
                print(f"ERROR: Missing tables: {missing}")
            else:
                print("All required tables present.")
    except Exception as e:
        print(f"Database error: {e}")

def check_routes():
    print("\nChecking registered routes...")
    found_deploy = False
    for route in app.routes:
        if hasattr(route, 'path') and 'deploy-servers' in route.path:
            print(f"Found route: {route.path}")
            found_deploy = True
    
    if not found_deploy:
        print("ERROR: /api/config/deploy-servers route NOT found in app.")

async def main():
    await check_db()
    check_routes()

if __name__ == "__main__":
    asyncio.run(main())
