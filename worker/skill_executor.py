import os
import asyncio
import logging
import httpx
import json
from typing import Dict, Any, Optional, List

from .container_manager import container_manager
from .skill_manager import SkillManager  # we'll need to import this; but it's in backend, not worker.
# Since we can't import from backend directly in worker, we'll make an HTTP call to fetch skill version.
# We'll use the orchestrator API to get the skill version.
# Alternatively, we can have a local skill manager that queries the DB. But the worker already has DB access.
# So we'll use the DB directly.

from sqlalchemy import text
from ..backend.core.database import AsyncSessionLocal  # we need to import from backend; careful with paths.
# But in the worker, the path is different. We'll need to adjust. For now, we'll assume we can import from backend.
# However, to keep things simple, we'll use the existing `skill_manager.py` from backend, but that's not in the worker's PYTHONPATH.
# A better approach: create a simple function in worker to fetch skill version by ID using the DB session.

# We'll add a helper function to fetch skill version from DB.

async def fetch_skill_version(version_id: str) -> Optional[Dict[str, Any]]:
    """Fetch skill version data from the database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT data FROM skill_versions WHERE id = :id"),
            {"id": version_id}
        )
        row = result.fetchone()
        if row:
            return row[0]
    return None

logger = logging.getLogger(__name__)


class SkillExecutor:
    def __init__(self, simulator_url: str = "http://simulator:8080"):
        self.simulator_url = simulator_url
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def execute(
        self,
        skill_name: str,
        params: Dict[str, Any],
        simulation: bool = False,
        allowed_skills: Optional[List[str]] = None,
        sandbox_level: str = "skill",
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a skill, checking permissions first.
        """
        # Permission check
        if allowed_skills is not None and skill_name not in allowed_skills:
            logger.warning(f"Skill '{skill_name}' not allowed for this agent")
            return {"error": f"Skill '{skill_name}' is not in allowed skills list", "simulated": simulation}

        if simulation:
            return await self._call_simulator(skill_name, params)

        # Fetch the skill by name (we need to get the active version).
        # We'll use the SkillManager from backend? For now, we'll make a DB query.
        # We need to map skill name to skill ID, then get the active version.
        # We'll do a simple DB query.

        async with AsyncSessionLocal() as session:
            # Get skill ID by name
            skill_row = await session.execute(
                text("SELECT id FROM skills WHERE data->>'name' = :name"),
                {"name": skill_name}
            )
            skill_id = skill_row.scalar()
            if not skill_id:
                logger.warning(f"Skill '{skill_name}' not found in database")
                return {"error": f"Skill '{skill_name}' not found"}

            # Get active version
            version_row = await session.execute(
                text("""
                    SELECT id, data FROM skill_versions
                    WHERE skill_id = :skill_id AND (data->>'is_active')::bool = TRUE
                    ORDER BY (data->>'created_at')::timestamptz DESC
                    LIMIT 1
                """),
                {"skill_id": skill_id}
            )
            version_data = version_row.fetchone()
            if not version_row:
                logger.warning(f"No active version for skill '{skill_name}'")
                return {"error": f"No active version for skill '{skill_name}'"}

            version_id = version_data[0]
            skill_version = version_data[1]
            code = skill_version.get("code")
            language = skill_version.get("language", "python")
            entry_point = skill_version.get("entry_point", "run")
            requirements = skill_version.get("requirements", [])

        if not code:
            return {"error": f"Skill '{skill_name}' has no code"}

        # For now, we only support Python
        if language != "python":
            return {"error": f"Unsupported language for skill '{skill_name}': {language}"}

        # Execute the code in the appropriate sandbox
        try:
            result = await container_manager.run_skill_in_container(
                skill_code=code,
                input_data=params,
                config={},  # we don't have a config yet
                sandbox_level=sandbox_level,
                task_id=task_id,
                project_id=project_id,
                agent_id=agent_id,
            )
            return result
        except Exception as e:
            logger.exception(f"Skill execution failed: {e}")
            return {"error": str(e), "simulated": False}

    async def _call_simulator(self, skill_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Forward call to simulator service."""
        client = await self._get_http_client()
        url = f"{self.simulator_url}/mock/{skill_name}"
        try:
            resp = await client.post(url, json=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Simulator call failed: {e}")
            return {"error": str(e), "simulated": True}
