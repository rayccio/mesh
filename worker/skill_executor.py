import os
import asyncio
import logging
import httpx
import json
from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from container_manager import container_manager

logger = logging.getLogger(__name__)

# Database setup – reuse same config as worker
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "hivebot")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "hivebot")
POSTGRES_DB = os.getenv("POSTGRES_DB", "hivebot")
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


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
        if allowed_skills is not None and skill_name not in allowed_skills:
            logger.warning(f"Skill '{skill_name}' not allowed for this agent")
            return {"error": f"Skill '{skill_name}' is not in allowed skills list", "simulated": simulation}

        if simulation:
            return await self._call_simulator(skill_name, params)

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
            row = version_row.fetchone()
            if not row:
                logger.warning(f"No active version for skill '{skill_name}'")
                return {"error": f"No active version for skill '{skill_name}'"}

            version_id = row[0]
            skill_version = row[1]
            code = skill_version.get("code")
            language = skill_version.get("language", "python")

        if not code:
            return {"error": f"Skill '{skill_name}' has no code"}

        if language != "python":
            return {"error": f"Unsupported language for skill '{skill_name}': {language}"}

        try:
            result = await container_manager.run_skill_in_container(
                skill_code=code,
                input_data=params,
                config={},
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
        client = await self._get_http_client()
        url = f"{self.simulator_url}/mock/{skill_name}"
        try:
            resp = await client.post(url, json=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Simulator call failed: {e}")
            return {"error": str(e), "simulated": True}
