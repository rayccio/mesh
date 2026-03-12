import json
import os
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.types import Hive, HiveCreate, HiveUpdate, Agent, Message, FileEntry
from ..models.task import TaskStatus
from ..core.config import settings
from ..core.database import AsyncSessionLocal
from ..repositories.hive_repository import HiveRepository
from ..repositories.agent_repository import AgentRepository
from .task_manager import TaskManager
import uuid
import shutil
import logging

logger = logging.getLogger(__name__)

class HiveManager:
    def __init__(self, agent_manager):  # agent_manager is AgentManager instance
        self.agent_manager = agent_manager
        self.repo = HiveRepository

    async def _get_session_and_repo(self):
        session = AsyncSessionLocal()
        return HiveRepository(session), session

    async def _get_agent_repo(self, session: AsyncSession):
        return AgentRepository(session)

    async def create_hive(self, hive_in: HiveCreate) -> Hive:
        hive_id = f"h-{uuid.uuid4().hex[:4]}"
        hive_dir = settings.AGENTS_DIR / hive_id
        hive_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.utcnow()
        # Store only agent_ids in the JSON
        hive_data = {
            "id": hive_id,
            "name": hive_in.name,
            "description": hive_in.description,
            "agent_ids": [],  # will be populated later
            "global_user_md": hive_in.global_user_md,
            "messages": [],
            "global_files": [],
            "hive_mind_config": {"access_level": "ISOLATED", "shared_hive_ids": []},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        hive = Hive(**hive_data)  # this will set agents=[], but we'll override later
        repo, session = await self._get_session_and_repo()
        try:
            created = await repo.create(hive)
        finally:
            await session.close()
        logger.info(f"Created hive {hive_id}")
        return created

    async def get_hive(self, hive_id: str) -> Optional[Hive]:
        repo, session = await self._get_session_and_repo()
        try:
            hive = await repo.get(hive_id)
            if not hive:
                return None
            # Fetch agents from agent_ids
            agent_ids = hive.dict().get("agent_ids", [])
            agents = []
            if agent_ids:
                agent_repo = await self._get_agent_repo(session)
                for aid in agent_ids:
                    agent = await agent_repo.get(aid)
                    if agent:
                        agents.append(agent)
            # Replace agent_ids with full agents list in the returned Hive object
            hive.agents = agents
            return hive
        finally:
            await session.close()

    async def list_hives(self) -> List[Hive]:
        repo, session = await self._get_session_and_repo()
        try:
            hives = await repo.get_all()
            agent_repo = await self._get_agent_repo(session)
            for hive in hives:
                agent_ids = hive.dict().get("agent_ids", [])
                agents = []
                for aid in agent_ids:
                    agent = await agent_repo.get(aid)
                    if agent:
                        agents.append(agent)
                hive.agents = agents
            return hives
        finally:
            await session.close()

    async def update_hive(self, hive_id: str, hive_update: HiveUpdate) -> Optional[Hive]:
        repo, session = await self._get_session_and_repo()
        try:
            # Convert update to dict
            update_data = hive_update.dict(exclude_unset=True)
            # If agents are updated, we need to handle agent_ids
            if "agents" in update_data:
                # We assume the update includes a list of full Agent objects; we store only their IDs
                agent_ids = [a.id for a in update_data["agents"]]
                update_data["agent_ids"] = agent_ids
                del update_data["agents"]  # don't store full objects
            # For other fields, they map directly
            hive = await repo.get(hive_id)
            if not hive:
                return None
            # Update the hive data
            current_data = hive.dict()
            current_data.update(update_data)
            current_data["updated_at"] = datetime.utcnow().isoformat()
            updated_hive = Hive(**current_data)
            await repo.update(hive_id, updated_hive.dict(by_alias=True))
            # Return with agents populated
            return await self.get_hive(hive_id)
        finally:
            await session.close()

    async def delete_hive(self, hive_id: str) -> bool:
        repo, session = await self._get_session_and_repo()
        try:
            deleted = await repo.delete(hive_id)
            if deleted:
                hive_dir = settings.AGENTS_DIR / hive_id
                if hive_dir.exists():
                    shutil.rmtree(hive_dir, ignore_errors=True)
            return deleted
        finally:
            await session.close()

    async def add_agent(self, hive_id: str, agent: Agent) -> Optional[Hive]:
        repo, session = await self._get_session_and_repo()
        try:
            hive = await repo.get(hive_id)
            if not hive:
                return None
            # Get current agent_ids
            agent_ids = hive.dict().get("agent_ids", [])
            if agent.id not in agent_ids:
                agent_ids.append(agent.id)
                # Update the hive data
                current_data = hive.dict()
                current_data["agent_ids"] = agent_ids
                current_data["updated_at"] = datetime.utcnow().isoformat()
                updated_hive = Hive(**current_data)
                await repo.update(hive_id, updated_hive.dict(by_alias=True))
            # Return with agents populated
            return await self.get_hive(hive_id)
        finally:
            await session.close()

    async def remove_agent(self, hive_id: str, agent_id: str) -> Optional[Hive]:
        repo, session = await self._get_session_and_repo()
        try:
            hive = await repo.get(hive_id)
            if not hive:
                return None
            agent_ids = hive.dict().get("agent_ids", [])
            if agent_id in agent_ids:
                agent_ids.remove(agent_id)
                current_data = hive.dict()
                current_data["agent_ids"] = agent_ids
                current_data["updated_at"] = datetime.utcnow().isoformat()
                updated_hive = Hive(**current_data)
                await repo.update(hive_id, updated_hive.dict(by_alias=True))
            return await self.get_hive(hive_id)
        finally:
            await session.close()

    # For messages and global files, we similarly store them as lists of objects in the hive JSON
    # Since they are small, we can keep them as full objects (no separate tables)
    async def add_message(self, hive_id: str, message: Message) -> Optional[Hive]:
        repo, session = await self._get_session_and_repo()
        try:
            hive = await repo.get(hive_id)
            if not hive:
                return None
            messages = hive.dict().get("messages", [])
            messages.append(message.dict())
            # Keep only last 100
            if len(messages) > 100:
                messages = messages[-100:]
            current_data = hive.dict()
            current_data["messages"] = messages
            current_data["updated_at"] = datetime.utcnow().isoformat()
            updated_hive = Hive(**current_data)
            await repo.update(hive_id, updated_hive.dict(by_alias=True))
            return await self.get_hive(hive_id)
        finally:
            await session.close()

    async def add_global_file(self, hive_id: str, file_entry: FileEntry) -> Optional[Hive]:
        repo, session = await self._get_session_and_repo()
        try:
            hive = await repo.get(hive_id)
            if not hive:
                return None
            files = hive.dict().get("global_files", [])
            files.append(file_entry.dict())
            current_data = hive.dict()
            current_data["global_files"] = files
            current_data["updated_at"] = datetime.utcnow().isoformat()
            updated_hive = Hive(**current_data)
            await repo.update(hive_id, updated_hive.dict(by_alias=True))
            return await self.get_hive(hive_id)
        finally:
            await session.close()

    async def remove_global_file(self, hive_id: str, file_id: str) -> Optional[Hive]:
        repo, session = await self._get_session_and_repo()
        try:
            hive = await repo.get(hive_id)
            if not hive:
                return None
            files = hive.dict().get("global_files", [])
            files = [f for f in files if f.get("id") != file_id]
            current_data = hive.dict()
            current_data["global_files"] = files
            current_data["updated_at"] = datetime.utcnow().isoformat()
            updated_hive = Hive(**current_data)
            await repo.update(hive_id, updated_hive.dict(by_alias=True))
            return await self.get_hive(hive_id)
        finally:
            await session.close()

    # --- NEW: Get agents currently executing tasks for this hive ---
    async def get_active_agents(self, hive_id: str) -> List[Agent]:
        """Return agents currently executing tasks for this hive."""
        task_manager = TaskManager()
        tasks = await task_manager.list_tasks_for_hive(hive_id)
        active_agent_ids = set()
        for t in tasks:
            if t.status in (TaskStatus.ASSIGNED, TaskStatus.RUNNING) and t.assigned_agent_id:
                active_agent_ids.add(t.assigned_agent_id)
        agents = []
        for aid in active_agent_ids:
            agent = await self.agent_manager.get_agent(aid)
            if agent:
                agents.append(agent)
        return agents
