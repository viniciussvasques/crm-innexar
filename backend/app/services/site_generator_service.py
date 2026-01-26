"""
Site Generator Service
Orchestrates the generation of website code based on onboarding data.
"""
import os
import json
import logging
import asyncio
import traceback
import re
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models.site_order import SiteOrder, SiteOrderStatus
from app.services.ai_service import AIService
from app.services.config_service import ConfigService
from app.services.template_service import TemplateService
from app.core.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class SiteGeneratorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai = AIService(db)

    async def _log_progress(self, order_id: int, step: str, message: str, status: str = "info", details: dict = None):
        """Emits a log entry to database (and acts as hook for SSE/Websockets)"""
        try:
            # Use asyncpg directly to avoid SQLAlchemy transaction conflicts
            import asyncpg
            import os
            
            # Ensure details is properly serialized
            details_json = None
            if details:
                try:
                    details_json = json.dumps(details)
                except (TypeError, ValueError) as e:
                    logger.warning(f"Could not serialize details for log: {e}")
                    details_json = json.dumps({"error": "Could not serialize details"})
            
            # Parse database URL
            database_url = os.getenv("DATABASE_URL", "postgresql://crm_user:senha_forte_aqui@postgres:5432/innexarcrm")
            # Remove asyncpg prefix if present
            if database_url.startswith("postgresql+asyncpg://"):
                database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
            elif database_url.startswith("postgresql://"):
                pass  # Already correct
            else:
                raise ValueError(f"Invalid database URL format: {database_url}")
            
            # Parse connection details
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            
            # Connect directly with asyncpg (no transaction, auto-commit)
            conn = await asyncpg.connect(
                host=parsed.hostname or "postgres",
                port=parsed.port or 5432,
                user=parsed.username or "crm_user",
                password=parsed.password or "senha_forte_aqui",
                database=parsed.path.lstrip("/") or "innexarcrm"
            )
            
            try:
                # Try with jsonb first, fallback to text if column is not jsonb
                try:
                    log_id = await conn.fetchval("""
                        INSERT INTO site_generation_logs (order_id, step, message, status, details, created_at) 
                        VALUES ($1, $2, $3, $4, $5::jsonb, NOW())
                        RETURNING id
                    """, order_id, step, message, status, details_json)
                except Exception as jsonb_error:
                    # Retry without jsonb cast
                    log_id = await conn.fetchval("""
                        INSERT INTO site_generation_logs (order_id, step, message, status, details, created_at) 
                        VALUES ($1, $2, $3, $4, $5, NOW())
                        RETURNING id
                    """, order_id, step, message, status, details_json)
                
                logger.info(f"[{order_id}] [{log_id}] {step}: {message} (status: {status})")
            finally:
                await conn.close()
        except Exception as e:
            # Log to console even if DB logging fails
            logger.error(f"Failed to log progress to database for order {order_id}: {e}", exc_info=True)
            # Also print to console as fallback
            print(f"[LOG ERROR] Order {order_id} - {step}: {message} - Error: {e}")

    def _get_target_dir(self, order_id: int) -> str:
        """Get the target directory for generated files"""
        # Use absolute path to ensure consistency with volume mount
        base_dir = os.getenv("SITES_BASE_DIR", "/app/generated_sites")
        return os.path.join(base_dir, f"project_{order_id}")
    
    def _replace_template_placeholders(self, target_dir: str, onboarding, order):
        """Replace placeholders in template files with actual data"""
        import re
        
        # Build replacement map
        replacements = {
            "{{BUSINESS_NAME}}": onboarding.business_name,
            "{{BUSINESS_DESCRIPTION}}": onboarding.site_description or f"{onboarding.business_name} - {onboarding.primary_service}",
            "{{BUSINESS_TAGLINE}}": onboarding.site_description or onboarding.primary_service,
            "{{BUSINESS_EMAIL}}": onboarding.business_email,
            "{{BUSINESS_PHONE}}": onboarding.business_phone,
            "{{BUSINESS_ADDRESS}}": onboarding.business_address or "",
            "{{PRIMARY_COLOR}}": onboarding.primary_color or "#3B82F6",
            "{{SECONDARY_COLOR}}": onboarding.secondary_color or "#1E40AF",
            "{{ACCENT_COLOR}}": onboarding.accent_color or "#F59E0B",
            "{{CTA_TEXT}}": onboarding.cta_text or "Entre em Contato",
            "{{HERO_TITLE}}": f"Bem-vindo à {onboarding.business_name}",
            "{{HERO_SUBTITLE}}": onboarding.site_description or f"{onboarding.primary_service} em {onboarding.primary_city}",
            "{{ABOUT_PREVIEW_TEXT}}": onboarding.about_owner or onboarding.site_description or f"Somos {onboarding.business_name}, especializados em {onboarding.primary_service}.",
            "{{ABOUT_FULL_TEXT}}": onboarding.about_owner or onboarding.site_description or f"{onboarding.business_name} é uma empresa dedicada a oferecer {onboarding.primary_service} de alta qualidade em {onboarding.primary_city}.",
            "{{YEARS_IN_BUSINESS}}": str(onboarding.years_in_business) if onboarding.years_in_business else "",
        }
        
        # Calculate color variations
        def darken_color(hex_color, factor=0.8):
            """Darken a hex color"""
            hex_color = hex_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            rgb = tuple(int(c * factor) for c in rgb)
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        
        primary_color = onboarding.primary_color or "#3B82F6"
        secondary_color = onboarding.secondary_color or "#1E40AF"
        replacements["{{PRIMARY_COLOR_DARK}}"] = darken_color(primary_color)
        replacements["{{SECONDARY_COLOR_DARK}}"] = darken_color(secondary_color)
        
        # Social media
        replacements["{{SOCIAL_FACEBOOK}}"] = getattr(onboarding, 'social_facebook', '') or ''
        replacements["{{SOCIAL_INSTAGRAM}}"] = getattr(onboarding, 'social_instagram', '') or ''
        
        # Business hours
        if hasattr(onboarding, 'business_hours') and onboarding.business_hours:
            hours_text = []
            days_map = {
                'monday': 'Segunda-feira',
                'tuesday': 'Terça-feira',
                'wednesday': 'Quarta-feira',
                'thursday': 'Quinta-feira',
                'friday': 'Sexta-feira',
                'saturday': 'Sábado',
                'sunday': 'Domingo'
            }
            for day, hours in onboarding.business_hours.items():
                day_name = days_map.get(day, day.capitalize())
                hours_text.append(f"{day_name}: {hours}")
            replacements["{{BUSINESS_HOURS}}"] = "\\n".join(hours_text)
        else:
            replacements["{{BUSINESS_HOURS}}"] = ""
        
        # Services
        services_list = []
        for i, service in enumerate(onboarding.services or []):
            services_list.append(f"    {{ title: '{service}', description: 'Serviço profissional de {service} com qualidade e dedicação.' }},")
        replacements["{{#SERVICES}}"] = "\\n".join(services_list)
        replacements["{{/SERVICES}}"] = ""
        
        # Testimonials
        testimonials_list = []
        if hasattr(onboarding, 'testimonials') and onboarding.testimonials:
            for testimonial in onboarding.testimonials:
                name = testimonial.get('name', 'Cliente')
                text = testimonial.get('text', '')
                rating = testimonial.get('rating', 5)
                testimonials_list.append(f"    {{ name: '{name}', text: '{text}', rating: {rating} }},")
        else:
            # Default testimonials
            testimonials_list.append("    { name: 'Cliente Satisfeito', text: 'Excelente serviço e atendimento!', rating: 5 },")
        replacements["{{#TESTIMONIALS}}"] = "\\n".join(testimonials_list)
        replacements["{{/TESTIMONIALS}}"] = ""
        
        # Replace in all files
        for root, dirs, files in os.walk(target_dir):
            # Skip node_modules if it exists
            if 'node_modules' in root:
                continue
                
            for file in files:
                if file.endswith(('.tsx', '.ts', '.js', '.jsx', '.json', '.css', '.md')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Replace all placeholders
                        for placeholder, value in replacements.items():
                            content = content.replace(placeholder, str(value))
                        
                        # Remove conditional blocks that are empty
                        content = re.sub(r'\{\{#.*?\}\}.*?\{\{/.*?\}\}', '', content, flags=re.DOTALL)
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                    except Exception as e:
                        logger.warning(f"Failed to replace placeholders in {file_path}: {e}")
                        continue
    
    async def _generate_custom_content(self, order_id: int, target_dir: str, onboarding):
        """Generate custom content (hero text, descriptions) via AI"""
        try:
            prompt = f"""
Generate professional, engaging content for a {onboarding.niche} business website.

BUSINESS:
- Name: {onboarding.business_name}
- Description: {onboarding.site_description or onboarding.primary_service}
- Services: {', '.join(onboarding.services or [])}
- Location: {onboarding.primary_city}, {onboarding.state}
- Tone: {onboarding.tone.value if hasattr(onboarding.tone, 'value') else onboarding.tone}

OUTPUT JSON:
{{
  "hero_title": "Engaging hero title (max 60 chars)",
  "hero_subtitle": "Compelling subtitle (max 120 chars)",
  "about_preview": "Brief about section (2-3 sentences)",
  "about_full": "Complete about section (4-6 sentences)",
  "service_descriptions": {{
    "{onboarding.services[0] if onboarding.services else 'Service'}": "Professional description (2-3 sentences)"
  }}
}}

Return ONLY valid JSON, no markdown, no explanations.
"""
            
            response = await self.ai.generate(
                task_type="creative_writing",
                prompt=prompt,
                system_instruction="You are a professional copywriter. Output ONLY valid JSON."
            )
            
            if response and response.get('content'):
                content = response.get('content')
                # Extract JSON
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                try:
                    ai_content = json.loads(content)
                    
                    # Update files with AI-generated content
                    hero_file = os.path.join(target_dir, "app", "page.tsx")
                    if os.path.exists(hero_file):
                        with open(hero_file, 'r', encoding='utf-8') as f:
                            hero_content = f.read()
                        
                        if ai_content.get('hero_title'):
                            hero_content = re.sub(r'Bem-vindo à .*?', ai_content['hero_title'], hero_content, count=1)
                        if ai_content.get('hero_subtitle'):
                            hero_content = re.sub(r'hero_subtitle.*?\n', f"hero_subtitle: '{ai_content['hero_subtitle']}',\\n", hero_content)
                        
                        with open(hero_file, 'w', encoding='utf-8') as f:
                            f.write(hero_content)
                    
                    await self._log_progress(order_id, "AI_CONTENT_APPLIED", "AI-generated content applied successfully", "success")
                except json.JSONDecodeError as e:
                    logger.warning(f"[{order_id}] Failed to parse AI content JSON: {e}")
                    await self._log_progress(order_id, "AI_CONTENT_ERROR", f"Failed to parse AI content: {e}", "warning")
        except Exception as e:
            logger.warning(f"[{order_id}] AI content generation failed (non-fatal): {e}")
            await self._log_progress(order_id, "AI_CONTENT_ERROR", f"AI content generation failed (non-fatal): {e}", "warning")
            # Continue anyway - template has default content
    
    def _check_stage_files(self, target_dir: str) -> dict:
        """Check which stage files exist and determine current stage"""
        stages = {
            "phase_1": False,  # Strategy briefing
            "phase_2": False,  # Code files exist
            "phase_3": False   # All files written
        }
        
        if not os.path.exists(target_dir):
            return {"current_stage": "none", "stages": stages, "files_count": 0}
        
        # Check for Phase 1: Strategy briefing (deliverable in DB, not files)
        # Phase 1 is tracked via deliverables, so we check DB later
        
        # Check for Phase 2 & 3: Code files
        files_count = 0
        has_package_json = False
        has_app_dir = False
        
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                files_count += 1
                if file == "package.json":
                    has_package_json = True
                if "app" in root or "src" in root:
                    has_app_dir = True
        
        if files_count > 0:
            stages["phase_2"] = True
        if has_package_json and has_app_dir and files_count > 5:
            stages["phase_3"] = True
        
        # Determine current stage
        if stages["phase_3"]:
            current_stage = "phase_3"
        elif stages["phase_2"]:
            current_stage = "phase_2"
        else:
            current_stage = "phase_1"
        
        return {
            "current_stage": current_stage,
            "stages": stages,
            "files_count": files_count
        }
    
    async def generate_site(self, order_id: int, resume: bool = True):
        """
        Main workflow with retry/resume capability:
        1. Check current stage and existing files
        2. Resume from last stage or start from beginning
        3. Fetch Order & Onboarding
        4. Construct Prompt
        5. Call AI (Coding Task)
        6. Parse Result
        7. Write to File System
        8. Update Status
        """
        # Ensure generated_sites directory exists (use absolute path)
        base_dir = os.getenv("SITES_BASE_DIR", "/app/generated_sites")
        os.makedirs(base_dir, exist_ok=True)
        
        target_dir = self._get_target_dir(order_id)
        stage_info = self._check_stage_files(target_dir)
        
        # Check order status first - if already completed, don't resume/regenerate
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(SiteOrder)
            .options(selectinload(SiteOrder.onboarding))
            .where(SiteOrder.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            await self._log_progress(order_id, "ERROR", "Order not found", "error")
            raise ValueError("Order not found")
        
        # If order is already in REVIEW or DELIVERED status, don't resume/regenerate
        if order.status in [SiteOrderStatus.REVIEW, SiteOrderStatus.DELIVERED]:
            await self._log_progress(
                order_id,
                "SKIP",
                f"Order already in {order.status.value} status. Skipping generation.",
                "info"
            )
            return {
                "success": True,
                "message": f"Order already in {order.status.value} status",
                "skipped": True
            }
        
        if resume and stage_info["current_stage"] != "none":
            await self._log_progress(
                order_id, 
                "RESUME", 
                f"Resuming generation from stage: {stage_info['current_stage']} (found {stage_info['files_count']} existing files)", 
                "info",
                stage_info
            )
            
            # Only restart if order is still in GENERATING status (incomplete generation)
            # If order is in REVIEW, the files are valid and we shouldn't clear them
            if order.status == SiteOrderStatus.GENERATING and stage_info["current_stage"] in ["phase_2", "phase_3"]:
                await self._log_progress(
                    order_id,
                    "RESUME_DECISION",
                    f"Found incomplete generation (status: {order.status.value}). Restarting from Phase 2 (Code Generation) to ensure consistency",
                    "info"
                )
                # Clear existing files to start fresh
                if os.path.exists(target_dir):
                    import shutil
                    try:
                        shutil.rmtree(target_dir)
                        await self._log_progress(order_id, "CLEANUP", "Removed incomplete files to restart generation", "info")
                    except Exception as e:
                        await self._log_progress(order_id, "CLEANUP_WARNING", f"Could not remove old files: {e}", "warning")
            elif order.status == SiteOrderStatus.REVIEW:
                # Order is already in REVIEW, files are valid - don't clear them
                await self._log_progress(
                    order_id,
                    "SKIP",
                    f"Order in REVIEW status with existing files. Files are valid, skipping cleanup.",
                    "info"
                )
                return {
                    "success": True,
                    "message": "Order already has valid generated files",
                    "skipped": True
                }
        else:
            await self._log_progress(order_id, "START", "Starting generation process", "info")
        
        # === PHASE 1: STRATEGY ===
        # Phase 1 is optional - if it fails, we continue with code generation
        # Use a separate try/except to ensure session stays clean
        try:
            # Ensure clean session before Phase 1
            try:
                await self.db.rollback()
            except:
                pass
            
            # Check if briefing already exists
            from sqlalchemy import select
            from app.models.site_deliverable import SiteDeliverable, DeliverableType
            result = await self.db.execute(
                select(SiteDeliverable)
                .where(SiteDeliverable.order_id == order_id)
                .where(SiteDeliverable.type == DeliverableType.BRIEFING)
            )
            existing_briefing = result.scalar_one_or_none()
            
            if existing_briefing:
                await self._log_progress(order_id, "PHASE_1_SKIP", "Strategy briefing already exists, skipping Phase 1", "info")
            else:
                # Try to generate strategy, but don't let it break the session
                try:
                    briefing = await self.generate_strategy_brief(order_id)
                except Exception as strategy_error:
                    # Use logger.exception for full stack trace
                    logger.exception(f"[{order_id}] Phase 1 failed: %r", strategy_error)
                    
                    # Capture full error details
                    error_type = type(strategy_error).__name__
                    error_msg = str(strategy_error) if str(strategy_error) else f"{error_type} occurred"
                    
                    # Log error but don't break the session
                    error_details = {
                        "error_type": error_type,
                        "error_message": error_msg,
                        "phase": "PHASE_1",
                        "traceback": traceback.format_exc()
                    }
                    await self._log_progress(
                        order_id, 
                        "PHASE_1_ERROR", 
                        f"Strategy phase failed (non-critical): {error_msg}", 
                        "warning",
                        error_details
                    )
                    # Ensure session is clean after error
                    try:
                        await self.db.rollback()
                    except:
                        pass
        except Exception as e:
            # If Phase 1 completely fails, rollback and continue
            try:
                await self.db.rollback()
            except:
                pass
            # Use logger.exception for full stack trace
            logger.exception(f"[{order_id}] Phase 1 outer exception: %r", e)
            
            # Capture full error details
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else f"{error_type} occurred"
            error_details = {
                "error_type": error_type,
                "error_message": error_msg,
                "phase": "PHASE_1",
                "traceback": traceback.format_exc()
            }
            await self._log_progress(
                order_id, 
                "PHASE_1_ERROR", 
                f"Strategy phase failed: {error_msg}", 
                "warning",
                error_details
            )
            # Continue anyway - strategy is optional
        
        # === PHASE 2 & 3: CODE ===
        
        # 1. Fetch Data (order already fetched above, but refresh to ensure latest state)
        await self._log_progress(order_id, "FETCH_DATA", "Loading order and onboarding details", "info")
        
        # Ensure clean transaction state before querying
        # Always start with a fresh query - rollback any existing transaction
        try:
            await self.db.rollback()
        except:
            pass  # Ignore if no transaction exists
        
        # Refresh order to ensure we have latest state (in case it was modified)
        try:
            await self.db.refresh(order)
        except:
            # If refresh fails, re-fetch
            result = await self.db.execute(
                select(SiteOrder)
                .options(selectinload(SiteOrder.onboarding))
                .where(SiteOrder.id == order_id)
            )
            order = result.scalar_one_or_none()
            if not order:
                await self._log_progress(order_id, "ERROR", "Order not found", "error")
                raise ValueError("Order not found")
        
        onboarding = order.onboarding
        if not onboarding:
            try:
                await self.db.rollback()
            except:
                pass
            await self._log_progress(order_id, "ERROR", "Onboarding data missing", "error")
            raise ValueError("Onboarding data missing")

        # 2. Use Template Base
        template_service = TemplateService()
        template_name = template_service.select_template(onboarding)
        
        await self._log_progress(order_id, "TEMPLATE_START", f"Using template: {template_name}", "info")
        
        # Copy template base to target directory
        if template_service.template_exists(template_name):
            if not template_service.copy_template_base(template_name, target_dir):
                await self._log_progress(order_id, "TEMPLATE_ERROR", f"Failed to copy template {template_name}", "error")
                raise ValueError(f"Failed to copy template {template_name}")
            
            await self._log_progress(order_id, "TEMPLATE_COPIED", f"Template {template_name} copied successfully", "success")
            
            # Replace placeholders in template files
            await self._log_progress(order_id, "TEMPLATE_CUSTOMIZE", "Customizing template with client data", "info")
            self._replace_template_placeholders(target_dir, onboarding, order)
            await self._log_progress(order_id, "TEMPLATE_CUSTOMIZED", "Template customized successfully", "success")
            
            # Generate additional content via AI (hero text, descriptions, etc)
            await self._log_progress(order_id, "AI_CONTENT_GENERATION", "Generating custom content via AI", "info")
            await self._generate_custom_content(order_id, target_dir, onboarding)
            
            # Skip the full AI generation - template is already complete
            files_count = len([f for f in Path(target_dir).rglob('*') if f.is_file()])
            await self._log_progress(order_id, "WRITE_COMPLETE", f"Template site ready with {files_count} files", "success")
            
            # Jump to integrations (skip AI generation and file writing)
            deployment_info = {}
            try:
                await self._log_progress(order_id, "INTEGRATIONS_START", "Starting integrations (GitHub, R2, Pages, DNS)", "info")
                deployment_info = await self._run_integrations(order_id, target_dir, order)
            except Exception as e:
                logger.error(f"[{order_id}] Integration error (non-fatal): {e}", exc_info=True)
                await self._log_progress(order_id, "INTEGRATIONS_ERROR", f"Integration error (non-fatal): {str(e)}", "warning")
            
            # Update status
            await self._log_progress(order_id, "FINALIZE", "Updating order status to REVIEW", "info")
            await self.db.refresh(order)
            order.status = SiteOrderStatus.REVIEW
            
            if deployment_info.get("pages_url"):
                order.site_url = deployment_info["pages_url"]
            else:
                order.site_url = f"https://preview.innexar.com/p/{order.id}"
            
            admin_notes_parts = [f"Site gerado usando template {template_name}"]
            if deployment_info.get("github_repo"):
                admin_notes_parts.append(f"GitHub: {deployment_info['github_repo']}")
            if deployment_info.get("pages_url"):
                admin_notes_parts.append(f"Pages: {deployment_info['pages_url']}")
            order.admin_notes = " | ".join(admin_notes_parts)
            
            await self.db.commit()
            await self._log_progress(order_id, "SUCCESS", "Site generation completed successfully!", "success", {
                "files_generated": files_count,
                "template_used": template_name,
                "deployment_info": deployment_info
            })
            
            return {
                "success": True,
                "files_generated": files_count,
                "path": target_dir,
                "template_used": template_name,
                "deployment_info": deployment_info
            }
        else:
            # Fallback to full AI generation if template doesn't exist
            await self._log_progress(order_id, "TEMPLATE_NOT_FOUND", f"Template {template_name} not found, using full AI generation", "warning")
            # 2. Construct Prompt
            await self._log_progress(order_id, "BUILD_PROMPT", "Constructing AI Prompt based on requirements", "info")
            prompt = self._build_prompt(onboarding)
        
        try:
            # 3. Call AI
            await self._log_progress(order_id, "AI_GENERATION", "Sending request to AI Model (Coding Task)... this may take a while", "info")
            logger.info(f"[{order_id}] Calling AI service with prompt length: {len(prompt)}")
            
            # Call AI with explicit error handling
            try:
                response = await self.ai.generate(
                    task_type="coding",
                    prompt=prompt,
                    system_instruction="You are a Senior React/Next.js Developer. Output PURE JSON ONLY."
                )
                
                if not response:
                    raise ValueError("AI service returned None")
                
                content = response.get('content', '')
                if not content:
                    raise ValueError("AI service returned empty content")
                
                logger.info(f"[{order_id}] ✅ AI response received: {len(content)} characters")
                await self._log_progress(order_id, "AI_COMPLETE", f"AI response received ({len(content)} chars)", "success")
            except Exception as ai_error:
                # CRITICAL: Log the REAL error FIRST before transforming it
                # This ensures we capture the actual exception, not a transformed one
                logger.error(f"[{order_id}] ❌ AI call failed: %r", ai_error)
                logger.error(f"[{order_id}] ❌ AI call traceback:\n%s", traceback.format_exc())
                
                # Build comprehensive error message from the ORIGINAL exception
                error_type = type(ai_error).__name__
                error_msg_raw = str(ai_error) if str(ai_error) else repr(ai_error)
                
                # Extract meaningful error message - always use repr if str is empty
                if error_msg_raw and error_msg_raw.strip():
                    error_msg = error_msg_raw
                elif hasattr(ai_error, 'args') and ai_error.args:
                    error_msg = f"{error_type}: {', '.join(repr(a) for a in ai_error.args)}"
                else:
                    error_msg = f"{error_type}: {repr(ai_error)}"
                
                # Build error details for logging to DB
                error_details = {
                    "error_type": error_type,
                    "error_message": error_msg,
                    "error_repr": repr(ai_error),
                    "traceback": traceback.format_exc()
                }
                
                # Add HTTP-specific details if available
                if hasattr(ai_error, 'response'):
                    try:
                        error_details["status_code"] = getattr(ai_error.response, 'status_code', None)
                        response_text = getattr(ai_error.response, 'text', '')
                        error_details["response_text"] = response_text[:500] if response_text else "Empty response"
                    except Exception as e:
                        error_details["response_extraction_error"] = str(e)
                if hasattr(ai_error, 'request'):
                    try:
                        error_details["request_url"] = str(getattr(ai_error.request, 'url', 'Unknown'))
                    except:
                        pass
                
                # Log to database with full details
                await self._log_progress(
                    order_id, 
                    "AI_ERROR", 
                    f"AI call failed: {error_msg}", 
                    "error",
                    error_details
                )
                
                # Raise with meaningful message, preserving original exception
                # Use !r to ensure we always have a message
                raise ValueError(f"AI generation failed: {error_msg!r}") from ai_error
            
            # 4. Parse Result
            await self._log_progress(order_id, "PARSE_RESULT", "Parsing generated code", "info")
            content = response.get("content", "")
            logger.info(f"[{order_id}] Raw AI content length: {len(content)}")
            
            if not content or len(content.strip()) == 0:
                await self._log_progress(order_id, "ERROR", "AI returned empty response", "error")
                raise ValueError("AI returned empty response")
            
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            logger.info(f"[{order_id}] Extracted content length: {len(content)}")
            
            try:
                project_data = json.loads(content)
                logger.info(f"[{order_id}] Parsed JSON successfully. Files count: {len(project_data.get('files', []))}")
            except json.JSONDecodeError as e:
                # Log the REAL error with full context
                logger.error(f"[{order_id}] JSON parse error: %r", e)
                logger.error(f"[{order_id}] JSON parse error traceback:\n%s", traceback.format_exc())
                
                # Try to fix common JSON issues
                fixed_content = content
                attempts = [
                    # Try to fix unescaped backslashes in strings
                    lambda c: c.replace('\\n', '\\\\n').replace('\\t', '\\\\t'),
                    # Try to remove trailing commas
                    lambda c: re.sub(r',(\s*[}\]])', r'\1', c),
                    # Try to fix unescaped quotes in strings (basic attempt)
                    lambda c: re.sub(r'(?<!\\)"(?![,}\]:\s])', '\\"', c),
                ]
                
                for i, fix_attempt in enumerate(attempts):
                    try:
                        fixed_content = fix_attempt(fixed_content)
                        project_data = json.loads(fixed_content)
                        logger.info(f"[{order_id}] JSON fixed with attempt {i+1}. Files count: {len(project_data.get('files', []))}")
                        break
                    except json.JSONDecodeError:
                        continue
                else:
                    # All fix attempts failed
                    error_pos = getattr(e, 'pos', None)
                    error_msg = str(e)
                    
                    # Log content around error position if available
                    content_preview = content[:2000] if len(content) > 2000 else content
                    if error_pos and error_pos < len(content):
                        # Show context around error
                        start = max(0, error_pos - 100)
                        end = min(len(content), error_pos + 100)
                        error_context = content[start:end]
                        logger.error(f"[{order_id}] JSON error at position {error_pos}, context: ...{error_context}...")
                    
                    error_details = {
                        "error_type": "JSONDecodeError",
                        "error_message": error_msg,
                        "error_pos": error_pos,
                        "content_length": len(content),
                        "content_preview": content_preview,
                        "traceback": traceback.format_exc()
                    }
                    
                    await self._log_progress(
                        order_id, 
                        "ERROR", 
                        f"Failed to parse AI output as JSON: {error_msg}", 
                        "error", 
                        error_details
                    )
                    raise ValueError(f"Invalid JSON output from AI: {error_msg}. The AI response may have been truncated or malformed.") from e
            
            # 5. Write to Disk
            files_count = len(project_data.get("files", []))
            await self._log_progress(order_id, "WRITE_FILES", f"Writing {files_count} files to disk", "info")
            
            target_dir = self._get_target_dir(order.id)
            os.makedirs(target_dir, exist_ok=True)
            
            written_count = 0
            for file in project_data.get("files", []):
                try:
                    file_path = os.path.join(target_dir, file["path"])
                    # Security: Prevent path traversal
                    if not os.path.abspath(file_path).startswith(os.path.abspath(target_dir)):
                        await self._log_progress(order_id, "SECURITY_WARNING", f"Skipping suspicious path: {file['path']}", "warning")
                        continue
                    
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(file["content"])
                    written_count += 1
                    
                    # Log every 10 files to avoid spam
                    if written_count % 10 == 0:
                        await self._log_progress(order_id, "WRITE_PROGRESS", f"Written {written_count}/{files_count} files", "info")
                except Exception as e:
                    await self._log_progress(order_id, "WRITE_ERROR", f"Failed to write {file.get('path', 'unknown')}: {e}", "error")
            
            await self._log_progress(order_id, "WRITE_COMPLETE", f"Successfully wrote {written_count}/{files_count} files", "success")
            
            # 6. Integrations (GitHub, R2, Pages, DNS)
            deployment_info = {}
            try:
                await self._log_progress(order_id, "INTEGRATIONS_START", "Starting integrations (GitHub, R2, Pages, DNS)", "info")
                deployment_info = await self._run_integrations(order_id, target_dir, order)
            except Exception as e:
                logger.error(f"[{order_id}] Integration error (non-fatal): {e}", exc_info=True)
                await self._log_progress(order_id, "INTEGRATIONS_ERROR", f"Integration error (non-fatal): {str(e)}", "warning")
                # Continue even if integrations fail
            
            # 7. Update Status
            await self._log_progress(order_id, "FINALIZE", "Updating order status to REVIEW", "info")
            # Refresh order to ensure we have the latest state
            await self.db.refresh(order)
            order.status = SiteOrderStatus.REVIEW
            
            # Set site URL from deployment info if available
            if deployment_info.get("pages_url"):
                order.site_url = deployment_info["pages_url"]
            elif deployment_info.get("github_url"):
                order.site_url = deployment_info["github_url"]
            else:
                order.site_url = f"https://preview.innexar.com/p/{order.id}"
            
            order.admin_notes = "Site generated successfully via AI Worker."
            if deployment_info:
                notes_parts = [order.admin_notes]
                if deployment_info.get("github_repo"):
                    notes_parts.append(f"GitHub: {deployment_info['github_repo']}")
                if deployment_info.get("pages_url"):
                    notes_parts.append(f"Pages: {deployment_info['pages_url']}")
                order.admin_notes = " | ".join(notes_parts)
            
            await self.db.commit()
            
            await self._log_progress(order_id, "SUCCESS", "Site generation completed successfully!", "success", {
                "path": target_dir,
                "deployment": deployment_info
            })
            return {
                "success": True, 
                "files_generated": files_count,
                "path": target_dir,
                "deployment": deployment_info
            }

        except Exception as e:
            # Use logger.exception for full stack trace
            logger.exception(f"Generation failed for order {order_id}: %r", e)
            
            # Capture full error details
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else f"{error_type} occurred"
            error_details = {
                "error_type": error_type,
                "error_message": error_msg,
                "traceback": traceback.format_exc()
            }
            await self._log_progress(
                order_id, 
                "ERROR", 
                f"Fatal error: {error_msg}", 
                "error", 
                error_details
            )
            
            # Update order status but don't fail completely - allow retry
            try:
                # Refresh order to ensure we have the latest state
                await self.db.refresh(order)
                order.admin_notes = f"Generation Failed: {str(e)}. Will retry automatically or you can retry manually."
                # Keep as GENERATING to allow automatic retry via auto-start-stuck-orders
                # Don't revert to BUILDING - this allows the system to detect and retry automatically
                if order.status == SiteOrderStatus.GENERATING:
                    # Already GENERATING, keep it
                    pass
                else:
                    # If somehow not GENERATING, set it
                    order.status = SiteOrderStatus.GENERATING
                await self.db.commit()
            except Exception as commit_error:
                logger.error(f"Failed to update order status after error: {commit_error}", exc_info=True)
            
            # Don't raise - allow the system to retry later
            return {
                "success": False,
                "error": str(e),
                "can_retry": True
            }

    def _build_prompt(self, data) -> str:
        """
        Creates the massive prompt for the AI.
        """
        # Build comprehensive context
        pages_list = data.selected_pages or ["Home", "Services", "About", "Contact"]
        pages_slugs = {
            "Home": "home",
            "Sobre": "sobre", 
            "About": "sobre",
            "Cardápio": "cardapio",
            "Menu": "cardapio",
            "Services": "servicos",
            "Serviços": "servicos",
            "Contato": "contato",
            "Contact": "contato",
            "Depoimentos": "depoimentos",
            "Testimonials": "depoimentos",
            "FAQ": "faq",
            "Pricing": "precos",
            "Preços": "precos",
            "Gallery": "galeria",
            "Galeria": "galeria"
        }
        
        context = {
            "business_name": data.business_name,
            "business_description": data.site_description or f"{data.business_name} - {data.primary_service}",
            "niche": data.niche,
            "city": data.primary_city,
            "state": data.state,
            "services": data.services,
            "primary_service": data.primary_service,
            "colors": {
                "primary": data.primary_color or "#3B82F6",
                "secondary": data.secondary_color or "#1E40AF",
                "accent": data.accent_color or "#F59E0B"
            },
            "contact": {
                "email": data.business_email,
                "phone": data.business_phone,
                "address": data.business_address,
                "has_whatsapp": data.has_whatsapp
            },
            "social": {
                "facebook": getattr(data, 'social_facebook', None),
                "instagram": getattr(data, 'social_instagram', None),
                "linkedin": getattr(data, 'social_linkedin', None),
                "youtube": getattr(data, 'social_youtube', None)
            },
            "pages": pages_list,
            "tone": data.tone.value if hasattr(data.tone, 'value') else str(data.tone),
            "cta": data.cta_text or "Entre em Contato",
            "testimonials": getattr(data, 'testimonials', None),
            "business_hours": getattr(data, 'business_hours', None),
            "about_owner": getattr(data, 'about_owner', None),
            "years_in_business": getattr(data, 'years_in_business', None)
        }
        
        # Build pages mapping
        pages_mapping = []
        for page in pages_list:
            slug = pages_slugs.get(page, page.lower().replace(" ", "-"))
            pages_mapping.append({"name": page, "slug": slug})
        
        return f"""
You are a Senior Next.js Developer. Generate a COMPLETE, PRODUCTION-READY Next.js 14 website with App Router.

CLIENT DETAILS:
{json.dumps(context, indent=2, ensure_ascii=False)}

REQUIRED PAGES (generate ALL of them):
{json.dumps(pages_mapping, indent=2, ensure_ascii=False)}

MANDATORY FILES TO GENERATE:

1. CONFIGURATION FILES (REQUIRED):
   - package.json (with all dependencies: next, react, react-dom, typescript, tailwindcss, lucide-react, framer-motion)
   - tsconfig.json (Next.js TypeScript config)
   - next.config.js (Next.js configuration)
   - tailwind.config.js (Tailwind CSS config with custom colors)
   - .gitignore (standard Next.js gitignore)
   - README.md (project documentation)

2. APP ROUTER STRUCTURE (REQUIRED):
   - app/layout.tsx (root layout with metadata, fonts, global styles)
   - app/page.tsx (home page - MUST be complete with hero, features, CTA sections)
   - app/globals.css (Tailwind directives + custom CSS)
   
3. ALL REQUESTED PAGES (REQUIRED - generate each one):
{chr(10).join(f'   - app/{pages_slugs.get(p, p.lower().replace(" ", "-"))}/page.tsx' for p in pages_list)}

4. COMPONENTS (REQUIRED - create reusable components):
   - components/Header.tsx (navigation with all page links)
   - components/Footer.tsx (footer with contact info, social links)
   - components/Hero.tsx (hero section component)
   - components/ServiceCard.tsx (service card component)
   - components/TestimonialCard.tsx (if testimonials exist)
   - components/ContactForm.tsx (contact form component)
   - components/Button.tsx (reusable button component)
   - components/Section.tsx (section wrapper component)

5. UTILITIES (if needed):
   - lib/utils.ts (utility functions, cn helper for Tailwind)

TECHNICAL REQUIREMENTS:
- Use Next.js 14 App Router (app/ directory)
- TypeScript for all files
- Tailwind CSS for styling (use provided colors: {context['colors']['primary']}, {context['colors']['secondary']}, {context['colors']['accent']})
- Use 'lucide-react' for icons (import from 'lucide-react')
- Use 'framer-motion' for smooth animations
- All components must be responsive (mobile-first)
- Use semantic HTML5 elements
- Implement proper SEO (meta tags in layout.tsx)
- All pages must have proper structure with Header and Footer
- Contact forms should be functional (use Next.js form handling)
- Use Next.js Image component for any images
- Follow Next.js best practices

CONTENT REQUIREMENTS:
- Home page: Hero section, Services/Features section, About preview, CTA section
- Services page: List all services with descriptions
- About page: Business story, owner info (if provided), values
- Contact page: Contact form, address, phone, email, business hours (if provided)
- Testimonials page: Display testimonials (if provided)
- All pages must have relevant, professional content in Portuguese
- Use the business name, description, and services throughout

DESIGN REQUIREMENTS:
- Modern, clean, professional design
- Use the provided color palette consistently
- Implement smooth hover effects and transitions
- Ensure good contrast and readability
- Mobile-responsive navigation (hamburger menu for mobile)
- Professional typography

CRITICAL - OUTPUT FORMAT:
Return ONLY valid, complete JSON with this EXACT structure:
{{
  "files": [
    {{ "path": "package.json", "content": "..." }},
    {{ "path": "tsconfig.json", "content": "..." }},
    {{ "path": "next.config.js", "content": "..." }},
    {{ "path": "tailwind.config.js", "content": "..." }},
    {{ "path": ".gitignore", "content": "..." }},
    {{ "path": "app/layout.tsx", "content": "..." }},
    {{ "path": "app/page.tsx", "content": "..." }},
    {{ "path": "app/globals.css", "content": "..." }},
    {{ "path": "app/sobre/page.tsx", "content": "..." }},
    {{ "path": "app/cardapio/page.tsx", "content": "..." }},
    {{ "path": "components/Header.tsx", "content": "..." }},
    {{ "path": "components/Footer.tsx", "content": "..." }},
    ... (ALL other required files)
  ]
}}

JSON VALIDATION RULES:
- ALL strings MUST be properly escaped (use \\\\ for backslashes, \\" for quotes, \\n for newlines)
- ALL strings MUST be enclosed in double quotes
- NO trailing commas
- NO unescaped newlines inside string values
- The JSON MUST be complete and valid - do not truncate it
- If content is long, ensure proper JSON escaping of all special characters
- Generate AT LEAST 20-30 files for a complete website

Example of proper escaping:
"content": "import React from 'react';\\n\\nexport default function Page() {{ return <div>Hello</div>; }}"

IMPORTANT: 
- Generate ALL requested pages
- Include ALL configuration files
- Create a COMPLETE, functional website
- Do not skip any required files
- Each page must be fully functional with proper content

Do not explain. Return ONLY the JSON object, nothing else.
"""

    async def generate_strategy_brief(self, order_id: int):
        """Phase 1: Generates the Executive Strategy Briefing"""
        from app.models.site_deliverable import SiteDeliverable, DeliverableType, DeliverableStatus
        
        await self._log_progress(order_id, "PHASE_1_START", "Starting Strategy Phase: Consultant Agent", "info")
        
        # Fetch Data
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(SiteOrder)
            .options(selectinload(SiteOrder.onboarding))
            .where(SiteOrder.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order: raise ValueError("Order not found")
        
        # Build Prompt for "Consultant Persona"
        prompt = f"""
        Act as a C-Level Digital Strategy Consultant.
        Analyze this business and create a Strategic Website Briefing.
        
        BUSINESS_DATA:
        Name: {order.onboarding.business_name}
        Niche: {order.onboarding.niche}
        Description: {order.onboarding.site_description}
        Services: {order.onboarding.services}
        Target Audience: {order.onboarding.custom_niche or "General public"}
        
        OUTPUT FORMAT (Markdown):
        # Executive Summary
        [Analysis of the business opportunity]
        
        # Target Audience Persona
        [Who are they, what are their pain points]
        
        # Brand Voice & Tone
        [How the website should communicate]
        
        # Key Differentials
        [Why choose this business]
        
        # Strategic Objectives
        [What the site needs to achieve]
        """
        
        await self._log_progress(order_id, "AI_STRATEGY", "Consultant Agent analyzing business model...", "info")
        
        try:
            briefing_response = await self.ai.generate(
                task_type="creative_writing", # We might need to add this to routing or reuse 'coding'/default
                prompt=prompt,
                system_instruction="You are a high-end Digital Strategy Consultant. Output professional Markdown."
            )
            content = briefing_response.get("content", "")
        except Exception as strategy_ai_error:
            # CRITICAL: Log the REAL error FIRST before transforming it
            logger.error(f"[{order_id}] ❌ Strategy AI call failed: %r", strategy_ai_error)
            logger.error(f"[{order_id}] ❌ Strategy AI call traceback:\n%s", traceback.format_exc())
            
            # Build error message from original exception
            error_type = type(strategy_ai_error).__name__
            error_msg = str(strategy_ai_error) if str(strategy_ai_error) else repr(strategy_ai_error)
            
            error_details = {
                "error_type": error_type,
                "error_message": error_msg,
                "error_repr": repr(strategy_ai_error),
                "traceback": traceback.format_exc(),
                "phase": "PHASE_1_STRATEGY"
            }
            
            await self._log_progress(
                order_id,
                "PHASE_1_ERROR",
                f"Strategy AI call failed: {error_msg}",
                "error",
                error_details
            )
            # Re-raise to be caught by outer handler
            raise ValueError(f"Strategy phase failed: {error_msg!r}") from strategy_ai_error
        
        # Save Deliverable
        deliverable = SiteDeliverable(
            order_id=order.id,
            type=DeliverableType.BRIEFING,
            title="Strategic Executive Briefing",
            content=content,
            status=DeliverableStatus.READY,
            is_visible_to_client=True
        )
        self.db.add(deliverable)
        await self.db.commit()
        
        await self._log_progress(order_id, "PHASE_1_COMPLETE", "Strategy Briefing generated successfully", "success")
        return deliverable
    
    async def _run_integrations(self, order_id: int, target_dir: str, order: SiteOrder) -> dict:
        """
        Run all integrations: GitHub, R2, Pages, DNS
        
        Args:
            order_id: Site order ID
            target_dir: Directory with generated files
            order: SiteOrder object
            
        Returns:
            Dict with deployment information
        """
        deployment_info = {}
        
        # Create sync session for services (they use sync Session)
        sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        sync_engine = create_engine(sync_db_url)
        SyncSession = sessionmaker(bind=sync_engine)
        sync_db = SyncSession()
        
        try:
            # 1. GitHub - Create repository and commit files
            try:
                await self._log_progress(order_id, "GITHUB_START", "Creating GitHub repository...", "info")
                from app.services.github_service import GitHubService
                github_service = GitHubService(sync_db)
                
                repo_name = f"site-{order_id}"
                # Load onboarding to avoid lazy loading issues
                from sqlalchemy.orm import selectinload
                from sqlalchemy import select
                result = await self.db.execute(
                    select(SiteOrder)
                    .options(selectinload(SiteOrder.onboarding))
                    .where(SiteOrder.id == order_id)
                )
                order_with_onboarding = result.scalar_one_or_none()
                business_name = order_with_onboarding.onboarding.business_name if order_with_onboarding and order_with_onboarding.onboarding else 'Client'
                
                repo_result = await github_service.create_repository(
                    repo_name=repo_name,
                    private=False,
                    description=f"Website for {business_name}"
                )
                
                deployment_info["github_repo"] = repo_result.get("html_url")
                deployment_info["github_clone_url"] = repo_result.get("clone_url")
                
                # Collect all files to commit
                files_to_commit = {}
                for root, dirs, files in os.walk(target_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, target_dir)
                        # Convert to forward slashes for GitHub
                        github_path = rel_path.replace("\\", "/")
                        
                        with open(file_path, "rb") as f:
                            files_to_commit[github_path] = f.read()
                
                # Commit all files
                commit_result = await github_service.commit_files(
                    repo_name=repo_name,
                    files=files_to_commit,
                    message=f"Initial commit: Generated website for order {order_id}",
                    branch=github_service._default_branch
                )
                
                await self._log_progress(order_id, "GITHUB_SUCCESS", f"GitHub repository created and files committed", "success")
            except Exception as e:
                logger.error(f"[{order_id}] GitHub integration failed: {e}", exc_info=True)
                await self._log_progress(order_id, "GITHUB_ERROR", f"GitHub integration failed: {str(e)}", "warning")
            
            # 2. R2 - Upload assets (images, etc.)
            try:
                await self._log_progress(order_id, "R2_START", "Uploading assets to R2...", "info")
                from app.services.cloudflare_r2_service import CloudflareR2Service
                r2_service = CloudflareR2Service(sync_db)
                
                # Find and upload image assets
                assets_uploaded = 0
                for root, dirs, files in os.walk(target_dir):
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico')):
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, target_dir)
                            r2_key = f"sites/{order_id}/{rel_path.replace(chr(92), '/')}"
                            
                            with open(file_path, "rb") as f:
                                content = f.read()
                                content_type = f"image/{file.split('.')[-1].lower()}"
                                if file.endswith('.svg'):
                                    content_type = "image/svg+xml"
                                
                                r2_service.upload_file(r2_key, content, content_type)
                                assets_uploaded += 1
                
                if assets_uploaded > 0:
                    deployment_info["r2_assets"] = assets_uploaded
                    await self._log_progress(order_id, "R2_SUCCESS", f"Uploaded {assets_uploaded} assets to R2", "success")
                else:
                    await self._log_progress(order_id, "R2_SKIP", "No assets found to upload", "info")
            except Exception as e:
                logger.error(f"[{order_id}] R2 integration failed: {e}", exc_info=True)
                await self._log_progress(order_id, "R2_ERROR", f"R2 integration failed: {str(e)}", "warning")
            
            # 3. Cloudflare Pages - Deploy site
            try:
                await self._log_progress(order_id, "PAGES_START", "Creating Cloudflare Pages project...", "info")
                from app.services.cloudflare_pages_service import CloudflarePagesService
                pages_service = CloudflarePagesService(sync_db)
                
                project_name = pages_service.get_project_name(order_id)
                
                # Get GitHub repo info if available
                github_repo_url = deployment_info.get("github_clone_url", "")
                repo_owner = None
                repo_name = None
                
                if github_repo_url and "github.com" in github_repo_url:
                    # Extract owner and repo from URL
                    # Format: https://github.com/owner/repo.git or https://github.com/owner/repo
                    parts = github_repo_url.replace("https://github.com/", "").replace(".git", "").split("/")
                    if len(parts) >= 2:
                        repo_owner = parts[0]
                        repo_name = parts[1]
                
                # Check if project already exists
                existing_project = await pages_service.get_project(project_name)
                if not existing_project:
                    # Create new project with GitHub integration if available
                    if repo_owner and repo_name:
                        project_result = await pages_service.create_project_with_github(
                            project_name=project_name,
                            repo_owner=repo_owner,
                            repo_name=repo_name,
                            production_branch="main",
                            build_command="npm run build",
                            output_directory=".next"
                        )
                        deployment_info["pages_project"] = project_name
                        deployment_info["pages_url"] = f"https://{project_result.get('url', f'{project_name}.pages.dev')}"
                        await self._log_progress(order_id, "PAGES_SUCCESS", f"Cloudflare Pages project created with GitHub integration: {deployment_info['pages_url']}", "success")
                    else:
                        # Create without GitHub (will need manual connection)
                        project_result = await pages_service.create_project(
                            project_name=project_name,
                            production_branch="main"
                        )
                        deployment_info["pages_project"] = project_name
                        deployment_info["pages_url"] = f"https://{project_result.get('url', f'{project_name}.pages.dev')}"
                        await self._log_progress(order_id, "PAGES_SUCCESS", f"Cloudflare Pages project created: {deployment_info['pages_url']}. Connect GitHub manually in dashboard.", "success")
                else:
                    # Project exists, try to connect GitHub if we have repo info
                    deployment_info["pages_project"] = project_name
                    deployment_info["pages_url"] = f"https://{existing_project.get('subdomain', f'{project_name}.pages.dev')}"
                    
                    if repo_owner and repo_name:
                        try:
                            await pages_service.connect_github_repository(
                                project_name=project_name,
                                repo_owner=repo_owner,
                                repo_name=repo_name,
                                production_branch="main",
                                build_command="npm run build",
                                output_directory=".next"
                            )
                            await self._log_progress(order_id, "PAGES_GITHUB_CONNECTED", f"Connected GitHub repository to existing Pages project", "success")
                        except Exception as gh_err:
                            logger.warning(f"[{order_id}] Failed to connect GitHub to existing project: {gh_err}")
                            await self._log_progress(order_id, "PAGES_GITHUB_WARNING", f"Pages project exists. Connect GitHub manually: {repo_owner}/{repo_name}", "warning")
                    else:
                        await self._log_progress(order_id, "PAGES_EXISTS", f"Cloudflare Pages project already exists: {deployment_info['pages_url']}", "info")
                
                # Note: Full Git integration requires OAuth setup in Cloudflare dashboard
                # The API can configure build settings, but the actual Git connection needs OAuth
                # After OAuth is set up once, future projects can use it automatically
            except Exception as e:
                logger.error(f"[{order_id}] Cloudflare Pages integration failed: {e}", exc_info=True)
                await self._log_progress(order_id, "PAGES_ERROR", f"Cloudflare Pages integration failed: {str(e)}", "warning")
            
            # 4. DNS - Create subdomain (if configured)
            try:
                await self._log_progress(order_id, "DNS_START", "Creating DNS subdomain...", "info")
                from app.services.cloudflare_dns_service import CloudflareDNSService
                dns_service = CloudflareDNSService(sync_db)
                
                subdomain = f"site-{order_id}"
                # Get Pages URL to point DNS to
                pages_url = deployment_info.get("pages_url", "")
                if pages_url:
                    # Extract domain from Pages URL (e.g., site-24.pages.dev)
                    target = pages_url.replace("https://", "").replace("http://", "")
                    
                    # Create CNAME record
                    dns_result = await dns_service.create_subdomain(
                        subdomain=subdomain,
                        target=target,
                        record_type="CNAME"
                    )
                    deployment_info["dns_subdomain"] = subdomain
                    deployment_info["dns_record"] = dns_result.get("name")
                    await self._log_progress(order_id, "DNS_SUCCESS", f"DNS subdomain created: {subdomain}", "success")
                else:
                    await self._log_progress(order_id, "DNS_SKIP", "Skipping DNS: No Pages URL available", "info")
            except Exception as e:
                logger.error(f"[{order_id}] DNS integration failed: {e}", exc_info=True)
                await self._log_progress(order_id, "DNS_ERROR", f"DNS integration failed: {str(e)}", "warning")
            
        finally:
            sync_db.close()
            sync_engine.dispose()
        
        return deployment_info