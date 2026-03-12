from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from ..models.db_models import SkillVersionModel
from ..models.skill import SkillVersion
from ..utils.json_encoder import prepare_json_data
import json

class SkillVersionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, version: SkillVersion) -> SkillVersion:
        data = prepare_json_data(version.model_dump(by_alias=True))
        db_version = SkillVersionModel(
            id=version.id,
            skill_id=version.skill_id,
            data=data
        )
        self.db.add(db_version)
        await self.db.commit()
        await self.db.refresh(db_version)
        return version

    async def get(self, version_id: str) -> SkillVersion | None:
        result = await self.db.execute(
            select(SkillVersionModel).where(SkillVersionModel.id == version_id)
        )
        db_version = result.scalar_one_or_none()
        if db_version:
            return SkillVersion(**db_version.data)
        return None

    async def get_by_skill(self, skill_id: str) -> list[SkillVersion]:
        result = await self.db.execute(
            select(SkillVersionModel).where(SkillVersionModel.skill_id == skill_id)
        )
        db_versions = result.scalars().all()
        return [SkillVersion(**v.data) for v in db_versions]

    async def update(self, version_id: str, updates: dict) -> SkillVersion | None:
        version = await self.get(version_id)
        if not version:
            return None
        data = prepare_json_data(updates)
        await self.db.execute(
            update(SkillVersionModel)
            .where(SkillVersionModel.id == version_id)
            .values(data=data)
        )
        await self.db.commit()
        return version

    async def delete(self, version_id: str) -> bool:
        result = await self.db.execute(
            delete(SkillVersionModel).where(SkillVersionModel.id == version_id)
        )
        await self.db.commit()
        return result.rowcount > 0
