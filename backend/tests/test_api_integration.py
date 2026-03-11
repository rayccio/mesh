import pytest
from httpx import AsyncClient
from app.models.types import AgentCreate, ReasoningConfig, ReportingTarget
from app.core.config import settings

@pytest.mark.asyncio
async def test_create_agent_api(client: AsyncClient, session):
    # First login to get token (simulate gateway disabled)
    # For tests, we can directly use the admin user created in setup
    # Or we can mock auth. Let's get a token by logging in.
    # Since tests run in isolation, we need to create a user first.
    # This is simplified: we'll use the no-auth token endpoint if gateway disabled.
    # For now, we'll assume gateway is enabled and we have a user.
    # We'll use the admin credentials from environment.
    # Alternatively, we can disable gateway in test settings.
    
    # For simplicity, we'll skip auth by setting an internal test header.
    headers = {"Authorization": f"Bearer {settings.secrets.get('INTERNAL_API_KEY')}"}
    
    agent_in = {
        "name": "API Test Agent",
        "role": "Worker",
        "soulMd": "test soul",
        "identityMd": "test identity",
        "toolsMd": "test tools",
        "reasoning": {
            "model": "openai/gpt-4o",
            "temperature": 0.7,
            "topP": 1.0,
            "maxTokens": 150,
            "use_global_default": True,
            "use_custom_max_tokens": False
        },
        "reportingTarget": "PARENT_AGENT"
    }
    response = await client.post("/api/v1/agents", json=agent_in, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "API Test Agent"
    agent_id = data["id"]
    
    # Clean up
    await client.delete(f"/api/v1/agents/{agent_id}", headers=headers)
