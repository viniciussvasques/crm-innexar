from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.models.site_order import SiteAddon, SiteTemplate, SiteNiche

class CatalogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_addons(self, active_only: bool = True) -> List[SiteAddon]:
        query = select(SiteAddon).order_by(SiteAddon.sort_order)
        if active_only:
            query = query.where(SiteAddon.is_active == True)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_addon(self, addon: SiteAddon) -> SiteAddon:
        self.db.add(addon)
        await self.db.commit()
        await self.db.refresh(addon)
        return addon

    async def get_addon(self, addon_id: int) -> Optional[SiteAddon]:
        return await self.db.get(SiteAddon, addon_id)

    async def update_addon(self, addon: SiteAddon) -> SiteAddon:
        # Note: Caller is responsible for setting attributes on the object
        await self.db.commit()
        await self.db.refresh(addon)
        return addon

    async def list_templates(self, niche: Optional[SiteNiche] = None, active_only: bool = True) -> List[SiteTemplate]:
        query = select(SiteTemplate).order_by(SiteTemplate.sort_order)
        if active_only:
            query = query.where(SiteTemplate.is_active == True)
        if niche:
            query = query.where(SiteTemplate.niche == niche)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_template(self, template: SiteTemplate) -> SiteTemplate:
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def get_template(self, template_id: int) -> Optional[SiteTemplate]:
        return await self.db.get(SiteTemplate, template_id)

    async def update_template(self, template: SiteTemplate) -> SiteTemplate:
        await self.db.commit()
        await self.db.refresh(template)
        return template
