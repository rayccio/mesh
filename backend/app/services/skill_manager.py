import json
import os
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.skill import Skill, SkillVersion, AgentSkill, SkillCreate, SkillVersionCreate, SkillVisibility
from ..core.config import settings
from ..core.database import AsyncSessionLocal
from ..repositories.skill_repository import SkillRepository
from ..repositories.skill_version_repository import SkillVersionRepository
import uuid
import logging

logger = logging.getLogger(__name__)

class SkillManager:
    def __init__(self):
        self.skill_repo = SkillRepository
        self.version_repo = SkillVersionRepository
        # Agent skills are stored in the agent's JSON data, not in a separate table
        # We'll handle them via AgentManager

    async def _get_skill_repo(self, session: AsyncSession = None):
        if session:
            return SkillRepository(session), session
        s = AsyncSessionLocal()
        return SkillRepository(s), s

    async def _get_version_repo(self, session: AsyncSession = None):
        if session:
            return SkillVersionRepository(session), session
        s = AsyncSessionLocal()
        return SkillVersionRepository(s), s

    async def create_skill(self, skill_in: SkillCreate) -> Skill:
        skill_id = f"sk-{uuid.uuid4().hex[:8]}"
        skill = Skill(
            id=skill_id,
            **skill_in.dict(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        repo, session = await self._get_skill_repo()
        try:
            created = await repo.create(skill)
        finally:
            await session.close()
        return created

    async def get_skill(self, skill_id: str) -> Optional[Skill]:
        repo, session = await self._get_skill_repo()
        try:
            return await repo.get(skill_id)
        finally:
            await session.close()

    async def list_skills(self, visibility: Optional[SkillVisibility] = None, author_id: Optional[str] = None) -> List[Skill]:
        repo, session = await self._get_skill_repo()
        try:
            skills = await repo.get_all()
            if visibility:
                skills = [s for s in skills if s.visibility == visibility]
            if author_id:
                skills = [s for s in skills if s.author_id == author_id]
            return skills
        finally:
            await session.close()

    async def update_skill(self, skill_id: str, **updates) -> Optional[Skill]:
        repo, session = await self._get_skill_repo()
        try:
            skill = await repo.get(skill_id)
            if not skill:
                return None
            for k, v in updates.items():
                if hasattr(skill, k):
                    setattr(skill, k, v)
            skill.updated_at = datetime.utcnow()
            await repo.update(skill_id, skill.dict(by_alias=True))
            return skill
        finally:
            await session.close()

    async def delete_skill(self, skill_id: str) -> bool:
        repo, session = await self._get_skill_repo()
        try:
            # First delete all versions
            vrepo, vsession = await self._get_version_repo()
            try:
                versions = await vrepo.get_by_skill(skill_id)
                for v in versions:
                    await vrepo.delete(v.id)
            finally:
                await vsession.close()
            return await repo.delete(skill_id)
        finally:
            await session.close()

    async def create_version(self, skill_id: str, version_in: SkillVersionCreate) -> SkillVersion:
        # Check skill exists
        skill = await self.get_skill(skill_id)
        if not skill:
            raise ValueError("Skill not found")
        version_id = f"sv-{uuid.uuid4().hex[:8]}"
        version = SkillVersion(
            id=version_id,
            skill_id=skill_id,
            **version_in.dict(),
            created_at=datetime.utcnow()
        )
        repo, session = await self._get_version_repo()
        try:
            created = await repo.create(version)
        finally:
            await session.close()
        return created

    async def get_version(self, version_id: str) -> Optional[SkillVersion]:
        repo, session = await self._get_version_repo()
        try:
            return await repo.get(version_id)
        finally:
            await session.close()

    async def list_versions(self, skill_id: str) -> List[SkillVersion]:
        repo, session = await self._get_version_repo()
        try:
            return await repo.get_by_skill(skill_id)
        finally:
            await session.close()

    async def update_version(self, version_id: str, **updates) -> Optional[SkillVersion]:
        repo, session = await self._get_version_repo()
        try:
            version = await repo.get(version_id)
            if not version:
                return None
            for k, v in updates.items():
                if hasattr(version, k):
                    setattr(version, k, v)
            await repo.update(version_id, version.dict(by_alias=True))
            return version
        finally:
            await session.close()

    # Agent skills are managed via AgentManager's skills field (JSON)
    # We'll keep those methods as before, but they should use AgentManager
    # For simplicity, we'll keep them here but they must call AgentManager to update the agent's JSON.
    # However, to avoid circular imports, we'll have AgentManager handle agent skills directly.
    # So these methods will be moved to AgentManager.
    # We'll keep the interface but redirect.
    async def install_skill(self, agent_id: str, skill_id: str, version_id: Optional[str] = None, config: dict = None):
        # This should be handled by AgentManager
        from .agent_manager import AgentManager  # local import to avoid circular
        agent_manager = AgentManager(docker_service=None)  # docker_service not needed for worker agents
        return await agent_manager.install_skill(agent_id, skill_id, version_id, config)

    async def uninstall_skill(self, agent_id: str, skill_id: str) -> bool:
        from .agent_manager import AgentManager
        agent_manager = AgentManager(docker_service=None)
        return await agent_manager.uninstall_skill(agent_id, skill_id)

    async def get_agent_skills(self, agent_id: str) -> List[AgentSkill]:
        from .agent_manager import AgentManager
        agent_manager = AgentManager(docker_service=None)
        agent = await agent_manager.get_agent(agent_id)
        if agent:
            return agent.skills
        return []

    async def update_agent_skill_config(self, agent_id: str, skill_id: str, config: dict) -> Optional[AgentSkill]:
        from .agent_manager import AgentManager
        agent_manager = AgentManager(docker_service=None)
        return await agent_manager.update_agent_skill_config(agent_id, skill_id, config)
