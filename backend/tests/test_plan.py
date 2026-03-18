import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from datetime import datetime
from app.api.v1.endpoints.plan import create_plan, GoalRequest
from app.models.types import HiveTask, HiveTaskStatus
from app.services.skill_manager import SkillManager
from app.services.skill_suggestion_manager import SkillSuggestionManager

@pytest.mark.asyncio
async def test_create_plan_with_scheduler_enabled():
    # Mock dependencies
    mock_task_manager = AsyncMock()
    mock_agent_manager = AsyncMock()
    mock_hive_manager = AsyncMock()
    mock_hive = MagicMock()
    mock_hive.global_user_md = "test context"
    mock_hive_manager.get_hive = AsyncMock(return_value=mock_hive)

    # Mock skill manager
    mock_skill_manager = AsyncMock(spec=SkillManager)
    mock_skill_manager.list_skills = AsyncMock(return_value=[])

    # Mock suggestion manager
    mock_suggestion_manager = AsyncMock(spec=SkillSuggestionManager)

    # Patch HiveManager inside the endpoint
    with patch('app.api.v1.endpoints.plan.HiveManager', return_value=mock_hive_manager):
        # Mock planner
        mock_planner = AsyncMock()
        # planner.plan now returns a list of HiveTask
        mock_task = HiveTask(
            id="t-test",
            goal_id="g-test",
            hive_id="h-test",
            description="Do something",
            agent_type="builder",
            status=HiveTaskStatus.PENDING,
            depends_on=[],
            required_skills=[],
            created_at=datetime.utcnow()
        )
        mock_planner.plan.return_value = [mock_task]

        with patch('app.api.v1.endpoints.plan.Planner', return_value=mock_planner):
            # Mock task graph creation
            mock_graph = {"goal_id": "g-test", "tasks": [mock_task]}
            mock_task_manager.create_task_graph.return_value = mock_graph

            # Patch redis zadd and the settings object inside the plan module
            mock_settings = MagicMock()
            mock_settings.SCHEDULER_ENABLED = True
            with patch('app.services.redis_service.redis_service.zadd', new_callable=AsyncMock) as mock_zadd, \
                 patch('app.api.v1.endpoints.plan.settings', mock_settings):

                request = GoalRequest(goal="Test goal")
                result = await create_plan(
                    hive_id="h-test",
                    goal_req=request,
                    task_manager=mock_task_manager,
                    agent_manager=mock_agent_manager,
                    skill_manager=mock_skill_manager,
                    suggestion_manager=mock_suggestion_manager
                )

                # Verify zadd was called once with correct key and member
                mock_zadd.assert_awaited_once()
                args = mock_zadd.call_args[0]
                assert args[0] == "tasks:pending"      # key
                assert isinstance(args[1], str)        # member (task id)
                assert isinstance(args[2], float)      # score

@pytest.mark.asyncio
async def test_create_plan_with_scheduler_disabled():
    mock_task_manager = AsyncMock()
    mock_agent_manager = AsyncMock()
    mock_hive_manager = AsyncMock()
    mock_hive = MagicMock()
    mock_hive.global_user_md = "test context"
    mock_hive_manager.get_hive = AsyncMock(return_value=mock_hive)

    mock_skill_manager = AsyncMock(spec=SkillManager)
    mock_skill_manager.list_skills = AsyncMock(return_value=[])

    mock_suggestion_manager = AsyncMock(spec=SkillSuggestionManager)

    with patch('app.api.v1.endpoints.plan.HiveManager', return_value=mock_hive_manager):
        mock_planner = AsyncMock()
        mock_task = HiveTask(
            id="t-test",
            goal_id="g-test",
            hive_id="h-test",
            description="Do something",
            agent_type="builder",
            status=HiveTaskStatus.PENDING,
            depends_on=[],
            required_skills=[],
            created_at=datetime.utcnow()
        )
        mock_planner.plan.return_value = [mock_task]

        with patch('app.api.v1.endpoints.plan.Planner', return_value=mock_planner):
            mock_graph = {"goal_id": "g-test", "tasks": [mock_task]}
            mock_task_manager.create_task_graph.return_value = mock_graph

            mock_settings = MagicMock()
            mock_settings.SCHEDULER_ENABLED = False
            with patch('app.services.redis_service.redis_service.zadd', new_callable=AsyncMock) as mock_zadd, \
                 patch('app.api.v1.endpoints.plan.settings', mock_settings):

                request = GoalRequest(goal="Test goal")
                result = await create_plan(
                    hive_id="h-test",
                    goal_req=request,
                    task_manager=mock_task_manager,
                    agent_manager=mock_agent_manager,
                    skill_manager=mock_skill_manager,
                    suggestion_manager=mock_suggestion_manager
                )

                mock_zadd.assert_not_called()
