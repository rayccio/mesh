import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from app.services.agent_manager import AgentManager
from app.services.docker_service import DockerService
from app.models.types import AgentCreate, ReasoningConfig, ReportingTarget

@pytest.mark.asyncio
async def test_create_agent(session):
    docker = Mock(spec=DockerService)
    agent_manager = AgentManager(docker)
    agent_in = AgentCreate(
        name="Test Agent",
        role="Worker",
        soulMd="test soul",
        identityMd="test identity",
        toolsMd="test tools",
        reasoning=ReasoningConfig(model="openai/gpt-4o", temperature=0.7),
        reporting_target=ReportingTarget.PARENT
    )
    agent = await agent_manager.create_agent(agent_in)
    assert agent.id.startswith("b-")
    assert agent.name == "Test Agent"
    # Clean up (agent_manager.delete_agent would call docker, but we mock)
    # We'll just delete from DB
    await agent_manager.delete_agent(agent.id)
