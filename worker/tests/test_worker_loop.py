import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime
import sys
sys.path.append('..')
from worker.main import execute_task_with_loop, process_task_assign

@pytest.mark.asyncio
async def test_execute_task_with_loop_success_first_try():
    agent_id = "b-test"
    task_id = "t-test"
    description = "Write a function that returns True"
    input_data = {}
    goal_id = "g-test"
    hive_id = "h-test"
    agent_data = {"reasoning": {"model": "openai/gpt-4o"}}

    with patch('worker.main.call_ai_delta', new_callable=AsyncMock) as mock_call, \
         patch('worker.main.save_artifact', new_callable=AsyncMock) as mock_save:

        # Builder returns code, tester passes
        mock_call.side_effect = [
            "def test_func(): return True",  # builder
            '{"passed": true, "errors": []}'  # tester
        ]

        success, iterations = await execute_task_with_loop(
            agent_id, task_id, description, input_data, goal_id, hive_id, agent_data
        )

        assert success is True
        assert iterations == 1
        assert mock_call.call_count == 2
        # In success path: save code (builder), save test result (tester), save final (final) = 3
        assert mock_save.call_count == 3

@pytest.mark.asyncio
async def test_execute_task_with_loop_failure_then_fix():
    agent_id = "b-test"
    task_id = "t-test"
    description = "Write a function that returns True"
    input_data = {}
    goal_id = "g-test"
    hive_id = "h-test"
    agent_data = {"reasoning": {"model": "openai/gpt-4o"}}

    with patch('worker.main.call_ai_delta', new_callable=AsyncMock) as mock_call, \
         patch('worker.main.save_artifact', new_callable=AsyncMock) as mock_save:

        # Simulate: builder (1), tester fails (2), reviewer (3), fixer (4), tester passes (5)
        # But the loop will also save final code after pass = 6 AI calls? Wait, after fixer, the next iteration runs tester, which passes, then loop exits after saving final.
        # Actually the loop structure: for iteration in range(MAX_ITER):
        #   builder
        #   tester
        #   if passed: save final and return
        #   reviewer
        #   fixer
        # So on success after fixer, the loop will go to next iteration? No, it checks after tester each iteration. So if tester passes in iteration 2, it saves final and returns. So total AI calls: iteration1: builder, tester, reviewer, fixer = 4; iteration2: builder? Wait, after fixer, the loop goes to next iteration, starting with builder again (using fixed code). So that's another builder, then tester. So total AI calls = 6 (builder1, tester1, reviewer, fixer, builder2, tester2). And saves: iteration1: code, test, issues, fixed = 4; iteration2: code (builder2), test (tester2), final = 3; total 7 saves.
        # But the test's mock_call side effect has 5 values, which is insufficient. We need to provide enough for the actual number of calls.
        # To keep test simple, we'll set MAX_ITERATIONS=2 in the test by patching the constant, and provide exactly 6 AI calls.
        # However, patching constants in another module is tricky. Instead, we'll set the side effect to a list of 6 values.
        with patch('worker.main.MAX_ITERATIONS', 2):
            mock_call.side_effect = [
                "def test_func(): return False",      # builder1
                '{"passed": false, "errors": ["Expected True got False"]}',  # tester1
                "The function returns False instead of True",  # reviewer
                "def test_func(): return True",       # fixer
                "def test_func(): return True",       # builder2 (unused? Actually builder2 will be called at start of iteration2, even though code is already fixed)
                '{"passed": true, "errors": []}'      # tester2
            ]

            success, iterations = await execute_task_with_loop(
                agent_id, task_id, description, input_data, goal_id, hive_id, agent_data
            )

            assert success is True
            assert iterations == 2
            # Expected AI calls: 6 (as above)
            assert mock_call.call_count == 6
            # Expected saves: iteration1: code, test, issues, fixed = 4; iteration2: code (builder2), test, final = 3; total 7
            assert mock_save.call_count == 7

@pytest.mark.asyncio
async def test_process_task_assign_integration():
    agent_id = "b-test"
    task_id = "t-test"
    description = "Write a function"
    input_data = {}
    goal_id = "g-test"
    hive_id = "h-test"

    # Provide complete agent_data with memory structure
    agent_data = {
        "status": "IDLE",
        "memory": {"shortTerm": [], "summary": "", "tokenCount": 0}
    }

    with patch('worker.main.get_agent_from_db', new_callable=AsyncMock) as mock_get, \
         patch('worker.main.update_agent_state', new_callable=AsyncMock) as mock_update, \
         patch('worker.main.execute_task_with_loop', new_callable=AsyncMock) as mock_loop, \
         patch('worker.main.register_agent_idle', new_callable=AsyncMock) as mock_register, \
         patch('worker.main.redis.from_url', new_callable=AsyncMock) as mock_redis:

        mock_get.return_value = agent_data
        mock_loop.return_value = (True, 2)

        mock_redis_client = AsyncMock()
        mock_redis_client.publish = AsyncMock()
        mock_redis_client.close = AsyncMock()
        mock_redis.return_value.__aenter__.return_value = mock_redis_client

        await process_task_assign(agent_id, task_id, description, input_data, goal_id, hive_id, simulation=False)

        mock_loop.assert_awaited_once_with(
            agent_id, task_id, description, input_data, goal_id, hive_id, agent_data
        )
        # update_agent_state called at least twice (start and end)
        assert mock_update.await_count >= 2
        mock_register.assert_awaited_once_with(agent_id)
        mock_redis_client.publish.assert_awaited_once()
