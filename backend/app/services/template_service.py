"""
Template Service
Manages template selection and customization for site generation.
"""
import os
import json
import shutil
from pathlib import Path
from typing import Dict, Optional, List
from app.models.site_order import SiteOnboarding

class TemplateService:
    """Service for managing and applying templates"""
    
    TEMPLATES_BASE_DIR = Path(os.getenv("TEMPLATES_BASE_DIR", "/app/templates"))
    
    def __init__(self):
        self.templates_dir = self.TEMPLATES_BASE_DIR
    
    def select_template(self, onboarding: SiteOnboarding) -> str:
        """
        Selects the best template based on onboarding data.
        
        Returns template name (e.g., "premium-static", "landing-page")
        """
        # Always use premium-static for now (we can add more templates later)
        return "premium-static"
    
    def get_template_path(self, template_name: str) -> Path:
        """Get the base path for a template"""
        return self.templates_dir / template_name / "base"
    
    def template_exists(self, template_name: str) -> bool:
        """Check if template exists"""
        return self.get_template_path(template_name).exists()
    
    def copy_template_base(self, template_name: str, target_dir: str) -> bool:
        """
        Copies template base files to target directory.
        
        Returns True if successful, False otherwise.
        """
        template_path = self.get_template_path(template_name)
        
        if not template_path.exists():
            return False
        
        try:
            # Copy entire template structure
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            
            shutil.copytree(template_path, target_dir)
            return True
        except Exception as e:
            print(f"Error copying template: {e}")
            return False
    
    def get_customization_prompt(self, template_name: str, onboarding: SiteOnboarding) -> str:
        """
        Generates a minimal prompt for customizing the template.
        
        This is much smaller than generating everything from scratch.
        """
        context = {
            "business_name": onboarding.business_name,
            "niche": onboarding.niche,
            "city": onboarding.primary_city,
            "services": onboarding.services,
            "colors": {
                "primary": onboarding.primary_color,
                "secondary": onboarding.secondary_color
            },
            "contact": {
                "email": onboarding.business_email,
                "phone": onboarding.business_phone
            },
            "pages": onboarding.selected_pages or ["Home", "Services", "About", "Contact"]
        }
        
        return f"""
        Customize the existing Next.js template with the following client details:
        
        CLIENT DETAILS:
        {json.dumps(context, indent=2)}
        
        TASKS:
        1. Update all text content to match the business name and services
        2. Update color scheme (primary: {onboarding.primary_color}, secondary: {onboarding.secondary_color})
        3. Update contact information (email, phone)
        4. Customize page content based on selected pages: {', '.join(context['pages'])}
        5. Ensure all components use the correct business information
        
        OUTPUT FORMAT:
        Return ONLY a JSON object with this structure:
        {{
          "customizations": [
            {{
              "file": "app/page.tsx",
              "changes": "List of specific changes to make"
            }}
          ],
          "new_content": {{
            "hero_title": "...",
            "hero_subtitle": "...",
            "services": [...]
          }}
        }}
        
        Keep changes minimal - only what needs to be customized.
        """
    
    def apply_customizations(self, target_dir: str, customizations: Dict) -> bool:
        """
        Applies customizations from AI to the template.
        
        This is a simplified version - in production, you'd want more robust
        file editing logic.
        """
        try:
            # Apply new content
            if "new_content" in customizations:
                content = customizations["new_content"]
                
                # Update main page
                page_path = os.path.join(target_dir, "app", "page.tsx")
                if os.path.exists(page_path):
                    with open(page_path, "r", encoding="utf-8") as f:
                        page_content = f.read()
                    
                    # Simple replacements (in production, use AST or more sophisticated parsing)
                    if "hero_title" in content:
                        page_content = page_content.replace("{{HERO_TITLE}}", content["hero_title"])
                    if "hero_subtitle" in content:
                        page_content = page_content.replace("{{HERO_SUBTITLE}}", content["hero_subtitle"])
                    
                    with open(page_path, "w", encoding="utf-8") as f:
                        f.write(page_content)
            
            # Apply file-specific changes
            if "customizations" in customizations:
                for change in customizations.get("customizations", []):
                    file_path = os.path.join(target_dir, change.get("file", ""))
                    if os.path.exists(file_path):
                        # In production, implement proper file editing
                        pass
            
            return True
        except Exception as e:
            print(f"Error applying customizations: {e}")
            return False
