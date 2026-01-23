"""
Site Generator Service
Orchestrates the generation of website code based on onboarding data.
"""
import os
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.site_order import SiteOrder, SiteOrderStatus
from app.services.ai_service import AIService
from datetime import datetime

logger = logging.getLogger(__name__)

class SiteGeneratorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai = AIService(db)

    async def generate_site(self, order_id: int):
        """
        Main workflow:
        1. Fetch Order & Onboarding
        2. Construct Prompt
        3. Call AI (Coding Task)
        4. Parse Result
        5. Write to File System
        6. Update Status
        """
        logger.info(f"Starting generation for Order #{order_id}")
        
        # 1. Fetch Data
        order = await self.db.get(SiteOrder, order_id)
        if not order:
            raise ValueError("Order not found")
            
        onboarding = order.onboarding
        if not onboarding:
            raise ValueError("Onboarding data missing")

        # 2. Construct Prompt
        # We generally want a structured JSON output of filesystem
        prompt = self._build_prompt(onboarding)
        
        try:
            # 3. Call AI
            # 'coding' is the task_type we defined in the Task Routing
            response = await self.ai.generate(
                task_type="coding",
                prompt=prompt,
                system_instruction="You are a Senior React/Next.js Developer. Output PURE JSON ONLY."
            )
            
            # 4. Parse Result (Expect JSON: { "files": [ { "path": "...", "content": "..." } ] })
            # If output ismarkdown fenced, clean it
            content = response.get("content", "")
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            project_data = json.loads(content)
            
            # 5. Write to Disk
            # Using the ID as the folder name
            target_dir = os.path.abspath(os.path.join(os.getcwd(), "generated_sites", str(order.id)))
            os.makedirs(target_dir, exist_ok=True)
            
            for file in project_data.get("files", []):
                file_path = os.path.join(target_dir, file["path"])
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file["content"])
            
            # 6. Update Status
            order.status = SiteOrderStatus.REVIEW
            order.site_url = f"https://preview.innexar.com/p/{order.id}" # Mock for now
            order.admin_notes = "Site generated successfully via AI Worker."
            await self.db.commit()
            
            return {
                "success": True, 
                "files_generated": len(project_data.get("files", [])),
                "path": target_dir
            }

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            order.admin_notes = f"Generation Failed: {str(e)}"
            await self.db.commit()
            raise e

    def _build_prompt(self, data) -> str:
        """
        Creates the massive prompt for the AI.
        """
        # Simplify data for prompt context
        context = {
            "business_name": data.business_name,
            "niche": data.niche,
            "city": data.primary_city,
            "services": data.services,
            "colors": {
                "primary": data.primary_color,
                "secondary": data.secondary_color
            },
            "contact": {
                "email": data.business_email,
                "phone": data.business_phone
            },
            "pages": data.selected_pages or ["Home", "Services", "About", "Contact"]
        }
        
        return f"""
        Generate a complete Next.js 14 (App Router) + Tailwind CSS website for a client.
        
        CLIENT DETAILS:
        {json.dumps(context, indent=2)}
        
        REQUIREMENTS:
        1. Use 'lucide-react' for icons.
        2. Use 'framer-motion' for simple animations.
        3. Components should be modern, clean, and responsive.
        4. Create a folder structure suitable for App Router.
        
        OUTPUT FORMAT:
        Return ONLY valid JSON with this structure:
        {{
          "files": [
            {{ "path": "app/page.tsx", "content": "..." }},
            {{ "path": "components/Header.tsx", "content": "..." }},
            {{ "path": "styles/globals.css", "content": "..." }}
          ]
        }}
        
        Do not explain. Just JSON.
        """
