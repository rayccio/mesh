import json
import os
from typing import Dict, Optional, List, Set
from datetime import datetime
from ..models.types import Agent, AgentCreate, AgentUpdate, AgentStatus, ChannelConfig, MetaInfo, ReasoningConfig, ReportingTarget, AgentRole
from ..core.config import settings
from .docker_service import DockerService
from .redis_service import redis_service
from ..repositories.agent_repository import AgentRepository
from ..core.database import AsyncSessionLocal
from ..constants import (
    INITIAL_SOUL, INITIAL_IDENTITY, INITIAL_TOOLS,
    BUILDER_SOUL, BUILDER_IDENTITY, BUILDER_TOOLS,
    TESTER_SOUL, TESTER_IDENTITY, TESTER_TOOLS,
    REVIEWER_SOUL, REVIEWER_IDENTITY, REVIEWER_TOOLS,
    FIXER_SOUL, FIXER_IDENTITY, FIXER_TOOLS,
    ARCHITECT_SOUL, ARCHITECT_IDENTITY, ARCHITECT_TOOLS,
    RESEARCHER_SOUL, RESEARCHER_IDENTITY, RESEARCHER_TOOLS
)
from .hive_manager import HiveManager
import uuid
import shutil
import logging

logger = logging.getLogger(__name__)

class AgentManager:
    def __init__(self, docker_service: DockerService):
        self.docker = docker_service
        self.cache: Dict[str, Agent] = {}

    def _get_prompts_for_role(self, role: AgentRole) -> tuple[str, str, str]:
        """Return (soul_md, identity_md, tools_md) for the given role."""
        if role == AgentRole.BUILDER:
            return BUILDER_SOUL, BUILDER_IDENTITY, BUILDER_TOOLS
        elif role == AgentRole.TESTER:
            return TESTER_SOUL, TESTER_IDENTITY, TESTER_TOOLS
        elif role == AgentRole.REVIEWER:
            return REVIEWER_SOUL, REVIEWER_IDENTITY, REVIEWER_TOOLS
        elif role == AgentRole.FIXER:
            return FIXER_SOUL, FIXER_IDENTITY, FIXER_TOOLS
        elif role == AgentRole.ARCHITECT:
            return ARCHITECT_SOUL, ARCHITECT_IDENTITY, ARCHITECT_TOOLS
        elif role == AgentRole.RESEARCHER:
            return RESEARCHER_SOUL, RESEARCHER_IDENTITY, RESEARCHER_TOOLS
        else:  # GENERIC or unknown
            return INITIAL_SOUL, INITIAL_IDENTITY, INITIAL_TOOLS

    async def create_role_agent(
        self,
        name: str,
        role: AgentRole,
        reasoning: ReasoningConfig,
        reporting_target: ReportingTarget = ReportingTarget.PARENT,
        parent_id: Optional[str] = None,
        user_uid: Optional[str] = None,
        channels: List[ChannelConfig] = None
    ) -> Agent:
        """Create a new agent with the given role, using role‑specific prompts."""
        soul, identity, tools = self._get_prompts_for_role(role)
        agent_in = AgentCreate(
            name=name,
            role=role,
            soulMd=soul,
            identityMd=identity,
            toolsMd=tools,
            reasoning=reasoning,
            reporting_target=reporting_target,
            parent_id=parent_id,
            user_uid=user_uid,
            channels=channels or []
        )
        return await self.create_agent(agent_in)

    async def create_agent(self, agent_in: AgentCreate) -> Agent:
        agent_id = f"b-{uuid.uuid4().hex[:4]}"
        user_uid = agent_in.user_uid or settings.DEFAULT_AGENT_UID
        internal_api_key = settings.secrets.get("INTERNAL_API_KEY")
        if not internal_api_key:
            raise RuntimeError("Internal API key not configured")

        container_id = ""  # empty means no container by default

        agent_dir = settings.AGENTS_DIR / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        with open(agent_dir / "soul.md", "w") as f:
            f.write(agent_in.soul_md)
        with open(agent_dir / "identity.md", "w") as f:
            f.write(agent_in.identity_md)
        with open(agent_dir / "tools.md", "w") as f:
            f.write(agent_in.tools_md)

        files_dir = agent_dir / "files"
        files_dir.mkdir(exist_ok=True)

        agent = Agent(
            id=agent_id,
            name=agent_in.name,
            role=agent_in.role,
            soul_md=agent_in.soul_md,
            identity_md=agent_in.identity_md,
            tools_md=agent_in.tools_md,
            status=AgentStatus.IDLE,
            reasoning=agent_in.reasoning,
            reporting_target=agent_in.reporting_target,
            parent_id=agent_in.parent_id,
            sub_agent_ids=[],
            memory={"short_term": [], "summary": "", "token_count": 0},
            last_active=datetime.utcnow(),
            container_id=container_id,
            user_uid=user_uid,
            local_files=[],
            channels=agent_in.channels or [],
            skills=[],
            meta={}
        )

        repo, session = await self._get_repo()
        try:
            await repo.create(agent)
        finally:
            await session.close()

        self.cache[agent_id] = agent

        # Add to Redis idle set
        await redis_service.sadd("agents:idle", agent_id)
        logger.info(f"Agent {agent_id} added to Redis idle set")

        if agent.parent_id and agent.parent_id in self.cache:
            parent = self.cache[agent.parent_id]
            parent.sub_agent_ids.append(agent_id)
            await self.update_agent(parent.id, AgentUpdate(sub_agent_ids=parent.sub_agent_ids))

        channel_types = {ch.type for ch in agent.channels if ch.enabled}
        if channel_types:
            await self._publish_config_update(agent, channel_types)

        logger.info(f"Created bot {agent_id} with role {agent.role}")
        return agent

    # ... (keep all other methods unchanged)

    # --- NEW: Spawn agent for a task with role ---
    async def spawn_agent_for_task(self, hive_id: str, required_skill_ids: List[str], agent_type: str) -> Optional[Agent]:
        """Create a new agent with the required role and skills, and add it to the hive."""
        from .skill_manager import SkillManager
        skill_manager = SkillManager()

        # Convert agent_type string to AgentRole enum (default to GENERIC)
        try:
            role = AgentRole(agent_type)
        except ValueError:
            role = AgentRole.GENERIC

        # Get a reasonable reasoning config (could be improved)
        reasoning = ReasoningConfig(
            model="openai/gpt-4o",  # or use global default
            temperature=0.7,
            topP=1.0,
            maxTokens=150,
            use_global_default=True
        )

        # Create agent with role-specific prompts
        agent = await self.create_role_agent(
            name=f"{role.value.capitalize()} Bee",
            role=role,
            reasoning=reasoning,
            reporting_target=ReportingTarget.PARENT,
            parent_id=None,
            user_uid=settings.DEFAULT_AGENT_UID,
            channels=[]
        )

        # Install the required skills
        for skill_id in required_skill_ids:
            skill = await skill_manager.get_skill(skill_id)
            if not skill:
                continue
            # Get the latest active version
            versions = await skill_manager.list_versions(skill.id)
            active_versions = [v for v in versions if v.is_active]
            if active_versions:
                latest = max(active_versions, key=lambda v: v.created_at)
                await skill_manager.install_skill(agent.id, skill.id, latest.id, {})

        # Add agent to the hive
        hive_manager = HiveManager(self)
        await hive_manager.add_agent(hive_id, agent)

        logger.info(f"Spawned agent {agent.id} (role {role.value}) for hive {hive_id} with skills {required_skill_ids}")
        return agent
