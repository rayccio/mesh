# backend/app/api/v1/endpoints/plan.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from pydantic import BaseModel
from ....services.task_manager import TaskManager
from ....services.planner import Planner
from ....services.agent_manager import AgentManager
from ....services.docker_service import DockerService
from ....services.redis_service import redis_service
from ....services.skill_manager import SkillManager
from ....services.skill_suggestion_manager import SkillSuggestionManager
from ....models.skill import SkillSuggestionCreate
from ....models.types import HiveTask, HiveTaskStatus
from ....services.hive_manager import HiveManager
from ....core.config import settings
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hives/{hive_id}/plan", tags=["planning"])

class GoalRequest(BaseModel):
    goal: str
    auto_spawn: bool = True

async def get_task_manager():
    return TaskManager()

async def get_agent_manager():
    docker_service = DockerService()
    return AgentManager(docker_service)

async def get_skill_manager():
    return SkillManager()

async def get_suggestion_manager():
    return SkillSuggestionManager()

@router.post("")
async def create_plan(
    hive_id: str,
    goal_req: GoalRequest,
    task_manager: TaskManager = Depends(get_task_manager),
    agent_manager: AgentManager = Depends(get_agent_manager),
    skill_manager: SkillManager = Depends(get_skill_manager),
    suggestion_manager: SkillSuggestionManager = Depends(get_suggestion_manager)
):
    """Decompose a goal into a task graph and optionally execute immediately."""
    goal_text = goal_req.goal
    if not goal_text:
        raise HTTPException(status_code=400, detail="Goal text required")

    # Get hive context
    hive_manager = HiveManager(agent_manager)
    hive = await hive_manager.get_hive(hive_id)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive not found")
    context = hive.global_user_md

    # Fetch all skills
    all_skills = await skill_manager.list_skills()
    skills_list = [{"id": s.id, "name": s.name, "description": s.description} for s in all_skills]

    # Build name->id mapping for skills
    skill_map = {s["name"].lower(): s["id"] for s in skills_list}

    planner = Planner()
    goal_id = f"g-{uuid.uuid4().hex[:8]}"
    try:
        tasks = await planner.plan(
            goal_id=goal_id,
            hive_id=hive_id,
            goal_text=goal_text,
            hive_context=context,
            skills=skills_list
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning failed: {e}")

    # Collect missing skills for suggestions
    missing_skill_tasks = []
    for task in tasks:
        req_skill_names = task.required_skills  # these are names, not IDs
        missing_names = [name for name in req_skill_names if name.lower() not in skill_map]
        if missing_names:
            missing_skill_tasks.append({
                "real_id": task.id,
                "task_dict": {"description": task.description},
                "missing_names": missing_names
            })

    # Create skill suggestions for missing skills
    for item in missing_skill_tasks:
        for name in item["missing_names"]:
            suggestion_in = SkillSuggestionCreate(
                skill_name=name,
                goal_id=goal_id,
                goal_description=goal_text,
                task_id=item["real_id"],
                task_description=item["task_dict"]["description"],
                suggested_by="planner"
            )
            await suggestion_manager.create_suggestion(suggestion_in)

    # --- Immediate execution logic ---
    if settings.SCHEDULER_ENABLED:
        # Push only tasks with empty depends_on to Redis pending queue
        for task in tasks:
            if not task.depends_on:
                score = task.created_at.timestamp() * 1000
                await redis_service.zadd("tasks:pending", task.id, score)
        logger.info(f"Pushed {len([t for t in tasks if not t.depends_on])} tasks to Redis pending queue")

        # If auto_spawn is enabled, check for idle agents and assign immediately
        if goal_req.auto_spawn:
            # Get idle agents from Redis
            idle_agents = await redis_service.smembers("agents:idle")
            if not idle_agents:
                # No idle agents – spawn new ones based on task requirements
                logger.info("No idle agents, spawning new agents for tasks")
                # Collect unique required skills across all tasks
                all_required_skill_ids = set()
                for task in tasks:
                    for name in task.required_skills:
                        sid = skill_map.get(name.lower())
                        if sid:
                            all_required_skill_ids.add(sid)
                # For each task, spawn an agent (simplified)
                spawned_agents = []
                for task in tasks:
                    agent = await agent_manager.spawn_agent_for_task(hive_id, list(all_required_skill_ids), task.agent_type)
                    if agent:
                        spawned_agents.append(agent.id)
                        await redis_service.sadd("agents:idle", agent.id)
                logger.info(f"Spawned {len(spawned_agents)} new agents")

    return {"goal_id": goal_id, "tasks": tasks, "edges": []}
