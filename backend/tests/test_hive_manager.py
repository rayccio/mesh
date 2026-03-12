import pytest
from app.services.hive_manager import HiveManager
from app.models.types import HiveCreate
from app.services.agent_manager import AgentManager
from app.services.docker_service import DockerService
from unittest.mock import Mock, patch
from app.core.config import settings

@pytest.mark.asyncio
async def test_create_hive(session):
    # Mock internal API key for AgentManager (even though not used here, it's required by AgentManager init)
    with patch.object(settings.secrets, 'get', return_value="test-internal-key"):
        docker = Mock(spec=DockerService)
        agent_manager = AgentManager(docker)
        hive_manager = HiveManager(agent_manager)
        hive_in = HiveCreate(name="Test Hive", description="Test Description", global_user_md="")
        hive = await hive_manager.create_hive(hive_in)
        assert hive.id.startswith("h-")
        assert hive.name == "Test Hive"
        # Clean up
        await hive_manager.delete_hive(hive.id)
