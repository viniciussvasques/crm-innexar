from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal

class ColorPalette(BaseModel):
    primary: str = Field(..., description="Main brand color (hex)")
    secondary: str = Field(..., description="Secondary color (hex)")
    accent: str = Field(..., description="Accent color for buttons/CTAs (hex)")
    background: str = Field(..., description="Background color (hex, usually white/light gray)")
    text: str = Field(..., description="Main text color (hex)")

class SiteSection(BaseModel):
    type: Literal['hero', 'features', 'about', 'services', 'testimonials', 'contact', 'gallery', 'faq', 'cta']
    title: str
    subtitle: Optional[str] = None
    content: str = Field(..., description="Main text content/copy for this section")
    image_prompt: Optional[str] = Field(None, description="Prompt to generate an image for this section")

class SitePage(BaseModel):
    path: str = Field(..., description="URL path, e.g., '/' or '/about'")
    title: str = Field(..., description="Page title for SEO")
    description: str = Field(..., description="Meta description")
    sections: List[SiteSection]

class SiteContent(BaseModel):
    """
    The 'Blueprint' that the AI Builder will use to write code.
    Verified by the user BEFORE code generation.
    """
    business_name: str
    tagline: str
    colors: ColorPalette
    fonts: Dict[str, str] = Field(..., description="Font assignments (heading, body)")
    pages: List[SitePage]
    
    # Global copy
    footer_text: str
    contact_phone: str
    contact_email: str
    address: Optional[str] = None
