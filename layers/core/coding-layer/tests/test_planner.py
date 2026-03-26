import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from planner.planner import CodingPlanner
from app.models.types import HiveTask, HiveTaskStatus
from datetime import datetime


@pytest.mark.asyncio
async def test_planner_decomposes_goal():
    planner = CodingPlanner()

    # Mock generate_with_messages to return a predefined decomposition
    mock_response = {
        "tasks": [
            {
                "id": "task_1",
                "description": "Design frontend layout",
                "agent_type": "frontend-developer",
                "depends_on": [],
                "required_skills": ["html_builder", "css_styling"]
            },
            {
                "id": "task_2",
                "description": "Build backend API",
                "agent_type": "backend-developer",
                "depends_on": [],
                "required_skills": ["rest_api"]
            }
        ],
        "reasoning": "test"
    }

    with patch('planner.planner.generate_with_messages', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = json.dumps(mock_response)

        skills = [
            {"id": "sk-1", "name": "html_builder", "description": ""},
            {"id": "sk-2", "name": "css_styling", "description": ""},
            {"id": "sk-3", "name": "rest_api", "description": ""}
        ]
        roles = ["frontend-developer", "backend-developer"]

        tasks = await planner.plan(
            goal_text="Build a web app",
            skills=skills,
            roles=roles
        )

        assert len(tasks) == 2
        assert tasks[0].description == "Design frontend layout"
        assert tasks[0].agent_type == "frontend-developer"
        assert tasks[0].required_skills == ["sk-1", "sk-2"]
        assert tasks[0].loop_handler == "coding_loop"
        assert tasks[0].sandbox_level == "task"
        assert tasks[1].description == "Build backend API"
        assert tasks[1].agent_type == "backend-developer"
        assert tasks[1].required_skills == ["sk-3"]

        # Check that dependencies are resolved correctly
        assert tasks[0].depends_on == []
        assert tasks[1].depends_on == []


@pytest.mark.asyncio
async def test_planner_fallback_on_failure():
    planner = CodingPlanner()

    with patch('planner.planner.generate_with_messages', new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = Exception("API error")

        tasks = await planner.plan(
            goal_text="Build a web app",
            skills=[],
            roles=[]
        )

        assert len(tasks) == 1
        assert tasks[0].description == "Build a web app"
        assert tasks[0].agent_type == "builder"
        assert tasks[0].required_skills == []
        assert tasks[0].loop_handler == "coding_loop"
        assert tasks[0].sandbox_level == "task"
