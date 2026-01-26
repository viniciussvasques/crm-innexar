import asyncio
import os
import sys

# Add backend directory to python path
sys.path.append(os.path.abspath("/opt/innexar-crm/backend"))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def debug_logs():
    async with AsyncSessionLocal() as session:
        print("=== Checking AI Task Routing ===")
        result = await session.execute(text("SELECT * FROM ai_task_routing"))
        routings = result.fetchall()
        if not routings:
            print("NO ROUTING RULES FOUND!")
        else:
            for r in routings:
                print(r)

        print("\n=== Checking AI Configs ===")
        result = await session.execute(text("SELECT id, name, provider, is_active, LEFT(api_key, 8) as key_prefix FROM ai_configs WHERE id IN (4, 5)"))
        configs = result.fetchall()
        for c in configs:
            print(c)

        print("\n=== Checking Recent Site Generation Logs (Last 10) ===")
        result = await session.execute(text("SELECT * FROM site_generation_logs ORDER BY created_at DESC LIMIT 10"))
        logs = result.fetchall()
        if not logs:
            print("NO LOGS FOUND!")
        else:
            for log in logs:
                print(f"[{log.created_at}] Order {log.order_id} | {log.step} | {log.status} | {log.message}")
                if log.details:
                    print(f"   Details: {log.details}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(debug_logs())
