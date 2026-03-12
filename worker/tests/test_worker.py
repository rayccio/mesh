import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime
import sys
sys.path.append('..')
from worker.main import (
    process_think_command,
    process_task_assign,
    register_agent_idle,
)

@pytest.mark.asyncio
async def test_register_agent_idle():
    mock_redis = AsyncMock()
    with patch('worker.main.redis.from_url', return_value=mock_redis):
        await register_agent_idle("agent1")
        mock_redis.sadd.assert_awaited_once_with("agents:idle", "agent1")
        mock_redis.close.assert_awaited_once()

@pytest.mark.asyncio
async def test_process_think_command_registers_idle():
    # Mock DB get and update
    mock_get_agent = AsyncMock(return_value={
        'status': 'RUNNING',
        'memory': {},
        'reportingTarget': 'OWNER_DIRECT',
        'parentId': None
    })
    mock_update = AsyncMock()
    mock_call_ai = AsyncMock(return_value="AI response")
    mock_redis_pub = AsyncMock()
    mock_redis_client = AsyncMock()
    mock_redis_client.publish = mock_redis_pub
    mock_redis_client.close = AsyncMock()

    with patch('worker.main.get_agent_from_db', mock_get_agent), \
         patch('worker.main.update_agent_state', mock_update), \
         patch('worker.main.call_ai_delta', mock_call_ai), \
         patch('worker.main.redis.from_url', return_value=mock_redis_client), \
         patch('worker.main.register_agent_idle', AsyncMock()) as mock_register:

        await process_think_command("agent1", "user input", {}, simulation=False)

        # Verify register_agent_idle called after status set to IDLE
        # In our code, register_agent_idle is called after update_agent_state to IDLE
        mock_register.assert_awaited_once_with("agent1")

@pytest.mark.asyncio
async def test_process_task_assign_registers_idle():
    mock_get_agent = AsyncMock(return_value={
        'status': 'RUNNING',
        'memory': {},
        'identityMd': '',
        'soulMd': '',
        'toolsMd': ''
    })
    mock_update = AsyncMock()
    mock_call_ai = AsyncMock(return_value="AI output")
    mock_redis_pub = AsyncMock()
    mock_redis_client = AsyncMock()
    mock_redis_client.publish = mock_redis_pub
    mock_redis_client.close = AsyncMock()

    with patch('worker.main.get_agent_from_db', mock_get_agent), \
         patch('worker.main.update_agent_state', mock_update), \
         patch('worker.main.call_ai_delta', mock_call_ai), \
         patch('worker.main.redis.from_url', return_value=mock_redis_client), \
         patch('worker.main.register_agent_idle', AsyncMock()) as mock_register:

        await process_task_assign("agent1", "task1", "description", {}, "goal1", simulation=False)

        mock_register.assert_awaited_once_with("agent1")
