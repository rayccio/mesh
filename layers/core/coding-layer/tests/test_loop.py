import pytest
from unittest.mock import AsyncMock, patch
from loop import CodingLoopHandler


@pytest.mark.asyncio
async def test_loop_handler_success_first_try():
    handler = CodingLoopHandler()

    # Mock call_ai_delta to return a successful code and test result
    async def mock_call_ai_delta(agent_id, user_input, model_config, system_prompt_override=None, retries=1):
        if "Generate the code" in user_input:
            return "def test_func(): return True"
        elif "Write and run tests" in user_input:
            return '{"passed": true, "errors": []}'
        elif "Review the code" in user_input:
            return '{"issues": [], "approved": true}'
        else:
            return ""

    mock_save_artifact = AsyncMock()
    mock_update_artifact_status = AsyncMock()
    mock_skill_executor = AsyncMock()

    result = await handler.run(
        agent_id="test_agent",
        task_id="test_task",
        description="Write a function that returns True",
        input_data={},
        goal_id="g-test",
        hive_id="h-test",
        project_id=None,
        skill_executor=mock_skill_executor,
        call_ai_delta=mock_call_ai_delta,
        save_artifact=mock_save_artifact,
        update_artifact_status=mock_update_artifact_status,
        layer_id="coding"
    )

    assert result["success"] is True
    assert result["iterations"] == 1
    # Ensure artifacts were saved
    assert mock_save_artifact.call_count >= 3  # code, test_result, review, final (actually 4)
    mock_update_artifact_status.assert_called()


@pytest.mark.asyncio
async def test_loop_handler_failure_then_fix():
    handler = CodingLoopHandler()
    handler.MAX_ITERATIONS = 2

    call_count = 0

    async def mock_call_ai_delta(agent_id, user_input, model_config, system_prompt_override=None, retries=1):
        nonlocal call_count
        call_count += 1
        if "Generate the code" in user_input:
            if call_count == 1:
                return "def test_func(): return False"
            elif call_count == 4:   # fixer
                return "def test_func(): return True"
            elif call_count == 5:   # second builder
                return "def test_func(): return True"
            else:
                return "def test_func(): return True"
        elif "Write and run tests" in user_input:
            if call_count == 2:
                return '{"passed": false, "errors": ["Expected True"]}'
            elif call_count == 6:
                return '{"passed": true, "errors": []}'
            else:
                return '{"passed": true, "errors": []}'
        elif "List the issues" in user_input:
            return "The function returns False instead of True"
        elif "Review the code" in user_input:
            return '{"issues": [], "approved": true}'
        else:
            return ""

    mock_save_artifact = AsyncMock()
    mock_update_artifact_status = AsyncMock()
    mock_skill_executor = AsyncMock()

    result = await handler.run(
        agent_id="test_agent",
        task_id="test_task",
        description="Write a function that returns True",
        input_data={},
        goal_id="g-test",
        hive_id="h-test",
        project_id=None,
        skill_executor=mock_skill_executor,
        call_ai_delta=mock_call_ai_delta,
        save_artifact=mock_save_artifact,
        update_artifact_status=mock_update_artifact_status,
        layer_id="coding"
    )

    assert result["success"] is True
    assert result["iterations"] == 2
    # Ensure artifacts were saved for both iterations
    assert mock_save_artifact.call_count >= 7   # code1, test1, issues, fixed1, code2, test2, final
    mock_update_artifact_status.assert_called()
