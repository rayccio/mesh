import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from datetime import datetime
from app.api.v1.endpoints.plan import create_plan, GoalRequest
from app.models.task import Task, TaskStatus

@pytest.mark.asyncio
async def test_create_plan_with_scheduler_enabled():
    # Mock dependencies
    mock_task_manager = AsyncMock()
    mock_agent_manager = AsyncMock()
    mock_hive_manager = AsyncMock()
    mock_hive = MagicMock()
    mock_hive.global_user_md = "test context"
    mock_hive_manager.get_hive = AsyncMock(return_value=mock_hive)

    # Mock planner
    mock_planner = AsyncMock()
    mock_planner.plan.return_value = {
        "tasks": [
            {"id": "task1", "description": "Do something", "depends_on": []}
        ],
        "reasoning": "ok"
    }

    # Mock task graph creation
    mock_graph = MagicMock()
    mock_graph.goal_id = "g-test"
    mock_task_manager.create_task_graph.return_value = mock_graph

    # Mock redis_service
    mock_redis = AsyncMock()
    with patch('app.api.v1.endpoints.plan.redis_service', mock_redis), \
         patch('app.api.v1.endpoints.plan.settings', MagicMock(SCHEDULER_ENABLED=True)):

        # Call endpoint
        request = GoalRequest(goal="Test goal")
        result = await create_plan(
            hive_id="h-test",
            goal_req=request,
            task_manager=mock_task_manager,
            agent_manager=mock_agent_manager
        )

        # Verify redis zadd called for each task
        mock_redis.zadd.assert_called_once()
        # Since there's one task, we can check the call
        args = mock_redis.zadd.call_args[0]
        assert args[0] == "tasks:pending"
        # The task id is dynamic, so we just check it's a string and score is a float
        assert isinstance(list(args[1].keys())[0], str)
        assert isinstance(list(args[1].values())[0], float)

@pytest.mark.asyncio
async def test_create_plan_with_scheduler_disabled():
    # Same as above but with scheduler disabled
    mock_task_manager = AsyncMock()
    mock_agent_manager = AsyncMock()
    mock_hive_manager = AsyncMock()
    mock_hive = MagicMock()
    mock_hive.global_user_md = "test context"
    mock_hive_manager.get_hive = AsyncMock(return_value=mock_hive)

    mock_planner = AsyncMock()
    mock_planner.plan.return_value = {
        "tasks": [{"id": "task1", "description": "Do something", "depends_on": []}],
        "reasoning": "ok"
    }
    mock_graph = MagicMock()
    mock_graph.goal_id = "g-test"
    mock_task_manager.create_task_graph.return_value = mock_graph

    mock_redis = AsyncMock()
    with patch('app.api.v1.endpoints.plan.redis_service', mock_redis), \
         patch('app.api.v1.endpoints.plan.settings', MagicMock(SCHEDULER_ENABLED=False)):

        request = GoalRequest(goal="Test goal")
        result = await create_plan(
            hive_id="h-test",
            goal_req=request,
            task_manager=mock_task_manager,
            agent_manager=mock_agent_manager
        )

        # Verify redis not called
        mock_redis.zadd.assert_not_called()
