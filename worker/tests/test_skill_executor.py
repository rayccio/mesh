import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from skill_executor import SkillExecutor

@pytest.mark.asyncio
async def test_skill_executor_permission_check():
    executor = SkillExecutor()
    result = await executor.execute(
        skill_name="web_search",
        params={"query": "test"},
        simulation=False,
        allowed_skills=["web_search"]
    )
    # In a real test, we mock the DB and skill execution
    # We'll just check that the permission check passed.
    # Actually, because the skill is allowed, it will try to fetch the skill version.
    # We need to mock that.
    # Let's mock the DB call to return a dummy skill.
    with patch('skill_executor.AsyncSessionLocal') as mock_session:
        mock_conn = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_conn

        # Mock the skill query result
        mock_skill_row = MagicMock()
        mock_skill_row.scalar.return_value = "sk-123"
        mock_conn.execute.return_value = mock_skill_row

        # Mock the version query result
        mock_version_row = MagicMock()
        mock_version_row.fetchone.return_value = ("sv-123", {"code": "def run(input, config): return {'result': 'ok'}", "language": "python"})
        mock_conn.execute.return_value = mock_version_row

        # Mock container_manager.run_skill_in_container
        with patch('skill_executor.container_manager.run_skill_in_container', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"result": "ok"}
            result = await executor.execute(
                skill_name="web_search",
                params={"query": "test"},
                simulation=False,
                allowed_skills=["web_search"]
            )
            assert "error" not in result
            mock_run.assert_awaited_once()

    # Test disallowed skill
    result = await executor.execute(
        skill_name="web_search",
        params={"query": "test"},
        simulation=False,
        allowed_skills=["run_code"]
    )
    assert "error" in result
    assert "not in allowed skills list" in result["error"]

@pytest.mark.asyncio
async def test_skill_executor_simulation():
    executor = SkillExecutor()
    with patch.object(executor, '_call_simulator', new_callable=AsyncMock) as mock_sim:
        mock_sim.return_value = {"simulated": True}
        result = await executor.execute(
            skill_name="web_search",
            params={"query": "test"},
            simulation=True,
            allowed_skills=["web_search"]
        )
        assert result == {"simulated": True}
        mock_sim.assert_awaited_once_with("web_search", {"query": "test"})
