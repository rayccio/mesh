import pytest
from httpx import AsyncClient
from app.core.config import settings

@pytest.mark.asyncio
async def test_create_agent_api(client: AsyncClient, session):
    # Use internal API key for authentication
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
