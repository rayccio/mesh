from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..models.db_models import GlobalSettingsModel
from ..models.types import GlobalSettings
import json

class GlobalSettingsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self) -> GlobalSettings | None:
        result = await self.db.execute(
            select(GlobalSettingsModel).where(GlobalSettingsModel.id == 1)
        )
        db_settings = result.scalar_one_or_none()
        if db_settings:
            return GlobalSettings(**db_settings.data)
        return None

    async def set(self, settings: GlobalSettings) -> GlobalSettings:
        # Upsert (id=1)
        db_settings = await self.db.get(GlobalSettingsModel, 1)
        if db_settings:
            db_settings.data = settings.dict()
        else:
            db_settings = GlobalSettingsModel(id=1, data=settings.dict())
            self.db.add(db_settings)
        await self.db.commit()
        return settings
