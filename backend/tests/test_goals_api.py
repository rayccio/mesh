# backend/tests/test_goals_api.py
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app as fastapi_app
from app.models.types import HiveGoal, HiveGoalStatus, HiveTask, HiveTaskStatus, Hive, HiveMindConfig
from app.models.db_models import HiveModel
from app.utils.json_encoder import prepare_json_data
from datetime import datetime
import json

@pytest.mark.asyncio
async def test_create_goal_api(client: AsyncClient, session):
    # ---- Create a real hive in the test database ----
    from app.core.database import AsyncSessionLocal
    hive_id = "h-test"
    hive_data = Hive(
        id=hive_id,
        name="Test Hive",
        description="",
        agent_ids=[],
        global_user_md="context",
        messages=[],
        global_files=[],
        hive_mind_config=HiveMindConfig(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    async with AsyncSessionLocal() as db_session:
        serialized_data = prepare_json_data(hive_data.model_dump(by_alias=True))
        db_hive = HiveModel(id=hive_data.id, data=serialized_data)
        db_session.add(db_hive)
        await db_session.commit()
    # ---------------------------------------------------

    # Mock dependencies – we DO NOT mock the goal engine,
    # we want the real goal engine to insert the goal.
    mock_planner = AsyncMock()
    mock_task = HiveTask(
        id="t-test",
        goal_id="g-test",
        hive_id=hive_id,
        description="Task",
        agent_type="builder",
        status=HiveTaskStatus.PENDING,
        depends_on=[],
        required_skills=[],
        created_at=datetime.utcnow()
    )
    mock_planner.plan.return_value = [mock_task]

    mock_hive_manager = AsyncMock()
    mock_hive = MagicMock(spec=Hive)
    mock_hive.global_user_md = "context"
    mock_hive_manager.get_hive.return_value = mock_hive

    # Override only the planner and hive_manager, leave goal_engine real
    from app.api.v1.endpoints.goals import get_planner, get_hive_manager
    fastapi_app.dependency_overrides[get_planner] = lambda: mock_planner
    fastapi_app.dependency_overrides[get_hive_manager] = lambda: mock_hive_manager

    # Patch SkillManager
    with patch('app.services.skill_manager.SkillManager') as MockSkillManager:
        mock_skill_manager = AsyncMock()
        mock_skill_manager.list_skills = AsyncMock(return_value=[])
        MockSkillManager.return_value = mock_skill_manager

        payload = {
            "description": "Test goal",
            "constraints": {},
            "success_criteria": []
        }
        response = await client.post(f"/api/v1/hives/{hive_id}/goals", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["goal"]["id"].startswith("g-")
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == "t-test"

    fastapi_app.dependency_overrides.clear()
