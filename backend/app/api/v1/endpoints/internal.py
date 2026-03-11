from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional
from ....services.litellm_service import generate_with_messages
from ....services.redis_service import redis_service
from ....services.agent_manager import AgentManager
from ....services.docker_service import DockerService
from ....core.config import settings
from ....models.types import ConversationMessage
from datetime import datetime
import secrets
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai")

class GenerateDeltaRequest(BaseModel):
    agent_id: str
    input: str
    config: Dict[str, Any] = {}

class GenerateResponse(BaseModel):
    response: str

async def verify_internal_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    scheme, token = authorization.split()
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    expected = settings.secrets.get("INTERNAL_API_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="Internal API key not configured")
    if not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="Invalid token")
    return token

@router.post("/generate-delta", response_model=GenerateResponse)
async def ai_generate_delta(
    request: GenerateDeltaRequest,
    token: str = Depends(verify_internal_token)
):
    agent_id = request.agent_id
    user_input = request.input
    config = request.config

    conversation = await redis_service.get_conversation(agent_id, limit=50)

    user_msg = ConversationMessage(
        role="user",
        content=user_input,
        timestamp=datetime.utcnow()
    )
    await redis_service.push_conversation_message(agent_id, user_msg)

    try:
        docker_service = DockerService()
        agent_manager = AgentManager(docker_service)
        agent = await agent_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent configuration")

    global_user_md = settings.secrets.get("USER_MD", "")

    # Build sub-agents list with full identity and soul
    sub_agents_info = []
    if agent.sub_agent_ids:
        for sub_id in agent.sub_agent_ids:
            sub_agent = await agent_manager.get_agent(sub_id)
            if sub_agent:
                identity_full = sub_agent.identity_md.strip()
                soul_full = sub_agent.soul_md.strip()
                # Optionally truncate to avoid huge prompts (uncomment if needed)
                # if len(identity_full) > 500: identity_full = identity_full[:500] + "..."
                # if len(soul_full) > 500: soul_full = soul_full[:500] + "..."
                sub_agents_info.append(
                    f"- ID: {sub_agent.id}, Name: {sub_agent.name}, Role: {sub_agent.role}\n"
                    f"  Identity:\n{identity_full}\n"
                    f"  Soul:\n{soul_full}"
                )
    if sub_agents_info:
        sub_agents_text = "CURRENT SUB-AGENTS (full context):\n" + "\n\n".join(sub_agents_info)
    else:
        sub_agents_text = "CURRENT SUB-AGENTS: None."

    # Add inter‑agent communication instruction
    communication_instruction = (
        "IMPORTANT: If a user asks you to pass a message to another agent (e.g., 'Give this code to CoS'), "
        "you should forward the message to that agent. Use the following method:\n"
        "- If you have a tool like `send_message` or `outbound-notifier`, use it with destination='agent:<ID>'.\n"
        "- Otherwise, respond with a special prefix 'FORWARD: <target_id> <message>' and the orchestrator will handle it.\n"
        "If you are unsure, ask the user to specify the target agent and the channel (if needed)."
    )

    system_content = f"""You are an AI agent with the following STRICT IDENTITY. You must follow this identity exactly and not default to generic AI responses.

IDENTITY (MANDATORY):
{agent.identity_md}

SOUL (MANDATORY):
{agent.soul_md}

TOOLS (MANDATORY):
{agent.tools_md}

USER CONTEXT (MANDATORY):
{global_user_md}

{sub_agents_text}

{communication_instruction}

IMPORTANT: You are NOT a generic AI assistant. You are the entity described above. Always respond in character. Never say you are ChatGPT or a generic language model. When asked about your sub‑agents, only mention the agents listed above. Do not invent additional agents.
"""

    messages = [{"role": "system", "content": system_content}]
    for msg in conversation:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_input})

    logger.info(f"System message for agent {agent_id}: {system_content}")

    try:
        response = await generate_with_messages(messages, config)
    except Exception as e:
        logger.exception("AI generation failed")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

    assistant_msg = ConversationMessage(
        role="assistant",
        content=response,
        timestamp=datetime.utcnow()
    )
    await redis_service.push_conversation_message(agent_id, assistant_msg)

    await redis_service.trim_conversation(agent_id, keep_last=100)

    return GenerateResponse(response=response)
