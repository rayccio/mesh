import pytest
from app.services.planner import Planner
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_plan():
    planner = Planner()
    # Mock the provider config and AI call
    with patch('app.services.planner.settings.secrets.get', return_value={"providers": {"openai": {"models": {"gpt-4o": {"is_primary": True, "enabled": True}}}}}) as mock_secrets, \
         patch('app.services.planner.generate_with_messages', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = '{"tasks": [{"id": "task_1", "description": "Do something", "depends_on": []}], "reasoning": "ok"}'
        result = await planner.plan("Test goal")
        assert "tasks" in result
        assert len(result["tasks"]) == 1
