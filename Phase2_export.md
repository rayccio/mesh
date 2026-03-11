## 📄 agent.json

```json
{"id":"z-1dde","name":"CTO","role":"Worker","soulMd":"# Soul.md\n## Core Identity\nYou are an autonomous agent specialized in security auditing and communication.\n\n## Personality\n- Precise and technical\n- Concise in communication\n- Focused on isolation and least privilege\n\n## Constraints\n- You operate only within your Docker container.\n- You report all findings to the Overseer.\n- Minimize token usage by summarizing history.\n","identityMd":"# IDENTITY.md\n## Background\nEx-military cybersecurity specialist, transitioned into autonomous node operations.\n## Primary Directive\nEnsure the perimeter is never breached and sub-agents perform optimally.\n## Signature\n[CLAW_NODE_SEC_AUTH]\n","toolsMd":"# TOOLS.md\n## Permitted Tools\n- network-scanner (Internal Only)\n- log-analyzer\n- outbound-notifier (Telegram/Discord/WhatsApp)\n\n## Prohibited\n- External API access (unless specified in Channels)\n- Filesystem writes outside /home/agent/\n- Sudo/Root access\n","status":"RUNNING","reasoning":{"model":"openai:gpt-3.5-turbo","temperature":0.7,"top_p":1.0,"max_tokens":150,"api_key":null,"organization_id":null,"cheap_model":null,"use_global_default":true,"use_custom_max_tokens":false},"reportingTarget":"OWNER_DIRECT","parentId":"z-64a1","subAgentIds":[],"channels":[{"id":"ch-i2xun","type":"telegram","enabled":true,"credentials":{"webhook_url":null,"botToken":"8536112005:AAEV2odW1-0z_njQy3o_uwF-RoN6vB96R6c","chatId":"7086842086","api_key":null,"api_secret":null,"client_id":null,"mode":null},"status":"disconnected","last_ping":null}],"memory":{"short_term":[],"summary":"","token_count":0},"lastActive":"2026-02-26T01:23:29.624029","containerId":"0fd811fc1e4935f0d2b23073de476098e8a783e2e89dc1f54897c618fd8c4d01","userUid":"10001","localFiles":[]}
```

---

## 📄 backend/app/__init__.py

```py
# Package init

```

---

## 📄 backend/app/api/__init__.py

```py
# Package init

```

---

## 📄 backend/app/api/v1/__init__.py

```py
# Package init

```

---

## 📄 backend/app/api/v1/endpoints/__init__.py

```py
# Package init

```

---

## 📄 backend/app/api/v1/endpoints/agents.py

```py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging
from ....models.types import Agent, AgentCreate, AgentUpdate
from ....services.agent_manager import AgentManager
from ....services.docker_service import DockerService

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_agent_manager():
    try:
        docker_service = DockerService()
        docker_service.client.ping()
        logger.info("Docker client is responsive")
        return AgentManager(docker_service)
    except Exception as e:
        logger.exception("Failed to initialize DockerService or AgentManager")
        raise HTTPException(status_code=500, detail=f"Backend initialization error: {str(e)}")

@router.get("", response_model=List[Agent])
async def list_agents(
    channel_type: Optional[str] = Query(None, description="Filter agents that have this channel enabled"),
    manager: AgentManager = Depends(get_agent_manager)
):
    try:
        agents = await manager.list_agents()
        if channel_type:
            # Filter: agents that have a channel of this type with enabled=True
            agents = [a for a in agents if any(ch for ch in a.channels if ch.type == channel_type and ch.enabled)]
        return agents
    except Exception as e:
        logger.exception("Failed to list agents")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("", response_model=Agent, status_code=201)
async def create_agent(agent_in: AgentCreate, manager: AgentManager = Depends(get_agent_manager)):
    try:
        logger.info(f"Creating agent with data: {agent_in.dict(by_alias=True)}")
        result = await manager.create_agent(agent_in)
        logger.info(f"Agent created successfully: {result.id}")
        return result
    except Exception as e:
        logger.exception("Failed to create agent")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str, manager: AgentManager = Depends(get_agent_manager)):
    try:
        agent = await manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get agent {agent_id}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.patch("/{agent_id}", response_model=Agent)
async def update_agent(agent_id: str, agent_update: AgentUpdate, manager: AgentManager = Depends(get_agent_manager)):
    try:
        agent = await manager.update_agent(agent_id, agent_update)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update agent {agent_id}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, manager: AgentManager = Depends(get_agent_manager)):
    try:
        deleted = await manager.delete_agent(agent_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Agent not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete agent {agent_id}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/{agent_id}/execute", status_code=202)
async def execute_agent(agent_id: str, payload: dict = None, manager: AgentManager = Depends(get_agent_manager)):
    try:
        input_text = payload.get("input", "") if payload else ""
        success = await manager.execute_agent(agent_id, input_text)
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"status": "execution triggered"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to execute agent {agent_id}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/{parent_id}/subagents/{child_id}", status_code=200)
async def add_sub_agent(parent_id: str, child_id: str, manager: AgentManager = Depends(get_agent_manager)):
    try:
        success = await manager.add_sub_agent(parent_id, child_id)
        if not success:
            raise HTTPException(status_code=404, detail="Parent or child agent not found")
        return {"status": "sub-agent added"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to add sub-agent {child_id} to {parent_id}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

```

---

## 📄 backend/app/api/v1/endpoints/bridges.py

```py
from fastapi import APIRouter, HTTPException
from ....services.docker_service import DockerService
from ....core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Known bridge types and their container names (updated to hivebot)
BRIDGE_CONTAINERS = {
    "telegram": "hivebot_bridge_telegram",
    "discord": "hivebot_bridge_discord",
    "slack": "hivebot_bridge_slack",
    "whatsapp": "hivebot_bridge_whatsapp",
    "teams": "hivebot_bridge_teams",
}

@router.get("")
async def list_bridges():
    """Return list of available bridges with their status."""
    docker = DockerService()
    result = []
    enabled_bridges = settings.secrets.get("ENABLED_BRIDGES") or []
    for bridge_type, container_name in BRIDGE_CONTAINERS.items():
        status = docker.get_container_status_by_name(container_name)
        is_enabled = bridge_type in enabled_bridges
        result.append({
            "type": bridge_type,
            "enabled": is_enabled,
            "status": status,
            "container": container_name
        })
    return result

@router.post("/{bridge_type}/enable")
async def enable_bridge(bridge_type: str):
    if bridge_type not in BRIDGE_CONTAINERS:
        raise HTTPException(status_code=404, detail="Bridge type not found")
    container_name = BRIDGE_CONTAINERS[bridge_type]
    docker = DockerService()
    try:
        docker.start_container(container_name)
    except Exception as e:
        logger.exception(f"Failed to start bridge {bridge_type}")
        raise HTTPException(status_code=500, detail=str(e))
    enabled = set(settings.secrets.get("ENABLED_BRIDGES") or [])
    enabled.add(bridge_type)
    settings.secrets.set("ENABLED_BRIDGES", list(enabled))
    return {"status": "enabled"}

@router.post("/{bridge_type}/disable")
async def disable_bridge(bridge_type: str):
    if bridge_type not in BRIDGE_CONTAINERS:
        raise HTTPException(status_code=404, detail="Bridge type not found")
    container_name = BRIDGE_CONTAINERS[bridge_type]
    docker = DockerService()
    try:
        docker.stop_container_by_name(container_name)
    except Exception as e:
        logger.exception(f"Failed to stop bridge {bridge_type}")
        raise HTTPException(status_code=500, detail=str(e))
    enabled = set(settings.secrets.get("ENABLED_BRIDGES") or [])
    enabled.discard(bridge_type)
    settings.secrets.set("ENABLED_BRIDGES", list(enabled))
    return {"status": "disabled"}

@router.post("/{bridge_type}/restart")
async def restart_bridge(bridge_type: str):
    if bridge_type not in BRIDGE_CONTAINERS:
        raise HTTPException(status_code=404, detail="Bridge type not found")
    container_name = BRIDGE_CONTAINERS[bridge_type]
    docker = DockerService()
    try:
        docker.restart_container(container_name)
    except Exception as e:
        logger.exception(f"Failed to restart bridge {bridge_type}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "restarted"}

```

---

## 📄 backend/app/api/v1/endpoints/diagnostic.py

```py
from fastapi import APIRouter, HTTPException
import logging
from ....services.docker_service import DockerService
from ....services.redis_service import redis_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/docker-images")
async def list_docker_images():
    """Return list of available Docker images (for debugging)."""
    try:
        docker = DockerService()
        images = docker.client.images.list()
        result = []
        for img in images:
            tags = img.tags
            if not tags:
                tags = ["<none>"]
            for tag in tags:
                result.append(tag)
        return {"images": result}
    except Exception as e:
        logger.exception("Failed to list Docker images")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/secrets-check")
async def check_secrets():
    """Check if required secrets are present."""
    from ....core.config import settings
    internal_key = settings.secrets.get("INTERNAL_API_KEY")
    return {
        "internal_key_present": internal_key is not None,
        "gemini_key_present": settings.GEMINI_API_KEY is not None,
        "openai_key_present": settings.OPENAI_API_KEY is not None,
        "anthropic_key_present": settings.ANTHROPIC_API_KEY is not None,
    }

```

---

## 📄 backend/app/api/v1/endpoints/files.py

```py
import os
import shutil
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from ....services.agent_manager import AgentManager
from ....services.docker_service import DockerService
from ....models.types import FileEntry, AgentUpdate
from ....core.config import settings

router = APIRouter()

async def get_agent_manager():
    docker_service = DockerService()
    return AgentManager(docker_service)

@router.post("/agents/{agent_id}/files")
async def upload_agent_file(
    agent_id: str,
    file: UploadFile = File(...),
    manager: AgentManager = Depends(get_agent_manager)
):
    """Upload a file to the agent's files directory."""
    agent = await manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent_dir = settings.AGENTS_DIR / agent_id
    files_dir = agent_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = files_dir / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    
    file_entry = FileEntry(
        id=str(uuid.uuid4()),
        name=file.filename,
        type=file.filename.split('.')[-1] if '.' in file.filename else "bin",
        content="",
        size=os.path.getsize(file_path),
        uploaded_at=datetime.utcnow().isoformat()
    )
    
    agent.local_files.append(file_entry)
    update = AgentUpdate(local_files=agent.local_files)
    await manager.update_agent(agent_id, update)
    
    return file_entry

@router.get("/agents/{agent_id}/files", response_model=List[FileEntry])
async def list_agent_files(
    agent_id: str,
    manager: AgentManager = Depends(get_agent_manager)
):
    agent = await manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.local_files

@router.get("/agents/{agent_id}/files/{file_id}")
async def download_agent_file(
    agent_id: str,
    file_id: str,
    manager: AgentManager = Depends(get_agent_manager)
):
    agent = await manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    file_entry = next((f for f in agent.local_files if f.id == file_id), None)
    if not file_entry:
        raise HTTPException(status_code=404, detail="File not found")
    
    agent_dir = settings.AGENTS_DIR / agent_id
    file_path = agent_dir / "files" / file_entry.name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(file_path, filename=file_entry.name)

@router.delete("/agents/{agent_id}/files/{file_id}")
async def delete_agent_file(
    agent_id: str,
    file_id: str,
    manager: AgentManager = Depends(get_agent_manager)
):
    agent = await manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    file_entry = next((f for f in agent.local_files if f.id == file_id), None)
    if not file_entry:
        raise HTTPException(status_code=404, detail="File not found")
    
    agent_dir = settings.AGENTS_DIR / agent_id
    file_path = agent_dir / "files" / file_entry.name
    if file_path.exists():
        file_path.unlink()
    
    agent.local_files = [f for f in agent.local_files if f.id != file_id]
    update = AgentUpdate(local_files=agent.local_files)
    await manager.update_agent(agent_id, update)
    
    return {"status": "deleted"}

```

---

## 📄 backend/app/api/v1/endpoints/global_files.py

```py
import os
import shutil
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from ....core.config import settings
from ....models.types import FileEntry

router = APIRouter(tags=["global-files"])

# Use settings.GLOBAL_FILES_DIR
GLOBAL_FILES_DIR = settings.GLOBAL_FILES_DIR

@router.post("")
async def upload_global_file(file: UploadFile = File(...)):
    """Upload a global file accessible to all agents."""
    file_path = GLOBAL_FILES_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    
    file_entry = FileEntry(
        id=str(uuid.uuid4()),
        name=file.filename,
        type=file.filename.split('.')[-1] if '.' in file.filename else "bin",
        content="",
        size=os.path.getsize(file_path),
        uploaded_at=datetime.utcnow().isoformat()
    )
    return file_entry

@router.get("", response_model=List[FileEntry])
async def list_global_files():
    """List all global files."""
    files = []
    for filename in os.listdir(GLOBAL_FILES_DIR):
        file_path = GLOBAL_FILES_DIR / filename
        if file_path.is_file():
            files.append(FileEntry(
                id=filename,
                name=filename,
                type=filename.split('.')[-1] if '.' in filename else "bin",
                content="",
                size=os.path.getsize(file_path),
                uploaded_at=datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            ))
    return files

@router.get("/{filename}")
async def download_global_file(filename: str):
    """Download a global file."""
    file_path = GLOBAL_FILES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)

@router.delete("/{filename}")
async def delete_global_file(filename: str):
    """Delete a global file."""
    file_path = GLOBAL_FILES_DIR / filename
    if file_path.exists():
        file_path.unlink()
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="File not found")

```

---

## 📄 backend/app/api/v1/endpoints/health.py

```py
from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def health():
    return {"status": "healthy"}

```

---

## 📄 backend/app/api/v1/endpoints/hives.py

```py
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional
import logging
from ....models.types import Hive, HiveCreate, HiveUpdate, Agent, Message, FileEntry
from ....services.hive_manager import HiveManager
from ....services.docker_service import DockerService

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_hive_manager():
    return HiveManager()

@router.get("", response_model=List[Hive])
async def list_hives(
    manager: HiveManager = Depends(get_hive_manager)
):
    """List all hives"""
    try:
        return await manager.list_hives()
    except Exception as e:
        logger.exception("Failed to list hives")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("", response_model=Hive, status_code=201)
async def create_hive(
    hive_in: HiveCreate,
    manager: HiveManager = Depends(get_hive_manager)
):
    """Create a new hive"""
    try:
        logger.info(f"Creating hive with data: {hive_in.dict()}")
        result = await manager.create_hive(hive_in)
        logger.info(f"Hive created successfully: {result.id}")
        return result
    except Exception as e:
        logger.exception("Failed to create hive")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{hive_id}", response_model=Hive)
async def get_hive(
    hive_id: str,
    manager: HiveManager = Depends(get_hive_manager)
):
    """Get a specific hive by ID"""
    try:
        hive = await manager.get_hive(hive_id)
        if not hive:
            raise HTTPException(status_code=404, detail="Hive not found")
        return hive
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get hive {hive_id}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.patch("/{hive_id}", response_model=Hive)
async def update_hive(
    hive_id: str,
    hive_update: HiveUpdate,
    manager: HiveManager = Depends(get_hive_manager)
):
    """Update a hive"""
    try:
        hive = await manager.update_hive(hive_id, hive_update)
        if not hive:
            raise HTTPException(status_code=404, detail="Hive not found")
        return hive
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update hive {hive_id}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/{hive_id}", status_code=204)
async def delete_hive(
    hive_id: str,
    manager: HiveManager = Depends(get_hive_manager)
):
    """Delete a hive"""
    try:
        deleted = await manager.delete_hive(hive_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Hive not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete hive {hive_id}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Agent endpoints within hive
@router.get("/{hive_id}/agents", response_model=List[Agent])
async def list_hive_agents(
    hive_id: str,
    manager: HiveManager = Depends(get_hive_manager)
):
    """List all agents in a hive"""
    hive = await manager.get_hive(hive_id)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive not found")
    return hive.agents

@router.post("/{hive_id}/agents", response_model=Agent)
async def add_agent_to_hive(
    hive_id: str,
    agent: Agent,
    manager: HiveManager = Depends(get_hive_manager)
):
    """Add an agent to a hive"""
    hive = await manager.add_agent(hive_id, agent)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive not found")
    return agent

@router.patch("/{hive_id}/agents/{agent_id}", response_model=Agent)
async def update_hive_agent(
    hive_id: str,
    agent_id: str,
    agent_update: Agent,
    manager: HiveManager = Depends(get_hive_manager)
):
    """Update an agent in a hive"""
    hive = await manager.update_agent(hive_id, agent_id, agent_update)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive or agent not found")
    return agent_update

@router.delete("/{hive_id}/agents/{agent_id}", status_code=204)
async def remove_agent_from_hive(
    hive_id: str,
    agent_id: str,
    manager: HiveManager = Depends(get_hive_manager)
):
    """Remove an agent from a hive"""
    hive = await manager.remove_agent(hive_id, agent_id)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive or agent not found")

# Message endpoints
@router.get("/{hive_id}/messages", response_model=List[Message])
async def list_hive_messages(
    hive_id: str,
    manager: HiveManager = Depends(get_hive_manager)
):
    """List messages in a hive"""
    hive = await manager.get_hive(hive_id)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive not found")
    return hive.messages

@router.post("/{hive_id}/messages", response_model=Message)
async def add_message_to_hive(
    hive_id: str,
    message: Message,
    manager: HiveManager = Depends(get_hive_manager)
):
    """Add a message to a hive"""
    hive = await manager.add_message(hive_id, message)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive not found")
    return message

# Global files endpoints
@router.get("/{hive_id}/global-files", response_model=List[FileEntry])
async def list_hive_global_files(
    hive_id: str,
    manager: HiveManager = Depends(get_hive_manager)
):
    """List global files in a hive"""
    hive = await manager.get_hive(hive_id)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive not found")
    return hive.global_files

@router.post("/{hive_id}/global-files", response_model=FileEntry)
async def add_global_file_to_hive(
    hive_id: str,
    file_entry: FileEntry,
    manager: HiveManager = Depends(get_hive_manager)
):
    """Add a global file to a hive"""
    hive = await manager.add_global_file(hive_id, file_entry)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive not found")
    return file_entry

@router.delete("/{hive_id}/global-files/{file_id}", status_code=204)
async def remove_global_file_from_hive(
    hive_id: str,
    file_id: str,
    manager: HiveManager = Depends(get_hive_manager)
):
    """Remove a global file from a hive"""
    hive = await manager.remove_global_file(hive_id, file_id)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive or file not found")

```

---

## 📄 backend/app/api/v1/endpoints/internal.py

```py
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

```

---

## 📄 backend/app/api/v1/endpoints/known_providers.py

```py
from fastapi import APIRouter
from ....known_providers import KNOWN_PROVIDERS

router = APIRouter()

@router.get("")
async def get_known_providers():
    """Return the list of known AI providers and their default models."""
    return KNOWN_PROVIDERS

```

---

## 📄 backend/app/api/v1/endpoints/providers.py

```py
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
from ....models.types import (
    GlobalProviderConfig, ProviderConfigUpdate, ProviderStatusResponse,
    ProviderConfig, ProviderModel
)
from ....core.config import settings
from ....known_providers import KNOWN_PROVIDERS
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def get_provider_config() -> GlobalProviderConfig:
    config_data = settings.secrets.get("PROVIDER_CONFIG")
    if config_data:
        return GlobalProviderConfig(**config_data)
    return GlobalProviderConfig()

def save_provider_config(config: GlobalProviderConfig):
    settings.secrets.set("PROVIDER_CONFIG", config.dict())

@router.get("", response_model=ProviderStatusResponse)
async def get_providers():
    config = get_provider_config()
    # Dynamically set api_key_present based on actual key presence in secrets
    primary_model_id = None
    utility_model_id = None
    for provider_key, provider in config.providers.items():
        key = settings.secrets.get(f"PROVIDER_API_KEY_{provider_key.upper()}")
        provider.api_key_present = key is not None
        # Find primary and utility for response
        for model_id, model in provider.models.items():
            if model.enabled and model.is_primary:
                primary_model_id = f"{provider_key}:{model_id}"
            if model.enabled and model.is_utility:
                utility_model_id = f"{provider_key}:{model_id}"
    return ProviderStatusResponse(
        providers=config.providers,
        primary_model_id=primary_model_id,
        utility_model_id=utility_model_id
    )

@router.post("", response_model=ProviderStatusResponse)
async def update_provider(update: ProviderConfigUpdate):
    config = get_provider_config()
    provider_key = update.provider

    # If provider doesn't exist, create a default entry from known_providers
    if provider_key not in config.providers:
        known = next((kp for kp in KNOWN_PROVIDERS if kp["name"] == provider_key), None)
        if known:
            display_name = known["display_name"]
            models = {}
            for m in known["models"]:
                models[m["id"]] = ProviderModel(
                    id=m["id"],
                    name=m["name"],
                    enabled=True,  # enable all by default? Or only default primary/utility?
                    is_primary=m.get("default_primary", False),
                    is_utility=m.get("default_utility", False)
                )
            config.providers[provider_key] = ProviderConfig(
                name=provider_key,
                display_name=display_name,
                enabled=False,
                api_key_present=False,
                models=models
            )
        else:
            # If unknown provider, create empty entry
            config.providers[provider_key] = ProviderConfig(
                name=provider_key,
                display_name=provider_key.capitalize(),
                enabled=False,
                api_key_present=False,
                models={}
            )

    provider = config.providers[provider_key]

    if update.enabled is not None:
        provider.enabled = update.enabled

    if update.api_key is not None:
        if update.api_key:
            settings.secrets.set(f"PROVIDER_API_KEY_{provider_key.upper()}", update.api_key)
            provider.api_key_present = True
        else:
            settings.secrets.set(f"PROVIDER_API_KEY_{provider_key.upper()}", None)
            provider.api_key_present = False

    # Track if this update explicitly sets a model as primary or utility
    new_primary_provider = None
    new_primary_model = None
    new_utility_provider = None
    new_utility_model = None

    if update.models is not None:
        for model_id, model_updates in update.models.items():
            if model_id in provider.models:
                for field, value in model_updates.dict(exclude_unset=True).items():
                    setattr(provider.models[model_id], field, value)
            else:
                provider.models[model_id] = model_updates
            # Check if this model is being set as primary or utility in this update
            if model_updates.is_primary:
                new_primary_provider = provider_key
                new_primary_model = model_id
            if model_updates.is_utility:
                new_utility_provider = provider_key
                new_utility_model = model_id

    # --- Primary enforcement ---
    # If a new primary was set in this update, clear all other primaries.
    if new_primary_provider and new_primary_model:
        for pkey, pconf in config.providers.items():
            for mid, mconf in pconf.models.items():
                if pkey == new_primary_provider and mid == new_primary_model:
                    mconf.is_primary = True
                else:
                    mconf.is_primary = False
    else:
        # No new primary explicitly set. Ensure there is exactly one primary among enabled models.
        current_primary_provider = None
        current_primary_model = None
        for pkey, pconf in config.providers.items():
            for mid, mconf in pconf.models.items():
                if mconf.is_primary and mconf.enabled:
                    current_primary_provider = pkey
                    current_primary_model = mid
                    break
            if current_primary_provider:
                break

        if current_primary_provider and current_primary_model:
            # Check if the primary model is still enabled
            primary_model = config.providers[current_primary_provider].models.get(current_primary_model)
            if not primary_model or not primary_model.enabled:
                config.providers[current_primary_provider].models[current_primary_model].is_primary = False
                current_primary_provider = None
                current_primary_model = None

        if not current_primary_provider:
            # Pick first enabled model as primary
            for pkey, pconf in config.providers.items():
                for mid, mconf in pconf.models.items():
                    if mconf.enabled:
                        mconf.is_primary = True
                        current_primary_provider = pkey
                        current_primary_model = mid
                        break
                if current_primary_provider:
                    break

    # --- Utility enforcement (similar logic) ---
    if new_utility_provider and new_utility_model:
        for pkey, pconf in config.providers.items():
            for mid, mconf in pconf.models.items():
                if pkey == new_utility_provider and mid == new_utility_model:
                    mconf.is_utility = True
                else:
                    mconf.is_utility = False
    else:
        current_utility_provider = None
        current_utility_model = None
        for pkey, pconf in config.providers.items():
            for mid, mconf in pconf.models.items():
                if mconf.is_utility and mconf.enabled:
                    current_utility_provider = pkey
                    current_utility_model = mid
                    break
            if current_utility_provider:
                break

        if current_utility_provider and current_utility_model:
            utility_model = config.providers[current_utility_provider].models.get(current_utility_model)
            if not utility_model or not utility_model.enabled:
                config.providers[current_utility_provider].models[current_utility_model].is_utility = False
                current_utility_provider = None
                current_utility_model = None

        if not current_utility_provider:
            for pkey, pconf in config.providers.items():
                for mid, mconf in pconf.models.items():
                    if mconf.enabled:
                        mconf.is_utility = True
                        current_utility_provider = pkey
                        current_utility_model = mid
                        break
                if current_utility_provider:
                    break

    save_provider_config(config)
    # After saving, recompute api_key_present dynamically for the response
    for pkey, pconf in config.providers.items():
        key = settings.secrets.get(f"PROVIDER_API_KEY_{pkey.upper()}")
        pconf.api_key_present = key is not None

    # Build response
    primary_model_id = None
    utility_model_id = None
    for pkey, pconf in config.providers.items():
        for mid, mconf in pconf.models.items():
            if mconf.enabled and mconf.is_primary:
                primary_model_id = f"{pkey}:{mid}"
            if mconf.enabled and mconf.is_utility:
                utility_model_id = f"{pkey}:{mid}"

    return ProviderStatusResponse(
        providers=config.providers,
        primary_model_id=primary_model_id,
        utility_model_id=utility_model_id
    )

@router.delete("/{provider}", status_code=204)
async def delete_provider(provider: str):
    config = get_provider_config()
    if provider in config.providers:
        del config.providers[provider]
        settings.secrets.set(f"PROVIDER_API_KEY_{provider.upper()}", None)
        save_provider_config(config)
    return None

```

---

## 📄 backend/app/api/v1/endpoints/system.py

```py
from fastapi import APIRouter, Body, HTTPException
from ....core.config import settings
import requests

router = APIRouter()

@router.get("/uid")
async def get_default_uid():
    """
    Return the default UID used for agent containers.
    """
    return {"default_uid": settings.DEFAULT_AGENT_UID}

@router.get("/public-url")
async def get_public_url():
    """Get the currently configured public URL (used for webhooks)."""
    url = settings.secrets.get("PUBLIC_URL")
    return {"public_url": url}

@router.post("/public-url")
async def set_public_url(payload: dict = Body(...)):
    """Set the public URL. Pass null or empty string to clear."""
    url = payload.get("public_url")
    if url is not None:
        settings.secrets.set("PUBLIC_URL", url.strip() if url.strip() else None)
    return {"status": "ok"}

@router.get("/detect-public-ip")
async def detect_public_ip():
    """Try to detect the server's public IP using external services."""
    services = ["https://ifconfig.me", "https://icanhazip.com", "https://api.ipify.org"]
    for service in services:
        try:
            resp = requests.get(service, timeout=5)
            if resp.status_code == 200:
                ip = resp.text.strip()
                return {"public_ip": ip}
        except:
            continue
    return {"public_ip": None}

@router.get("/user-md")
async def get_user_md():
    """Get the global USER.md content."""
    content = settings.secrets.get("USER_MD")
    return {"content": content or ""}

@router.post("/user-md")
async def set_user_md(payload: dict = Body(...)):
    """Set the global USER.md content."""
    content = payload.get("content")
    settings.secrets.set("USER_MD", content)
    return {"status": "ok"}

```

---

## 📄 backend/app/api/v1/endpoints/ws.py

```py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ....services.ws_manager import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; we only send messages, no need to receive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

```

---

## 📄 backend/app/api/v1/router.py

```py
from fastapi import APIRouter
from .endpoints import health, agents, internal, files, global_files, providers, system, known_providers, bridges, hives

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(internal.router, prefix="/internal", tags=["internal"])
api_router.include_router(files.router, prefix="", tags=["files"])
api_router.include_router(global_files.router, prefix="/global-files", tags=["global-files"])
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(known_providers.router, prefix="/known-providers", tags=["known-providers"])
api_router.include_router(bridges.router, prefix="/bridges", tags=["bridges"])
api_router.include_router(hives.router, prefix="/hives", tags=["hives"])

```

---

## 📄 backend/app/core/__init__.py

```py
# Package init

```

---

## 📄 backend/app/core/config.py

```py
import os
from pydantic import Field, PrivateAttr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from pathlib import Path
from .secrets import SecretsManager

class Settings(BaseSettings):
    APP_NAME: str = "HiveBot Orchestrator"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: str = "http://localhost,http://localhost:3000"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    DOCKER_NETWORK: str = "hivebot_network"  # This must match the network name in compose

    # Base data directory (can be overridden by env)
    HIVEBOT_DATA: str = Field(default_factory=lambda: os.getenv('HIVEBOT_DATA', '/app/data'))

    # Default UID for agent containers
    DEFAULT_AGENT_UID: str = "10001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # These are computed properties, not fields, to avoid validation issues
    @property
    def SECRETS_DIR(self) -> Path:
        return Path(self.HIVEBOT_DATA) / "secrets"

    @property
    def AGENTS_DIR(self) -> Path:
        return Path(self.HIVEBOT_DATA) / "agents"

    @property
    def GLOBAL_FILES_DIR(self) -> Path:
        return Path(self.HIVEBOT_DATA) / "global_files"

    @property
    def DATA_DIR(self) -> Path:
        return Path(self.HIVEBOT_DATA) / "data"

    _secrets: SecretsManager = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        self.AGENTS_DIR.mkdir(parents=True, exist_ok=True)
        self.GLOBAL_FILES_DIR.mkdir(parents=True, exist_ok=True)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

        self._secrets = SecretsManager(
            secrets_path=self.SECRETS_DIR / "secrets.enc",
            master_key_path=self.SECRETS_DIR / "master.key"
        )

    @property
    def secrets(self) -> SecretsManager:
        return self._secrets

    @property
    def cors_origins(self) -> List[str]:
        if not self.BACKEND_CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()

```

---

## 📄 backend/app/core/secrets.py

```py
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag
from .security import derive_key, generate_salt

class SecretsManager:
    """
    Manages encrypted secrets using AES-256-GCM.
    Master key is stored as hex string, loaded and decoded to bytes.
    """

    def __init__(self, secrets_path: str, master_key_path: str):
        self.secrets_path = Path(secrets_path)
        self.master_key_path = Path(master_key_path)
        self._master_key = None
        self._secrets = None

    def _load_master_key(self) -> bytes:
        """Load master key from hex file, decode to bytes."""
        if self.master_key_path.exists():
            with open(self.master_key_path, 'r') as f:
                hex_key = f.read().strip()
                return bytes.fromhex(hex_key)
        else:
            key = os.urandom(32)
            self.master_key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.master_key_path, 'w') as f:
                f.write(key.hex())
            os.chmod(self.master_key_path, 0o600)
            return key

    def _get_master_key(self) -> bytes:
        if self._master_key is None:
            self._master_key = self._load_master_key()
        return self._master_key

    def encrypt_secrets(self, secrets: Dict[str, Any]) -> None:
        key = self._get_master_key()
        nonce = os.urandom(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        plaintext = json.dumps(secrets).encode('utf-8')
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        payload = nonce + ciphertext + encryptor.tag
        with open(self.secrets_path, 'wb') as f:
            f.write(payload)
        os.chmod(self.secrets_path, 0o600)

    def load_secrets(self) -> Dict[str, Any]:
        if not self.secrets_path.exists():
            return {}
        key = self._get_master_key()
        with open(self.secrets_path, 'rb') as f:
            payload = f.read()
        nonce = payload[:12]
        tag = payload[-16:]
        ciphertext = payload[12:-16]
        try:
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return json.loads(plaintext.decode('utf-8'))
        except InvalidTag:
            backup = f"{self.secrets_path}.corrupted.{int(time.time())}"
            os.rename(self.secrets_path, backup)
            return {}

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        if self._secrets is None:
            self._secrets = self.load_secrets()
        return self._secrets.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if self._secrets is None:
            self._secrets = self.load_secrets()
        self._secrets[key] = value
        self.encrypt_secrets(self._secrets)

```

---

## 📄 backend/app/core/security.py

```py
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

def derive_key(password: str, salt: bytes, iterations: int = 600000) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def generate_salt() -> bytes:
    return os.urandom(16)

```

---

## 📄 backend/app/known_providers.py

```py
# backend/app/known_providers.py
KNOWN_PROVIDERS = [
    {
        "name": "openai",
        "display_name": "OpenAI",
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o", "default_primary": True, "default_utility": False},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "default_primary": False, "default_utility": True},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "default_primary": False, "default_utility": False},
            {"id": "gpt-4", "name": "GPT-4", "default_primary": False, "default_utility": False},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "default_primary": False, "default_utility": False},
        ]
    },
    {
        "name": "anthropic",
        "display_name": "Anthropic",
        "models": [
            {"id": "claude-3-opus", "name": "Claude 3 Opus", "default_primary": True, "default_utility": False},
            {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet", "default_primary": False, "default_utility": False},
            {"id": "claude-3-haiku", "name": "Claude 3 Haiku", "default_primary": False, "default_utility": True},
            {"id": "claude-2.1", "name": "Claude 2.1", "default_primary": False, "default_utility": False},
            {"id": "claude-instant", "name": "Claude Instant", "default_primary": False, "default_utility": False},
        ]
    },
    {
        "name": "gemini",
        "display_name": "Google Gemini",
        "models": [
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "default_primary": True, "default_utility": False},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "default_primary": False, "default_utility": True},
            {"id": "gemini-1.0-pro", "name": "Gemini 1.0 Pro", "default_primary": False, "default_utility": False},
        ]
    },
    {
        "name": "deepseek",
        "display_name": "DeepSeek",
        "models": [
            {"id": "deepseek-chat", "name": "DeepSeek Chat", "default_primary": True, "default_utility": False},
            {"id": "deepseek-coder", "name": "DeepSeek Coder", "default_primary": False, "default_utility": False},
            {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner", "default_primary": False, "default_utility": True},
        ]
    },
    {
        "name": "cohere",
        "display_name": "Cohere",
        "models": [
            {"id": "command-r", "name": "Command R", "default_primary": True, "default_utility": False},
            {"id": "command-r-plus", "name": "Command R+", "default_primary": False, "default_utility": False},
            {"id": "command", "name": "Command", "default_primary": False, "default_utility": True},
            {"id": "command-light", "name": "Command Light", "default_primary": False, "default_utility": False},
        ]
    },
    {
        "name": "mistral",
        "display_name": "Mistral AI",
        "models": [
            {"id": "mistral-large", "name": "Mistral Large", "default_primary": True, "default_utility": False},
            {"id": "mistral-medium", "name": "Mistral Medium", "default_primary": False, "default_utility": False},
            {"id": "mistral-small", "name": "Mistral Small", "default_primary": False, "default_utility": True},
            {"id": "mixtral-8x7b", "name": "Mixtral 8x7B", "default_primary": False, "default_utility": False},
        ]
    },
    {
        "name": "groq",
        "display_name": "Groq",
        "models": [
            {"id": "llama3-70b", "name": "Llama 3 70B", "default_primary": True, "default_utility": False},
            {"id": "llama3-8b", "name": "Llama 3 8B", "default_primary": False, "default_utility": True},
            {"id": "mixtral-8x7b", "name": "Mixtral 8x7B", "default_primary": False, "default_utility": False},
            {"id": "gemma-7b", "name": "Gemma 7B", "default_primary": False, "default_utility": False},
        ]
    },
    {
        "name": "perplexity",
        "display_name": "Perplexity AI",
        "models": [
            {"id": "pplx-7b-online", "name": "7B Online", "default_primary": True, "default_utility": False},
            {"id": "pplx-70b-online", "name": "70B Online", "default_primary": False, "default_utility": True},
            {"id": "pplx-7b-chat", "name": "7B Chat", "default_primary": False, "default_utility": False},
        ]
    },
    {
        "name": "together",
        "display_name": "Together AI",
        "models": [
            {"id": "together-mix", "name": "Mix", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "fireworks",
        "display_name": "Fireworks AI",
        "models": [
            {"id": "fireworks-llama2", "name": "Llama 2", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "replicate",
        "display_name": "Replicate",
        "models": [
            {"id": "replicate-default", "name": "Default", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "huggingface",
        "display_name": "Hugging Face",
        "models": [
            {"id": "hf-default", "name": "Default", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "azure",
        "display_name": "Azure OpenAI",
        "models": [
            {"id": "azure-gpt4", "name": "GPT-4", "default_primary": True, "default_utility": False},
            {"id": "azure-gpt35", "name": "GPT-3.5", "default_primary": False, "default_utility": True},
        ]
    },
    {
        "name": "aws-bedrock",
        "display_name": "AWS Bedrock",
        "models": [
            {"id": "bedrock-claude", "name": "Claude", "default_primary": True, "default_utility": False},
            {"id": "bedrock-llama2", "name": "Llama 2", "default_primary": False, "default_utility": True},
        ]
    },
    {
        "name": "grok",
        "display_name": "xAI Grok",
        "models": [
            {"id": "grok-1", "name": "Grok-1", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "qwen",
        "display_name": "Qwen (Alibaba)",
        "models": [
            {"id": "qwen-72b", "name": "Qwen 72B", "default_primary": True, "default_utility": False},
            {"id": "qwen-14b", "name": "Qwen 14B", "default_primary": False, "default_utility": True},
        ]
    },
    {
        "name": "yi",
        "display_name": "Yi (01.AI)",
        "models": [
            {"id": "yi-34b", "name": "Yi 34B", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "nvidia",
        "display_name": "NVIDIA",
        "models": [
            {"id": "nemotron", "name": "Nemotron", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "ibm",
        "display_name": "IBM Watsonx",
        "models": [
            {"id": "granite", "name": "Granite", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "oracle",
        "display_name": "Oracle OCI",
        "models": [
            {"id": "oci-default", "name": "Default", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "sambanova",
        "display_name": "SambaNova",
        "models": [
            {"id": "sambanova-default", "name": "Default", "default_primary": True, "default_utility": True},
        ]
    },
]

```

---

## 📄 backend/app/main.py

```py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.v1.router import api_router
from .api.v1.endpoints.ws import router as ws_router
from .services.redis_service import redis_service
from .services.ws_manager import manager
from .services.agent_manager import AgentManager
from .services.docker_service import DockerService
from .services.litellm_service import generate_with_messages
from .api.v1.endpoints.bridges import BRIDGE_CONTAINERS
import logging
import asyncio
import json
import litellm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def sync_bridge_containers():
    """Ensure that only bridges marked as enabled are running."""
    docker = DockerService()
    enabled_bridges = settings.secrets.get("ENABLED_BRIDGES") or []
    for bridge_type, container_name in BRIDGE_CONTAINERS.items():
        status = docker.get_container_status_by_name(container_name)
        is_enabled = bridge_type in enabled_bridges
        if is_enabled and status != "running":
            logger.info(f"Starting bridge {bridge_type} (enabled but not running)")
            try:
                docker.start_container(container_name)
            except Exception as e:
                logger.error(f"Failed to start bridge {bridge_type}: {e}")
        elif not is_enabled and status == "running":
            logger.info(f"Stopping bridge {bridge_type} (disabled but running)")
            try:
                docker.stop_container_by_name(container_name)
            except Exception as e:
                logger.error(f"Failed to stop bridge {bridge_type}: {e}")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT != "production" else None,
    )
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(api_router, prefix=settings.API_V1_STR)
    app.include_router(ws_router)

    @app.get("/health")
    async def health_check():
        try:
            docker = DockerService()
            docker.client.ping()
            docker_ok = True
        except:
            docker_ok = False
        return {"status": "ok", "environment": settings.ENVIRONMENT, "docker": docker_ok}

    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting up HiveBot Orchestrator...")
        await redis_service.wait_ready()
        logger.info("Redis connected")
        asyncio.create_task(listen_for_owner_reports())
        asyncio.create_task(listen_for_parent_reports())
        asyncio.create_task(update_agent_memory_from_reports())
        asyncio.create_task(summarize_agent_memories())
        asyncio.create_task(sync_bridge_containers())

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down HiveBot...")
        await manager.disconnect_all()

    async def listen_for_owner_reports():
        pubsub = redis_service.client.pubsub()
        await pubsub.subscribe("report:owner")
        logger.info("Subscribed to report:owner")
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    response = data.get("response", "")
                    # Check for forwarding directive
                    if response.startswith("FORWARD:"):
                        parts = response.split(maxsplit=2)
                        if len(parts) >= 3:
                            _, target_id, forward_msg = parts
                            forward_cmd = {
                                "type": "think",
                                "input": forward_msg,
                                "config": {},
                                "timestamp": data.get("timestamp", "")
                            }
                            await redis_service.publish(f"agent:{target_id}", forward_cmd)
                            logger.info(f"Forwarded message to agent {target_id}")
                            continue
                    await manager.broadcast(message["data"])
                except Exception as e:
                    logger.error(f"Error processing report:owner message: {e}")

    async def listen_for_parent_reports():
        pubsub = redis_service.client.pubsub()
        await pubsub.psubscribe("report:parent:*")
        logger.info("Subscribed to report:parent:*")
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                channel = message["channel"]
                parent_id = channel.split(":")[-1]
                try:
                    data = json.loads(message["data"])
                    forward_msg = {
                        "type": "child_report",
                        "child_id": data.get("agent_id"),
                        "response": data.get("response"),
                        "timestamp": data.get("timestamp")
                    }
                    await redis_service.publish(f"agent:{parent_id}", forward_msg)
                    logger.info(f"Forwarded child report from {data.get('agent_id')} to parent {parent_id}")
                except Exception as e:
                    logger.error(f"Failed to forward parent report: {e}")

    async def update_agent_memory_from_reports():
        pubsub = redis_service.client.pubsub()
        await pubsub.subscribe("report:owner")
        logger.info("Subscribed to report:owner for memory updates")
        docker_service = DockerService()
        agent_manager = AgentManager(docker_service)

        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                data = json.loads(message["data"])
                agent_id = data.get("agent_id")
                response = data.get("response")
                if not agent_id or not response:
                    continue

                agent = await agent_manager.get_agent(agent_id)
                if not agent:
                    continue

                agent.memory.short_term.append(response)
                if len(agent.memory.short_term) > 10:
                    agent.memory.short_term = agent.memory.short_term[-10:]
                agent.memory.token_count += len(response.split()) * 1.3

                agent_manager._save_agents()
                logger.debug(f"Updated memory for agent {agent_id}")
            except Exception as e:
                logger.error(f"Failed to update agent memory: {e}")

    async def summarize_agent_memories():
        """Periodically summarize long conversations using cheap models."""
        while True:
            await asyncio.sleep(300)
            try:
                docker_service = DockerService()
                agent_manager = AgentManager(docker_service)
                for agent_id, agent in agent_manager.agents.items():
                    conversation = await redis_service.get_conversation(agent_id, limit=20)
                    if len(conversation) < 10:
                        continue

                    history = "\n".join([f"{msg.role}: {msg.content}" for msg in conversation])
                    prompt = f"""Summarize the following conversation history of an AI agent.

Agent identity:
{agent.identity_md}

Soul:
{agent.soul_md}

Conversation history:
{history}

Provide a concise summary (max 100 words) that captures the key points and context."""
                    
                    model_config = {}
                    if agent.reasoning.cheap_model:
                        model_config["model"] = agent.reasoning.cheap_model
                    else:
                        provider_config = settings.secrets.get("PROVIDER_CONFIG", {})
                        utility = None
                        for pkey, pconf in provider_config.get("providers", {}).items():
                            for mid, mconf in pconf.get("models", {}).items():
                                if mconf.get("is_utility"):
                                    utility = f"{pkey}/{mid}"
                                    break
                            if utility:
                                break
                        if utility:
                            model_config["model"] = utility
                        else:
                            logger.warning(f"No utility model available for summarization of agent {agent_id}")
                            continue
                    
                    try:
                        messages_for_ai = [{"role": "user", "content": prompt}]
                        response = await generate_with_messages(messages_for_ai, model_config)
                        agent.memory.summary = response
                        agent_manager._save_agents()
                        logger.info(f"Summarized memory for agent {agent_id}")
                    except Exception as e:
                        logger.error(f"Summarization failed for agent {agent_id}: {e}")
            except Exception as e:
                logger.exception("Error in memory summarization task")

    return app

app = create_app()

```

---

## 📄 backend/app/models/__init__.py

```py
# Package init

```

---

## 📄 backend/app/models/types.py

```py
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from datetime import datetime

class AgentStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"

class ReportingTarget(str, Enum):
    PARENT = "PARENT_AGENT"
    OWNER_DIRECT = "OWNER_DIRECT"
    BOTH = "HYBRID"

class HiveMindAccessLevel(str, Enum):
    ISOLATED = "ISOLATED"
    SHARED = "SHARED"
    GLOBAL = "GLOBAL"

class UserRole(str, Enum):
    GLOBAL_ADMIN = "GLOBAL_ADMIN"
    HIVE_ADMIN = "HIVE_ADMIN"
    HIVE_USER = "HIVE_USER"

# Channel types and configurations
ChannelType = Literal["telegram", "discord", "whatsapp", "slack", "custom"]

class ChannelCredentials(BaseModel):
    webhook_url: Optional[str] = None
    bot_token: Optional[str] = Field(None, alias="botToken")
    chat_id: Optional[str] = Field(None, alias="chatId")
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    client_id: Optional[str] = None
    mode: Optional[str] = None  # "auto", "webhook", "polling"

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True
    )

class ChannelConfig(BaseModel):
    id: str
    type: ChannelType
    enabled: bool
    credentials: ChannelCredentials
    status: Literal["connected", "error", "disconnected"] = "disconnected"
    last_ping: Optional[datetime] = None

class FileEntry(BaseModel):
    id: str
    name: str
    type: str  # file extension, e.g., 'txt', 'png', 'pdf'
    content: str
    size: int
    uploaded_at: datetime

class AgentMemory(BaseModel):
    short_term: List[str] = []
    summary: str = ""
    token_count: int = 0

class ReasoningConfig(BaseModel):
    model: str  # provider:model, e.g., "openai:gpt-4o"
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int = 150
    api_key: Optional[str] = None
    organization_id: Optional[str] = None
    cheap_model: Optional[str] = None
    use_global_default: bool = False
    use_custom_max_tokens: bool = False

class Agent(BaseModel):
    id: str
    name: str
    role: str
    soul_md: str = Field(alias="soulMd")
    identity_md: str = Field(alias="identityMd")
    tools_md: str = Field(alias="toolsMd")
    status: AgentStatus
    reasoning: ReasoningConfig
    reporting_target: ReportingTarget = ReportingTarget.PARENT
    parent_id: Optional[str] = None
    sub_agent_ids: List[str] = []
    channels: List[ChannelConfig] = []
    memory: AgentMemory
    last_active: datetime
    container_id: str
    user_uid: str
    local_files: List[FileEntry] = []

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        use_enum_values=True
    )

class Message(BaseModel):
    id: str
    from_agent: Optional[str] = Field(None, alias="from")
    to_agent: Optional[str] = Field(None, alias="to")
    content: str
    timestamp: datetime
    type: Optional[Literal["log", "chat", "internal", "error", "outbound"]] = None
    role: Optional[Literal["user", "model", "system"]] = None

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True
    )

class AgentCreate(BaseModel):
    name: str
    role: str = "Worker"
    soul_md: str = Field(alias="soulMd")
    identity_md: str = Field(alias="identityMd")
    tools_md: str = Field(alias="toolsMd")
    reasoning: ReasoningConfig
    reporting_target: ReportingTarget = ReportingTarget.PARENT
    parent_id: Optional[str] = None
    user_uid: Optional[str] = None
    channels: List[ChannelConfig] = []

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        use_enum_values=True
    )

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    soul_md: Optional[str] = Field(None, alias="soulMd")
    identity_md: Optional[str] = Field(None, alias="identityMd")
    tools_md: Optional[str] = Field(None, alias="toolsMd")
    status: Optional[AgentStatus] = None
    reasoning: Optional[ReasoningConfig] = None
    reporting_target: Optional[ReportingTarget] = None
    parent_id: Optional[str] = None
    channels: Optional[List[ChannelConfig]] = None
    memory: Optional[AgentMemory] = None
    local_files: Optional[List[FileEntry]] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        use_enum_values=True
    )

# ----------------------------
# Provider Configuration Models
# ----------------------------

class ProviderModel(BaseModel):
    id: str
    name: str
    enabled: bool = False
    is_primary: bool = False
    is_utility: bool = False

class ProviderConfig(BaseModel):
    name: str
    display_name: str
    enabled: bool = False
    api_key_present: bool = False
    models: Dict[str, ProviderModel] = {}

class GlobalProviderConfig(BaseModel):
    providers: Dict[str, ProviderConfig] = {}

class ProviderConfigUpdate(BaseModel):
    provider: str
    enabled: Optional[bool] = None
    api_key: Optional[str] = None
    models: Optional[Dict[str, ProviderModel]] = None

class ProviderStatusResponse(BaseModel):
    providers: Dict[str, ProviderConfig]
    primary_model_id: Optional[str] = None
    utility_model_id: Optional[str] = None

# ----------------------------
# Conversation Message for Delta Updates
# ----------------------------
class ConversationMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime

# ----------------------------
# Hive (Project) Models
# ----------------------------
class HiveMindConfig(BaseModel):
    access_level: HiveMindAccessLevel = HiveMindAccessLevel.ISOLATED
    shared_hive_ids: List[str] = []

class Hive(BaseModel):
    id: str
    name: str
    description: str = ""
    agents: List[Agent] = []
    global_user_md: str = ""
    global_uid: str = "1001"
    global_api_key: str = ""
    messages: List[Message] = []
    global_files: List[FileEntry] = []
    hive_mind_config: HiveMindConfig = HiveMindConfig()
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        use_enum_values=True
    )

class HiveCreate(BaseModel):
    name: str
    description: str = ""
    global_user_md: str = ""
    global_uid: str = "1001"
    global_api_key: str = ""

class HiveUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    global_user_md: Optional[str] = None
    global_uid: Optional[str] = None
    global_api_key: Optional[str] = None
    hive_mind_config: Optional[HiveMindConfig] = None

# ----------------------------
# User Models
# ----------------------------
class UserAccount(BaseModel):
    id: str
    username: str
    password_hash: str  # We'll store hashed passwords
    role: UserRole
    assigned_hive_ids: List[str] = []
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.HIVE_USER
    assigned_hive_ids: List[str] = []

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    assigned_hive_ids: Optional[List[str]] = None

class UserLogin(BaseModel):
    username: str
    password: str

# ----------------------------
# Global Settings
# ----------------------------
class GlobalSettings(BaseModel):
    login_enabled: bool = True
    session_timeout: int = 30  # minutes
    system_name: str = "HiveBot Orchestrator"
    maintenance_mode: bool = False

```

---

## 📄 backend/app/services/__init__.py

```py
# Package init

```

---

## 📄 backend/app/services/agent_manager.py

```py
import json
import os
from typing import Dict, Optional, List, Set
from datetime import datetime
from ..models.types import Agent, AgentCreate, AgentUpdate, AgentStatus, ChannelConfig
from ..core.config import settings
from .docker_service import DockerService
from .redis_service import redis_service
import uuid
import shutil
import logging

logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class AgentManager:
    def __init__(self, docker_service: DockerService):
        self.docker = docker_service
        self.agents: Dict[str, Agent] = {}
        self.storage_path = settings.DATA_DIR / "agents.json"
        self._load_agents()

    def _deserialize_agent(self, data: dict) -> Agent:
        if "last_active" in data and isinstance(data["last_active"], str):
            data["last_active"] = datetime.fromisoformat(data["last_active"])
        return Agent(**data)

    def _load_agents(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for agent_id, agent_dict in data.items():
                        self.agents[agent_id] = self._deserialize_agent(agent_dict)
                logger.info(f"Loaded {len(self.agents)} agents from {self.storage_path}")
            except Exception as e:
                logger.error(f"Failed to load agents from {self.storage_path}: {e}")
                if self.storage_path.exists():
                    backup = self.storage_path.with_suffix(".corrupted")
                    os.rename(self.storage_path, backup)
                    logger.info(f"Backed up corrupted file to {backup}")

    def _save_agents(self):
        try:
            data = {}
            for agent_id, agent in self.agents.items():
                data[agent_id] = agent.dict(by_alias=True)
            temp_path = self.storage_path.with_suffix(".tmp")
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2, cls=DateTimeEncoder)
            os.replace(temp_path, self.storage_path)
            logger.info(f"Saved {len(self.agents)} agents to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save agents to {self.storage_path}: {e}")

    async def _publish_config_update(self, agent: Agent, changed_types: Set[str]):
        """For each channel type in changed_types, publish a config update to Redis."""
        for ch_type in changed_types:
            await redis_service.publish(f"config:bridge:{ch_type}", json.dumps({"agent_id": agent.id}))

    async def create_agent(self, agent_in: AgentCreate) -> Agent:
        agent_id = f"b-{uuid.uuid4().hex[:4]}"  # use b- prefix for bots
        user_uid = agent_in.user_uid or "10001"
        internal_api_key = settings.secrets.get("INTERNAL_API_KEY")
        if not internal_api_key:
            raise RuntimeError("Internal API key not configured")
        
        container_id = self.docker.create_container(
            agent_id=agent_id,
            user_uid=user_uid,
            parent_id=agent_in.parent_id,
            reporting_target=agent_in.reporting_target,
            internal_api_key=internal_api_key,
            redis_host=settings.REDIS_HOST,
            orchestrator_url="http://backend:8000"
        )
        
        agent_dir = settings.AGENTS_DIR / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        with open(agent_dir / "soul.md", "w") as f:
            f.write(agent_in.soul_md)
        with open(agent_dir / "identity.md", "w") as f:
            f.write(agent_in.identity_md)
        with open(agent_dir / "tools.md", "w") as f:
            f.write(agent_in.tools_md)
        
        files_dir = agent_dir / "files"
        files_dir.mkdir(exist_ok=True)
        
        agent = Agent(
            id=agent_id,
            name=agent_in.name,
            role=agent_in.role,
            soul_md=agent_in.soul_md,
            identity_md=agent_in.identity_md,
            tools_md=agent_in.tools_md,
            status=AgentStatus.IDLE,
            reasoning=agent_in.reasoning,
            reporting_target=agent_in.reporting_target,
            parent_id=agent_in.parent_id,
            sub_agent_ids=[],
            memory={"short_term": [], "summary": "", "token_count": 0},
            last_active=datetime.utcnow(),
            container_id=container_id,
            user_uid=user_uid,
            local_files=[],
            channels=agent_in.channels or []
        )
        self.agents[agent_id] = agent
        self._save_agents()

        if agent.parent_id and agent.parent_id in self.agents:
            parent = self.agents[agent.parent_id]
            parent.sub_agent_ids.append(agent_id)
            self._save_agents()
            logger.info(f"Bot {agent_id} added as sub‑bot of {agent.parent_id}")

        channel_types = {ch.type for ch in agent.channels if ch.enabled}
        if channel_types:
            await self._publish_config_update(agent, channel_types)

        logger.info(f"Created bot {agent_id}")
        return agent

    async def add_sub_agent(self, parent_id: str, child_id: str) -> bool:
        if parent_id not in self.agents or child_id not in self.agents:
            return False
        parent = self.agents[parent_id]
        child = self.agents[child_id]
        if child.parent_id and child.parent_id != parent_id:
            old_parent = self.agents.get(child.parent_id)
            if old_parent and child_id in old_parent.sub_agent_ids:
                old_parent.sub_agent_ids.remove(child_id)
        child.parent_id = parent_id
        if child_id not in parent.sub_agent_ids:
            parent.sub_agent_ids.append(child_id)
        self._save_agents()
        logger.info(f"Bot {child_id} now child of {parent_id}")
        return True

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        agent = self.agents.get(agent_id)
        if agent:
            status = self.docker.get_container_status(agent.container_id)
            agent.status = self._map_docker_status(status)
        return agent

    async def list_agents(self) -> List[Agent]:
        container_map = self.docker.list_containers()
        for agent_id, agent in self.agents.items():
            if agent.container_id in container_map:
                agent.status = self._map_docker_status(container_map[agent.container_id]["status"])
            else:
                agent.status = AgentStatus.OFFLINE
        return list(self.agents.values())

    async def get_agents_by_channel_type(self, channel_type: str) -> List[Agent]:
        """Return agents that have an enabled channel of the given type."""
        return [a for a in self.agents.values() if any(ch for ch in a.channels if ch.type == channel_type and ch.enabled)]

    async def update_agent(self, agent_id: str, agent_update: AgentUpdate) -> Optional[Agent]:
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        if isinstance(agent_update, dict):
            agent_update = AgentUpdate(**agent_update)
        update_data = agent_update.dict(exclude_unset=True, by_alias=False)

        old_enabled_channels = {ch.id: ch for ch in agent.channels if ch.enabled}

        for field, value in update_data.items():
            if field == "channels" and value is not None:
                converted = []
                for ch_dict in value:
                    if isinstance(ch_dict, dict):
                        converted.append(ChannelConfig(**ch_dict))
                    else:
                        converted.append(ch_dict)
                setattr(agent, field, converted)
            else:
                setattr(agent, field, value)

        new_enabled_channels = {ch.id: ch for ch in agent.channels if ch.enabled}

        old_types = {ch.type for ch in agent.channels if ch.enabled}
        new_types = {ch.type for ch in agent.channels if ch.enabled}
        changed_types = old_types.symmetric_difference(new_types)

        common_ids = set(old_enabled_channels.keys()) & set(new_enabled_channels.keys())
        for ch_id in common_ids:
            old_ch = old_enabled_channels[ch_id]
            new_ch = new_enabled_channels[ch_id]
            if old_ch.credentials != new_ch.credentials:
                changed_types.add(old_ch.type)

        if "soul_md" in update_data or "identity_md" in update_data or "tools_md" in update_data:
            agent_dir = settings.AGENTS_DIR / agent_id
            if "soul_md" in update_data:
                with open(agent_dir / "soul.md", "w") as f:
                    f.write(agent.soul_md)
            if "identity_md" in update_data:
                with open(agent_dir / "identity.md", "w") as f:
                    f.write(agent.identity_md)
            if "tools_md" in update_data:
                with open(agent_dir / "tools.md", "w") as f:
                    f.write(agent.tools_md)
        agent.last_active = datetime.utcnow()
        self._save_agents()

        if changed_types:
            await self._publish_config_update(agent, changed_types)

        return agent

    async def delete_agent(self, agent_id: str) -> bool:
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        channel_types = {ch.type for ch in agent.channels if ch.enabled}

        if agent.parent_id and agent.parent_id in self.agents:
            parent = self.agents[agent.parent_id]
            if agent_id in parent.sub_agent_ids:
                parent.sub_agent_ids.remove(agent_id)
        for child_id in agent.sub_agent_ids:
            if child_id in self.agents:
                self.agents[child_id].parent_id = None
        self.docker.stop_container(agent.container_id)
        del self.agents[agent_id]
        self._save_agents()
        shutil.rmtree(settings.AGENTS_DIR / agent_id, ignore_errors=True)
        await redis_service.clear_conversation(agent_id)

        if channel_types:
            for ch_type in channel_types:
                await redis_service.publish(f"config:bridge:{ch_type}", json.dumps({"agent_id": agent_id}))

        return True

    async def execute_agent(self, agent_id: str, input_text: str = "") -> bool:
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        message = {
            "type": "think",
            "input": input_text,
            "config": agent.reasoning.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        await redis_service.publish(f"agent:{agent_id}", message)
        agent.status = AgentStatus.RUNNING
        return True

    def _map_docker_status(self, docker_status: str) -> AgentStatus:
        if docker_status == "running":
            return AgentStatus.RUNNING
        elif docker_status in ("exited", "dead"):
            return AgentStatus.ERROR
        elif docker_status == "paused":
            return AgentStatus.IDLE
        else:
            return AgentStatus.OFFLINE

```

---

## 📄 backend/app/services/docker_service.py

```py
import docker
from docker.errors import DockerException, NotFound, APIError
from typing import Optional, Dict, Any
from ..core.config import settings
import os
import logging

logger = logging.getLogger(__name__)

class DockerService:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Docker client initialized")
        except DockerException as e:
            logger.error(f"Docker connection failed: {e}")
            raise

    def _ensure_image_exists(self) -> str:
        """Check if agent image exists; if not, raise error. Returns image tag."""
        image_tag = "hivebot/agent:latest"
        try:
            self.client.images.get(image_tag)
            logger.info(f"Agent image {image_tag} found.")
            return image_tag
        except NotFound:
            logger.error(f"Agent image {image_tag} not found. Please build it first using the agent-builder service or setup.sh.")
            try:
                images = self.client.images.list()
                image_names = [tag for img in images for tag in img.tags]
                logger.info(f"Available images: {image_names}")
            except Exception as e:
                logger.error(f"Failed to list images: {e}")
            raise RuntimeError(f"Agent image {image_tag} missing. Run the agent-builder service or re-run setup.sh.")
        except APIError as e:
            logger.error(f"Error checking agent image: {e}")
            raise RuntimeError(f"Failed to check agent image: {e}")

    def _set_ownership(self, path: str, uid: int):
        """Recursively change ownership of path to uid:uid."""
        for root, dirs, files in os.walk(path):
            for d in dirs:
                try:
                    os.chown(os.path.join(root, d), uid, uid)
                except Exception as e:
                    logger.warning(f"Failed to chown directory {d}: {e}")
            for f in files:
                try:
                    os.chown(os.path.join(root, f), uid, uid)
                except Exception as e:
                    logger.warning(f"Failed to chown file {f}: {e}")
        try:
            os.chown(path, uid, uid)
        except Exception as e:
            logger.warning(f"Failed to chown root directory {path}: {e}")

    def create_container(self,
                        agent_id: str,
                        user_uid: str,
                        parent_id: Optional[str] = None,
                        reporting_target: str = "PARENT_AGENT",
                        internal_api_key: str = None,
                        redis_host: str = "redis",
                        orchestrator_url: str = "http://backend:8000") -> str:
        image = self._ensure_image_exists()
        host_data_dir = settings.AGENTS_DIR / agent_id
        host_data_dir.mkdir(parents=True, exist_ok=True)

        try:
            uid_int = int(user_uid)
            self._set_ownership(str(host_data_dir), uid_int)
        except ValueError:
            logger.error(f"Invalid user_uid: {user_uid}, not an integer")
            raise RuntimeError(f"Invalid UID: {user_uid}")

        environment = {
            "AGENT_ID": agent_id,
            "PARENT_ID": parent_id or "",
            "REPORTING_TARGET": reporting_target,
            "REDIS_HOST": redis_host,
            "ORCHESTRATOR_URL": orchestrator_url,
            "INTERNAL_API_KEY": internal_api_key,
            "AGENT_UID": user_uid,
        }

        try:
            container = self.client.containers.run(
                image=image,
                name=f"hivebot_agent_{agent_id}",
                detach=True,
                network=settings.DOCKER_NETWORK,
                environment=environment,
                volumes={
                    str(host_data_dir): {"bind": "/data", "mode": "rw"}
                },
                user=f"{user_uid}:{user_uid}",
                mem_limit="128m",
                cpu_shares=512,
                restart_policy={"Name": "unless-stopped"},
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                read_only=True,
                tmpfs={"/tmp": "rw,noexec,nosuid,size=64m"}
            )
            logger.info(f"Created container {container.id} for agent {agent_id}")
            return container.id
        except APIError as e:
            logger.error(f"Docker API error creating container for agent {agent_id}: {e}")
            raise RuntimeError(f"Container creation failed: {e}")

    def get_container_status(self, container_id: str) -> str:
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except NotFound:
            return "not_found"
        except APIError as e:
            logger.error(f"Error getting container {container_id}: {e}")
            return "unknown"

    def stop_container(self, container_id: str):
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=5)
            container.remove()
            logger.info(f"Removed container {container_id}")
        except NotFound:
            logger.warning(f"Container {container_id} not found")
        except APIError as e:
            logger.error(f"Error stopping container {container_id}: {e}")

    def list_containers(self) -> Dict[str, Dict[str, Any]]:
        try:
            containers = self.client.containers.list(all=True, filters={"name": "hivebot_agent_"})
            result = {}
            for c in containers:
                if c.name.startswith("hivebot_agent_"):
                    agent_id = c.name[14:]  # len("hivebot_agent_") = 14
                    result[agent_id] = {
                        "id": c.id,
                        "status": c.status,
                        "created": c.attrs["Created"],
                    }
            return result
        except APIError as e:
            logger.error(f"Failed to list containers: {e}")
            return {}

    def get_container_status_by_name(self, container_name: str) -> str:
        try:
            container = self.client.containers.get(container_name)
            return container.status
        except NotFound:
            return "not_found"
        except APIError as e:
            logger.error(f"Error getting container {container_name}: {e}")
            return "unknown"

    def start_container(self, container_name: str):
        try:
            container = self.client.containers.get(container_name)
            container.start()
            logger.info(f"Started container {container_name}")
        except NotFound:
            logger.error(f"Container {container_name} not found")
            raise RuntimeError(f"Container {container_name} not found")
        except APIError as e:
            logger.error(f"Error starting container {container_name}: {e}")
            raise

    def stop_container_by_name(self, container_name: str):
        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=5)
            logger.info(f"Stopped container {container_name}")
        except NotFound:
            logger.warning(f"Container {container_name} not found")
        except APIError as e:
            logger.error(f"Error stopping container {container_name}: {e}")
            raise

    def restart_container(self, container_name: str):
        try:
            container = self.client.containers.get(container_name)
            container.restart(timeout=5)
            logger.info(f"Restarted container {container_name}")
        except NotFound:
            logger.error(f"Container {container_name} not found")
            raise RuntimeError(f"Container {container_name} not found")
        except APIError as e:
            logger.error(f"Error restarting container {container_name}: {e}")
            raise

```

---

## 📄 backend/app/services/hive_manager.py

```py
import json
import os
from typing import Dict, Optional, List
from datetime import datetime
from ..models.types import Hive, HiveCreate, HiveUpdate, Agent, Message, FileEntry
from ..core.config import settings
import uuid
import shutil
import logging

logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class HiveManager:
    def __init__(self):
        self.hives: Dict[str, Hive] = {}
        self.storage_path = settings.DATA_DIR / "hives.json"
        self._load_hives()

    def _deserialize_hive(self, data: dict) -> Hive:
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return Hive(**data)

    def _load_hives(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for hive_id, hive_dict in data.items():
                        self.hives[hive_id] = self._deserialize_hive(hive_dict)
                logger.info(f"Loaded {len(self.hives)} hives from {self.storage_path}")
            except Exception as e:
                logger.error(f"Failed to load hives from {self.storage_path}: {e}")
                if self.storage_path.exists():
                    backup = self.storage_path.with_suffix(".corrupted")
                    os.rename(self.storage_path, backup)
                    logger.info(f"Backed up corrupted file to {backup}")

    def _save_hives(self):
        try:
            data = {}
            for hive_id, hive in self.hives.items():
                data[hive_id] = hive.dict(by_alias=True)
            temp_path = self.storage_path.with_suffix(".tmp")
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2, cls=DateTimeEncoder)
            os.replace(temp_path, self.storage_path)
            logger.info(f"Saved {len(self.hives)} hives to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save hives to {self.storage_path}: {e}")

    async def create_hive(self, hive_in: HiveCreate) -> Hive:
        hive_id = f"h-{uuid.uuid4().hex[:4]}"
        
        # Create hive directory
        hive_dir = settings.AGENTS_DIR / hive_id
        hive_dir.mkdir(parents=True, exist_ok=True)
        
        now = datetime.utcnow()
        hive = Hive(
            id=hive_id,
            name=hive_in.name,
            description=hive_in.description,
            agents=[],
            global_user_md=hive_in.global_user_md,
            global_uid=hive_in.global_uid,
            global_api_key=hive_in.global_api_key,
            messages=[],
            global_files=[],
            hive_mind_config={"access_level": "ISOLATED", "shared_hive_ids": []},
            created_at=now,
            updated_at=now
        )
        self.hives[hive_id] = hive
        self._save_hives()
        logger.info(f"Created hive {hive_id}")
        return hive

    async def get_hive(self, hive_id: str) -> Optional[Hive]:
        return self.hives.get(hive_id)

    async def list_hives(self) -> List[Hive]:
        return list(self.hives.values())

    async def update_hive(self, hive_id: str, hive_update: HiveUpdate) -> Optional[Hive]:
        hive = self.hives.get(hive_id)
        if not hive:
            return None
        
        update_data = hive_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(hive, field, value)
        
        hive.updated_at = datetime.utcnow()
        self._save_hives()
        return hive

    async def delete_hive(self, hive_id: str) -> bool:
        if hive_id not in self.hives:
            return False
        
        # Remove hive directory
        hive_dir = settings.AGENTS_DIR / hive_id
        if hive_dir.exists():
            shutil.rmtree(hive_dir, ignore_errors=True)
        
        del self.hives[hive_id]
        self._save_hives()
        return True

    # Agent management within hive
    async def add_agent(self, hive_id: str, agent: Agent) -> Optional[Hive]:
        hive = self.hives.get(hive_id)
        if not hive:
            return None
        
        hive.agents.append(agent)
        hive.updated_at = datetime.utcnow()
        self._save_hives()
        return hive

    async def update_agent(self, hive_id: str, agent_id: str, agent_update: Agent) -> Optional[Hive]:
        hive = self.hives.get(hive_id)
        if not hive:
            return None
        
        for i, agent in enumerate(hive.agents):
            if agent.id == agent_id:
                hive.agents[i] = agent_update
                hive.updated_at = datetime.utcnow()
                self._save_hives()
                return hive
        return None

    async def remove_agent(self, hive_id: str, agent_id: str) -> Optional[Hive]:
        hive = self.hives.get(hive_id)
        if not hive:
            return None
        
        hive.agents = [a for a in hive.agents if a.id != agent_id]
        hive.updated_at = datetime.utcnow()
        self._save_hives()
        return hive

    # Message management
    async def add_message(self, hive_id: str, message: Message) -> Optional[Hive]:
        hive = self.hives.get(hive_id)
        if not hive:
            return None
        
        hive.messages.append(message)
        # Keep only last 100 messages per hive
        if len(hive.messages) > 100:
            hive.messages = hive.messages[-100:]
        hive.updated_at = datetime.utcnow()
        self._save_hives()
        return hive

    # File management
    async def add_global_file(self, hive_id: str, file_entry: FileEntry) -> Optional[Hive]:
        hive = self.hives.get(hive_id)
        if not hive:
            return None
        
        hive.global_files.append(file_entry)
        hive.updated_at = datetime.utcnow()
        self._save_hives()
        return hive

    async def remove_global_file(self, hive_id: str, file_id: str) -> Optional[Hive]:
        hive = self.hives.get(hive_id)
        if not hive:
            return None
        
        hive.global_files = [f for f in hive.global_files if f.id != file_id]
        hive.updated_at = datetime.utcnow()
        self._save_hives()
        return hive

```

---

## 📄 backend/app/services/litellm_service.py

```py
import logging
from typing import List, Dict, Any
from ..core.config import settings
import litellm
from litellm import acompletion

logger = logging.getLogger(__name__)

async def generate_with_messages(messages: List[Dict[str, str]], config: Dict[str, Any]) -> str:
    """
    Generate a response using LiteLLM with a list of messages.
    config must contain a 'model' string in the format "provider/model" (e.g., "openai/gpt-4o").
    """
    if "model" not in config:
        raise ValueError("Missing 'model' in generation config")

    model = config["model"].replace(":", "/")  # ensure litellm format
    provider = model.split("/")[0]
    api_key = settings.secrets.get(f"PROVIDER_API_KEY_{provider.upper()}")

    litellm.api_key = api_key

    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 200)
    top_p = config.get("top_p", 1.0)

    # Log the messages being sent (for debugging)
    logger.info(f"LiteLLM call with model={model}, messages={messages}")

    try:
        response = await acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LiteLLM call failed: {e}")
        raise

```

---

## 📄 backend/app/services/redis_service.py

```py
import redis.asyncio as redis
from typing import Optional, Any, List
from ..core.config import settings
import json
import logging
import asyncio
from ..models.types import ConversationMessage
from datetime import datetime

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        self.client = None

    async def connect(self):
        self.client = await redis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
            decode_responses=True
        )
        await self.client.ping()
        return self.client

    async def wait_ready(self, max_attempts=10, delay=2):
        for i in range(max_attempts):
            try:
                await self.connect()
                logger.info("Redis is ready.")
                return
            except Exception as e:
                logger.warning(f"Redis not ready (attempt {i+1}/{max_attempts}): {e}")
                await asyncio.sleep(delay)
        raise ConnectionError("Redis unreachable after multiple attempts")

    async def publish(self, channel: str, message: dict):
        await self.client.publish(channel, json.dumps(message))

    async def set(self, key: str, value: Any, expire: Optional[int] = None):
        if expire:
            await self.client.setex(key, expire, json.dumps(value))
        else:
            await self.client.set(key, json.dumps(value))

    async def get(self, key: str) -> Optional[Any]:
        val = await self.client.get(key)
        if val:
            return json.loads(val)
        return None

    async def delete(self, key: str):
        await self.client.delete(key)

    def pubsub(self):
        return self.client.pubsub()

    # ----------------------------
    # Conversation Methods (Delta Updates)
    # ----------------------------
    async def push_conversation_message(self, agent_id: str, message: ConversationMessage):
        """Append a message to the agent's conversation list."""
        key = f"conversation:{agent_id}"
        await self.client.rpush(key, message.model_dump_json())

    async def get_conversation(self, agent_id: str, limit: int = -1) -> List[ConversationMessage]:
        """Retrieve all or last N messages from conversation."""
        key = f"conversation:{agent_id}"
        if limit > 0:
            items = await self.client.lrange(key, -limit, -1)
        else:
            items = await self.client.lrange(key, 0, -1)
        messages = []
        for item in items:
            try:
                data = json.loads(item)
                messages.append(ConversationMessage(**data))
            except Exception as e:
                logger.error(f"Failed to parse conversation message: {e}")
        return messages

    async def clear_conversation(self, agent_id: str):
        await self.client.delete(f"conversation:{agent_id}")

    async def trim_conversation(self, agent_id: str, keep_last: int = 50):
        """Keep only the last `keep_last` messages."""
        key = f"conversation:{agent_id}"
        await self.client.ltrim(key, -keep_last, -1)

redis_service = RedisService()

```

---

## 📄 backend/app/services/ws_manager.py

```py
from fastapi import WebSocket
from typing import List
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        """Send JSON string to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                # Optionally remove dead connection
                await self.disconnect(connection)

    async def disconnect_all(self):
        for connection in self.active_connections:
            try:
                await connection.close()
            except:
                pass
        self.active_connections.clear()

manager = ConnectionManager()

```

---

## 📄 backend/app/utils/__init__.py

```py
# Package init

```

---

## 📄 backend/bridges/base.py

```py
import abc
from typing import Dict, Any, Optional
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


class BaseChannelBridge(abc.ABC):
    """
    Abstract base class for all channel bridges.
    Each concrete channel bridge must implement the four abstract methods.
    """

    def __init__(self, agent_id: str, channel_config: Dict[str, Any], reasoning_config: Dict[str, Any], global_settings: Dict[str, Any]):
        """
        :param agent_id: ID of the agent this bridge instance belongs to.
        :param channel_config: The channel configuration from the agent (type, credentials, etc.).
        :param reasoning_config: The agent's reasoning configuration (model, temperature, etc.).
        :param global_settings: Global settings, e.g., PUBLIC_URL, Redis connection params.
        """
        self.agent_id = agent_id
        self.config = channel_config
        self.reasoning_config = reasoning_config
        self.global_settings = global_settings
        self.redis_client = None  # will be set by worker
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}[{agent_id}]")

    async def set_redis(self, redis_client: redis.Redis):
        """Inject the shared Redis client after construction."""
        self.redis_client = redis_client

    @abc.abstractmethod
    async def start(self):
        """
        Start the bridge instance.
        - If in webhook mode, set up the webhook listener (or register the webhook with the platform).
        - If in polling mode, start a background polling loop.
        This method should be idempotent; calling it on an already running bridge should be a no-op.
        """
        pass

    @abc.abstractmethod
    async def stop(self):
        """
        Stop the bridge instance gracefully.
        - Shut down any polling loops or webhook servers.
        """
        pass

    @abc.abstractmethod
    async def send_message(self, text: str, destination: Optional[str] = None) -> bool:
        """
        Send an outbound message to the channel.
        :param text: The message content.
        :param destination: Optional override for the destination (e.g., a specific chat ID).
                            If None, use the default from channel_config.
        :return: True if successful, False otherwise.
        """
        pass

    @abc.abstractmethod
    async def handle_incoming(self, raw_payload: Dict[str, Any]) -> None:
        """
        Process an incoming message (from webhook or polling) and trigger the agent.
        This method should publish a "think" command to the agent's Redis channel.
        """
        pass

```

---

## 📄 backend/bridges/discord.py

```py
# Placeholder for Discord bridge

```

---

## 📄 backend/bridges/init.py

```py
# Bridges package

```

---

## 📄 backend/bridges/registry.py

```py
"""
Registry for channel bridge classes.
Bridge implementations should import and call register_bridge() at module level.
"""

from typing import Dict, Type, Optional
from .base import BaseChannelBridge

_bridge_registry: Dict[str, Type[BaseChannelBridge]] = {}


def register_bridge(channel_type: str, bridge_class: Type[BaseChannelBridge]) -> None:
    """
    Register a bridge class for a given channel type.
    :param channel_type: e.g., 'telegram', 'discord', etc.
    :param bridge_class: The class implementing BaseChannelBridge.
    """
    _bridge_registry[channel_type] = bridge_class


def get_bridge_class(channel_type: str) -> Optional[Type[BaseChannelBridge]]:
    """Return the registered bridge class for the channel type, or None."""
    return _bridge_registry.get(channel_type)


def list_registered_types() -> list[str]:
    """Return a list of all registered channel types."""
    return list(_bridge_registry.keys())

```

---

## 📄 backend/bridges/slack.py

```py
# Placeholder for Slack bridge

```

---

## 📄 backend/bridges/teams.py

```py
# Placeholder for Microsoft Teams bridge

```

---

## 📄 backend/bridges/telegram.py

```py
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from datetime import datetime

from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from .base import BaseChannelBridge
from .registry import register_bridge

logger = logging.getLogger(__name__)


class TelegramBridge(BaseChannelBridge):
    def __init__(self, agent_id: str, channel_config: Dict[str, Any], reasoning_config: Dict[str, Any], global_settings: Dict[str, Any]):
        super().__init__(agent_id, channel_config, reasoning_config, global_settings)
        credentials = self.config.get("credentials", {})
        self.bot_token = credentials.get("botToken") or credentials.get("bot_token") or credentials.get("token")
        self.chat_id = credentials.get("chatId") or credentials.get("chat_id") or credentials.get("chat")

        if not self.bot_token:
            raise ValueError(f"Telegram bridge for agent {agent_id}: missing bot_token")

        self.bot = Bot(token=self.bot_token)
        self.application = None
        self.polling_task = None

    async def start(self):
        """Start the bridge – webhook if PUBLIC_URL is HTTPS, otherwise polling."""
        public_url = self.global_settings.get("PUBLIC_URL")
        if public_url:
            parsed = urlparse(public_url)
            if parsed.scheme == "https":
                # Use webhook mode (Telegram requires HTTPS)
                self.logger.info("Starting Telegram bridge in webhook mode (HTTPS detected)")
                webhook_base = f"{parsed.scheme}://{parsed.hostname}:8081"
                webhook_url = f"{webhook_base}/webhook/{self.agent_id}"
                await self.bot.set_webhook(url=webhook_url)
                self.logger.info(f"Registered webhook: {webhook_url}")
                return
            else:
                self.logger.info("PUBLIC_URL is not HTTPS, falling back to polling mode")
        else:
            self.logger.info("No PUBLIC_URL set, using polling mode")

        # Polling mode
        self.logger.info("Starting Telegram bridge in polling mode")
        self.application = Application.builder().token(self.bot_token).build()
        self.application.add_handler(MessageHandler(filters.ALL, self._polling_handler))
        await self.application.initialize()
        await self.application.start()
        self.polling_task = asyncio.create_task(self.application.updater.start_polling())

    async def stop(self):
        """Stop the bridge."""
        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        # Only delete webhook if we were in webhook mode
        if self.global_settings.get("PUBLIC_URL") and urlparse(self.global_settings["PUBLIC_URL"]).scheme == "https":
            try:
                await self.bot.delete_webhook()
            except Exception as e:
                self.logger.warning(f"Failed to delete webhook: {e}")

    async def send_message(self, text: str, destination: Optional[str] = None) -> bool:
        """Send a message to the default chat or specified destination."""
        chat_id = destination or self.chat_id
        if not chat_id:
            self.logger.error("No chatId configured for outbound message")
            return False
        try:
            await self.bot.send_message(chat_id=chat_id, text=text)
            return True
        except Exception as e:
            self.logger.exception(f"Failed to send message: {e}")
            return False

    async def handle_incoming(self, raw_payload: Dict[str, Any]) -> None:
        """Called by webhook server with the incoming update JSON."""
        try:
            update = Update.de_json(raw_payload, self.bot)
            await self._process_update(update)
        except Exception as e:
            self.logger.exception("Error processing incoming update")

    async def _polling_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for polling mode."""
        await self._process_update(update)

    async def _process_update(self, update: Update):
        """Process incoming message – send think command to agent."""
        if not update.message or not update.message.text:
            return
        user_input = update.message.text
        chat_id = update.message.chat_id

        # Prepare think command
        think_command = {
            "type": "think",
            "input": user_input,
            "config": self.reasoning_config,
            "timestamp": datetime.utcnow().isoformat()
        }
        # Publish to agent's command channel
        if self.redis_client:
            await self.redis_client.publish(f"agent:{self.agent_id}", json.dumps(think_command))
            self.logger.info(f"Forwarded incoming message from chat {chat_id} to agent {self.agent_id}")
        else:
            self.logger.warning("Redis client not set; cannot forward incoming message")


# Register this bridge
register_bridge("telegram", TelegramBridge)

```

---

## 📄 backend/bridges/whatsapp.py

```py
# Placeholder for WhatsApp bridge

```

---

## 📄 backend/bridges/worker.py

```py
#!/usr/bin/env python3
"""
Generic bridge worker for a specific channel type.
This script is intended to be run as a standalone Docker service.
It expects environment variables:
    - CHANNEL_TYPE (required)
    - REDIS_HOST (default: redis)
    - REDIS_PORT (default: 6379)
    - PUBLIC_URL (optional, for webhook mode)
    - BACKEND_API_URL (default: http://backend:8000/api/v1)
    - INTERNAL_API_KEY (required, to authenticate with backend)
    - WEBHOOK_PORT (default: 8080)
"""

import os
import asyncio
import json
import logging
import signal
import pkgutil
import importlib
import sys
from typing import Dict, Optional

import redis.asyncio as redis
import httpx
from fastapi import FastAPI, Request, HTTPException
import uvicorn

from .registry import get_bridge_class, register_bridge
from .base import BaseChannelBridge

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(f"bridge-worker-{os.getenv('CHANNEL_TYPE', 'unknown')}")

# Auto-import all bridge modules
try:
    import bridges
    imported_modules = []
    for _, module_name, _ in pkgutil.iter_modules(bridges.__path__):
        if module_name not in ("base", "registry", "worker"):
            try:
                importlib.import_module(f"bridges.{module_name}")
                imported_modules.append(module_name)
                logger.info(f"Auto-imported bridge module: {module_name}")
            except Exception as e:
                logger.error(f"Failed to import bridges.{module_name}: {e}")
    if imported_modules:
        logger.info(f"Successfully imported modules: {imported_modules}")
except Exception as e:
    logger.exception(f"Error during bridge auto-import: {e}")

# Environment
CHANNEL_TYPE = os.getenv("CHANNEL_TYPE")
if not CHANNEL_TYPE:
    raise ValueError("CHANNEL_TYPE environment variable is required")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
PUBLIC_URL = os.getenv("PUBLIC_URL")  # may be None
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000/api/v1")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
if not INTERNAL_API_KEY:
    raise ValueError("INTERNAL_API_KEY environment variable is required")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))

# Try to get the bridge class for this channel type
bridge_class = get_bridge_class(CHANNEL_TYPE)
if bridge_class is None:
    logger.error(f"No bridge registered for channel type {CHANNEL_TYPE}")
    sys.exit(1)

# Global state
redis_client: Optional[redis.Redis] = None
active_bridges: Dict[str, BaseChannelBridge] = {}  # agent_id -> bridge instance
shutdown_event = asyncio.Event()
webhook_server_task: Optional[asyncio.Task] = None


async def fetch_agents_with_channel() -> list[dict]:
    """Fetch all agents that have this channel type enabled."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BACKEND_API_URL}/agents",
            params={"channel_type": CHANNEL_TYPE},
            headers={"Authorization": f"Bearer {INTERNAL_API_KEY}"}
        )
        resp.raise_for_status()
        data = resp.json()
        return data


async def apply_config(agents: list[dict]):
    """
    Synchronize active bridges with the list of agents.
    - For each agent, if a bridge exists, update its config.
    - If a bridge does not exist, create and start it.
    - Remove bridges for agents no longer in the list.
    """
    global active_bridges
    bridge_class = get_bridge_class(CHANNEL_TYPE)
    if not bridge_class:
        logger.error(f"No bridge registered for channel type {CHANNEL_TYPE}")
        return

    current_ids = set()
    for agent_data in agents:
        agent_id = agent_data["id"]
        current_ids.add(agent_id)

        channels = agent_data.get("channels", [])
        channel_config = next((ch for ch in channels if ch.get("type") == CHANNEL_TYPE and ch.get("enabled")), None)
        if not channel_config:
            logger.warning(f"Agent {agent_id} has no enabled {CHANNEL_TYPE} channel, skipping")
            continue

        reasoning_config = agent_data.get("reasoning", {})
        global_settings = {
            "PUBLIC_URL": PUBLIC_URL,
            "REDIS_HOST": REDIS_HOST,
            "REDIS_PORT": REDIS_PORT,
        }

        if agent_id in active_bridges:
            bridge = active_bridges[agent_id]
            if bridge.config != channel_config or bridge.reasoning_config != reasoning_config:
                logger.info(f"Agent {agent_id} config changed, restarting bridge")
                await bridge.stop()
                try:
                    new_bridge = bridge_class(agent_id, channel_config, reasoning_config, global_settings)
                    await new_bridge.set_redis(redis_client)
                    await new_bridge.start()
                    active_bridges[agent_id] = new_bridge
                except Exception as e:
                    logger.error(f"Failed to create bridge for agent {agent_id}: {e}")
                    # Remove from active_bridges if it was there before
                    if agent_id in active_bridges:
                        del active_bridges[agent_id]
        else:
            try:
                logger.info(f"Creating new {CHANNEL_TYPE} bridge for agent {agent_id}")
                bridge = bridge_class(agent_id, channel_config, reasoning_config, global_settings)
                await bridge.set_redis(redis_client)
                await bridge.start()
                active_bridges[agent_id] = bridge
            except Exception as e:
                logger.error(f"Failed to create bridge for agent {agent_id}: {e}")

    # Remove bridges for agents no longer present or disabled
    to_remove = set(active_bridges.keys()) - current_ids
    for agent_id in to_remove:
        logger.info(f"Stopping bridge for agent {agent_id} (no longer enabled)")
        bridge = active_bridges[agent_id]
        await bridge.stop()
        del active_bridges[agent_id]


async def listen_for_config_updates():
    """
    Subscribe to Redis channel `config:bridge:<CHANNEL_TYPE>`.
    When a message arrives, re-fetch agents and apply config.
    """
    pubsub = redis_client.pubsub()
    channel = f"config:bridge:{CHANNEL_TYPE}"
    await pubsub.subscribe(channel)
    logger.info(f"Subscribed to {channel}")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            data = json.loads(message["data"])
            logger.info(f"Config update received on {channel}, reloading agents")
            agents = await fetch_agents_with_channel()
            await apply_config(agents)
        except Exception as e:
            logger.exception(f"Error processing config update: {e}")


async def start_webhook_server():
    """Start FastAPI server to handle incoming webhooks."""
    app = FastAPI(title=f"Bridge Webhook - {CHANNEL_TYPE}")

    @app.post("/webhook/{agent_id}")
    async def handle_webhook(agent_id: str, request: Request):
        bridge = active_bridges.get(agent_id)
        if not bridge:
            raise HTTPException(status_code=404, detail="Agent not found")
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON")
        await bridge.handle_incoming(payload)
        return {"ok": True}

    config = uvicorn.Config(app, host="0.0.0.0", port=WEBHOOK_PORT, log_level="warning")
    server = uvicorn.Server(config)
    logger.info(f"Starting webhook server on port {WEBHOOK_PORT}")
    await server.serve()


async def main_loop():
    """Main worker loop."""
    global redis_client, webhook_server_task
    redis_client = await redis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)
    logger.info("Connected to Redis")

    # Initial load
    agents = await fetch_agents_with_channel()
    await apply_config(agents)

    # Start listening for config updates
    config_task = asyncio.create_task(listen_for_config_updates())

    # Start webhook server if PUBLIC_URL is set
    if PUBLIC_URL:
        webhook_server_task = asyncio.create_task(start_webhook_server())
    else:
        logger.info("PUBLIC_URL not set, webhook server disabled (polling only)")

    # Subscribe to report:owner to forward outbound messages
    pubsub_out = redis_client.pubsub()
    await pubsub_out.subscribe("report:owner")
    logger.info("Subscribed to report:owner")

    async for msg in pubsub_out.listen():
        if msg["type"] != "message":
            continue
        try:
            data = json.loads(msg["data"])
            agent_id = data.get("agent_id")
            response = data.get("response")
            if not agent_id or not response:
                continue
            bridge = active_bridges.get(agent_id)
            if bridge:
                await bridge.send_message(response)
            else:
                logger.debug(f"No active bridge for agent {agent_id} (message ignored)")
        except Exception as e:
            logger.exception("Error processing outbound message")

    # Wait for shutdown signal
    await shutdown_event.wait()
    config_task.cancel()
    if webhook_server_task:
        webhook_server_task.cancel()
    for bridge in active_bridges.values():
        await bridge.stop()
    await redis_client.close()


def handle_shutdown(sig, frame):
    logger.info(f"Received signal {sig}, shutting down...")
    shutdown_event.set()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    asyncio.run(main_loop())

```

---

## 📄 backend/requirements.txt

```txt
fastapi==0.115.12
uvicorn[standard]==0.34.0
docker==7.1.0
redis==5.2.1
litellm==1.63.2
cryptography==44.0.2
pydantic==2.10.6
pydantic-settings==2.7.1
python-dotenv==1.0.1
python-multipart==0.0.20

```

---

## 📄 backend/scripts/__init__.py

```py
# Package init

```

---

## 📄 data/data/hives.json

```json
{
  "h-d725": {
    "id": "h-d725",
    "name": "Main Hive",
    "description": "Primary cluster for bot orchestration",
    "agents": [],
    "globalUserMd": "",
    "globalUid": "1001",
    "globalApiKey": "",
    "messages": [],
    "globalFiles": [],
    "hiveMindConfig": {
      "access_level": "ISOLATED",
      "shared_hive_ids": []
    },
    "createdAt": "2026-03-03T11:09:34.914331",
    "updatedAt": "2026-03-03T11:09:34.914331"
  },
  "h-ef0f": {
    "id": "h-ef0f",
    "name": "New Hive",
    "description": "Autonomous bot orchestration hive",
    "agents": [],
    "globalUserMd": "",
    "globalUid": "1001",
    "globalApiKey": "",
    "messages": [],
    "globalFiles": [],
    "hiveMindConfig": {
      "access_level": "ISOLATED",
      "shared_hive_ids": []
    },
    "createdAt": "2026-03-03T11:26:06.804170",
    "updatedAt": "2026-03-03T11:26:06.804170"
  },
  "h-3e38": {
    "id": "h-3e38",
    "name": "New Hive",
    "description": "Autonomous bot orchestration hive",
    "agents": [],
    "globalUserMd": "",
    "globalUid": "1001",
    "globalApiKey": "",
    "messages": [],
    "globalFiles": [],
    "hiveMindConfig": {
      "access_level": "ISOLATED",
      "shared_hive_ids": []
    },
    "createdAt": "2026-03-03T11:26:14.964040",
    "updatedAt": "2026-03-03T11:26:14.964040"
  }
}
```

---

## 📄 docker/agent/agent_worker.py

```py
import os
import json
import redis
import requests
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_worker")

AGENT_ID = os.environ.get("AGENT_ID")
PARENT_ID = os.environ.get("PARENT_ID")                      # fallback only
REPORTING_TARGET = os.environ.get("REPORTING_TARGET", "PARENT_AGENT")  # fallback only
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY")
ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://backend:8000")

DATA_DIR = Path("/data")
SOUL_PATH = DATA_DIR / "soul.md"
IDENTITY_PATH = DATA_DIR / "identity.md"
TOOLS_PATH = DATA_DIR / "tools.md"

def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def load_agent_files():
    return {
        "soul": read_file(SOUL_PATH),
        "identity": read_file(IDENTITY_PATH),
        "tools": read_file(TOOLS_PATH),
    }

def call_ai_delta(agent_id, user_input, model_config):
    """Call orchestrator's delta AI endpoint."""
    url = f"{ORCHESTRATOR_URL}/api/v1/internal/ai/generate-delta"
    headers = {
        "Authorization": f"Bearer {INTERNAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "agent_id": agent_id,
        "input": user_input,
        "config": model_config
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json()["response"]
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        return f"Error: {str(e)}"

def get_agent_config():
    """Fetch the current agent configuration from the orchestrator."""
    url = f"{ORCHESTRATOR_URL}/api/v1/agents/{AGENT_ID}"
    headers = {"Authorization": f"Bearer {INTERNAL_API_KEY}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        config = resp.json()
        logger.info(f"Fetched live config for {AGENT_ID}: reportingTarget={config.get('reportingTarget')}, parentId={config.get('parentId')}")
        return config
    except Exception as e:
        logger.error(f"Failed to fetch agent config: {e}")
        return None

def main():
    logger.info(f"Agent {AGENT_ID} starting...")
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    pubsub = r.pubsub()
    channel = f"agent:{AGENT_ID}"
    pubsub.subscribe(channel)
    logger.info(f"Subscribed to {channel}")
    
    agent_files = load_agent_files()
    
    for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            data = json.loads(message["data"])
            cmd = data.get("type")
            if cmd == "think":
                logger.info("Received think command")
                user_input = data.get("input", "")
                model_config = data.get("config", {})

                # Call AI using delta endpoint
                response = call_ai_delta(AGENT_ID, user_input, model_config)

                # --- Get current agent configuration ---
                agent_config = get_agent_config()
                if agent_config is None:
                    # Fall back to environment variables (original container config)
                    logger.warning("Using fallback reporting target from environment")
                    current_parent_id = PARENT_ID
                    current_reporting = REPORTING_TARGET
                else:
                    current_parent_id = agent_config.get("parentId")
                    current_reporting = agent_config.get("reportingTarget", "PARENT_AGENT")

                # Determine reporting channels based on current config
                channels_to_publish = []
                if current_reporting == "PARENT_AGENT" and current_parent_id:
                    channels_to_publish.append(f"report:parent:{current_parent_id}")
                elif current_reporting == "OWNER_DIRECT":
                    channels_to_publish.append("report:owner")
                elif current_reporting == "HYBRID":
                    if current_parent_id:
                        channels_to_publish.append(f"report:parent:{current_parent_id}")
                    channels_to_publish.append("report:owner")
                else:
                    # Fallback: always publish to owner if unknown
                    channels_to_publish.append("report:owner")

                result = {
                    "agent_id": AGENT_ID,
                    "response": response,
                    "timestamp": data.get("timestamp", "")
                }

                for ch in channels_to_publish:
                    r.publish(ch, json.dumps(result))
                    logger.info(f"Published result to {ch}")

            else:
                logger.warning(f"Unknown command: {cmd}")
        except Exception as e:
            logger.exception("Error processing message")

if __name__ == "__main__":
    main()

```

---

## 📄 docker/agent/requirements.txt

```txt
redis==5.2.1
requests==2.32.3

```

---

## 📄 docker/nginx.conf

```conf
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

```

---

## 📄 docker-compose.yml

```yml
services:
  agent-builder:
    build:
      context: .
      dockerfile: docker/agent/Dockerfile
    image: hivebot/agent:latest
    container_name: hivebot_agent_builder
    profiles: ["tools"]

  redis:
    image: redis:7-alpine
    container_name: hivebot_redis
    restart: unless-stopped
    command: redis-server --save 60 1 --loglevel warning
    volumes:
      - redis_data:/data
    networks:
      - hivebot_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: docker/backend.Dockerfile
    image: hivebot/backend:latest
    container_name: hivebot_backend
    restart: unless-stopped
    user: "0:0"
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - ENVIRONMENT=production
      - REDIS_HOST=redis
      - HIVEBOT_DATA=/app/data
      - DOCKER_NETWORK=hivebot_network
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./agents:/app/data/agents
      - hivebot_secrets:/app/data/secrets
      - ./global_files:/app/data/global_files
      - ./data:/app/data
      - ./.env:/app/.env
    networks:
      - hivebot_network
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

  frontend:
    build:
      context: .
      dockerfile: docker/frontend.Dockerfile
    image: hivebot/frontend:latest
    container_name: hivebot_frontend
    restart: unless-stopped
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - hivebot_network
    ports:
      - "8080:80"

  bridge-base:
    build:
      context: .
      dockerfile: docker/bridge-base.Dockerfile
    image: hivebot/bridge-base:latest
    container_name: hivebot_bridge_base
    profiles: ["tools"]

  bridge-telegram:
    build:
      context: .
      dockerfile: docker/bridge-telegram.Dockerfile
    image: hivebot/bridge-telegram:latest
    container_name: hivebot_bridge_telegram
    restart: "no"
    depends_on:
      - redis
      - backend
    env_file:
      - ./bridges.env
    environment:
      - CHANNEL_TYPE=telegram
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - BACKEND_API_URL=http://backend:8000/api/v1
      - WEBHOOK_PORT=8080
    networks:
      - hivebot_network
    ports:
      - "8081:8080"

  bridge-discord:
    build:
      context: .
      dockerfile: docker/bridge-discord.Dockerfile
    image: hivebot/bridge-discord:latest
    container_name: hivebot_bridge_discord
    restart: "no"
    depends_on:
      - redis
      - backend
    env_file:
      - ./bridges.env
    environment:
      - CHANNEL_TYPE=discord
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - BACKEND_API_URL=http://backend:8000/api/v1
      - WEBHOOK_PORT=8080
    networks:
      - hivebot_network
    ports:
      - "8082:8080"

  bridge-slack:
    build:
      context: .
      dockerfile: docker/bridge-slack.Dockerfile
    image: hivebot/bridge-slack:latest
    container_name: hivebot_bridge_slack
    restart: "no"
    depends_on:
      - redis
      - backend
    env_file:
      - ./bridges.env
    environment:
      - CHANNEL_TYPE=slack
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - BACKEND_API_URL=http://backend:8000/api/v1
      - WEBHOOK_PORT=8080
    networks:
      - hivebot_network
    ports:
      - "8083:8080"

  bridge-whatsapp:
    build:
      context: .
      dockerfile: docker/bridge-whatsapp.Dockerfile
    image: hivebot/bridge-whatsapp:latest
    container_name: hivebot_bridge_whatsapp
    restart: "no"
    depends_on:
      - redis
      - backend
    env_file:
      - ./bridges.env
    environment:
      - CHANNEL_TYPE=whatsapp
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - BACKEND_API_URL=http://backend:8000/api/v1
      - WEBHOOK_PORT=8080
    networks:
      - hivebot_network
    ports:
      - "8084:8080"

  bridge-teams:
    build:
      context: .
      dockerfile: docker/bridge-teams.Dockerfile
    image: hivebot/bridge-teams:latest
    container_name: hivebot_bridge_teams
    restart: "no"
    depends_on:
      - redis
      - backend
    env_file:
      - ./bridges.env
    environment:
      - CHANNEL_TYPE=teams
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - BACKEND_API_URL=http://backend:8000/api/v1
      - WEBHOOK_PORT=8080
    networks:
      - hivebot_network
    ports:
      - "8085:8080"

networks:
  hivebot_network:
    name: hivebot_network  # Explicitly set name to avoid project prefix
    driver: bridge

volumes:
  redis_data:
  hivebot_secrets:
    driver: local
    driver_opts:
      type: none
      device: ./secrets
      o: bind

```

---

## 📄 frontend/README.md

```md

# 🛡️ ZikoraNode v2 Deployment Guide

ZikoraNode is an enterprise-grade agent orchestrator. Follow this guide to deploy your instance to a production VPS.

## 🚀 Quick Start (Automated)

The easiest way to get ZikoraNode running on a clean Ubuntu 22.04+ VPS:

```bash
# 1. Update and install Docker
sudo apt update && sudo apt install -y docker.io docker-compose

# 2. Clone the repository
git clone https://github.com/your-username/zikoranode.git
cd zikoranode

# 3. Configure your environment
echo "GEMINI_API_KEY=your_actual_key_here" > .env

# 4. Spin up the production container
sudo docker-compose up -d --build
```

---

## 🛠️ Detailed Production Setup

### 1. VPS Requirements
- **OS:** Ubuntu 22.04 LTS (Recommended)
- **RAM:** 1GB Minimum (2GB Recommended)
- **CPU:** 1 Core
- **Disk:** 10GB Free Space

### 2. Environment Configuration
The application uses **Vite** to bundle your environment variables into the static build.
1. Create a `.env` file in the root directory.
2. Add your global key: `GEMINI_API_KEY=AIza...`
3. If you want to use per-agent keys, you can define them directly within the app UI once it is running.

### 3. Domain & SSL (Recommended for Production)
To serve ZikoraNode over HTTPS (port 443), we recommend using **Caddy** or **Certbot**.

**Using Certbot with Nginx (on the host):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### 4. Security Best Practices
- **Firewall:** Only keep ports 80, 443, and 22 (SSH) open.
  `sudo ufw allow 80,443,22/tcp && sudo ufw enable`
- **Secrets:** Never commit your `.env` file to version control.
- **UID Isolation:** ZikoraNode simulates UID isolation. Ensure your server user has restricted permissions.

### 5. Managing the Application
- **View Logs:** `sudo docker logs -f zikoranode_app`
- **Stop App:** `sudo docker-compose down`
- **Update App:**
  ```bash
  git pull
  sudo docker-compose up -d --build
  ```

---

## 🏗️ Folder Structure
- `/dist`: Built static assets (after `npm run build`).
- `/nginx.conf`: Directs all traffic to `index.html` (required for React Router).
- `/Dockerfile`: Orchestrates the Node-to-Nginx pipeline.

## 🆘 Troubleshooting
- **404 on Refresh:** Ensure `nginx.conf` includes the `try_files` directive.
- **API Key Not Working:** Verify that the key is correctly set in `.env` *before* running the build stage in Docker.
- **Port 80 Conflict:** Ensure no other web server (like a default Apache) is running on the host.

---
*Maintained by the Zikora Engineering Team.*

```

---

## 📄 frontend/docker-compose.yml

```yml

services:
  zikoranode:
    build: .
    container_name: zikoranode_app
    ports:
      - "80:80"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    restart: always

```

---

## 📄 frontend/index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HiveBot Orchestrator</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Fira+Code:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/src/index.css">
</head>
<body>
    <div id="root"></div>
    <script type="module" src="/src/index.tsx"></script>
</body>
</html>

```

---

## 📄 frontend/metadata.json

```json

{
  "name": "ZikoraNode v2 - Pro Orchestrator",
  "description": "Enterprise-grade multi-agent mesh with hierarchical reporting, isolated pod sandboxing, and production-ready communication relays for Telegram, Discord, and Slack.",
  "requestFramePermissions": [
    "camera",
    "microphone"
  ]
}

```

---

## 📄 frontend/nginx.conf

```conf

server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # Cache control for static assets
    location /assets/ {
        root /usr/share/nginx/html;
        expires 1y;
        add_header Cache-Control "public, no-transform";
    }

    # Error handling
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}

```

---

## 📄 frontend/package.json

```json
{
  "name": "hivebot-frontend",
  "private": true,
  "version": "0.0.1",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@google/genai": "^1.40.0",
    "framer-motion": "^11.0.0",
    "react": "^19.2.4",
    "react-dom": "^19.2.4",
    "recharts": "^3.7.0"
  },
  "devDependencies": {
    "@types/node": "^22.14.0",
    "@vitejs/plugin-react": "^5.0.0",
    "autoprefixer": "10.4.18",
    "postcss": "8.4.35",
    "tailwindcss": "3.4.1",
    "typescript": "~5.8.2",
    "vite": "^6.2.0"
  }
}

```

---

## 📄 frontend/postcss.config.js

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}

```

---

## 📄 frontend/src/App.tsx

```tsx
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Agent, AgentStatus, ReportingTarget, Message, FileEntry, AgentCreate, Hive, HiveCreate, HiveUpdate, HiveMindConfig, HiveMindAccessLevel, UserAccount, GlobalSettings, UserRole } from './types';
import { INITIAL_SOUL, INITIAL_IDENTITY, INITIAL_TOOLS, INITIAL_USER_MD, Icons } from './constants';
import { Sidebar } from './components/Sidebar';
import { AgentGrid } from './components/AgentGrid';
import { AgentDetails } from './components/AgentDetails';
import { GlobalStats } from './components/GlobalStats';
import { GlobalFiles } from './components/GlobalFiles';
import { AIProviderConfig } from './components/AIProviderConfig';
import { PublicUrlConfig } from './components/PublicUrlConfig';
import { BridgeManager } from './components/BridgeManager';
import { Dashboard } from './components/Dashboard';
import { HiveMindDashboard } from './components/HiveMindDashboard';
import { GlobalConfig } from './components/GlobalConfig';
import { HiveTeam } from './components/HiveTeam';
import { LoginPage } from './components/LoginPage';
import { orchestratorService } from './services/orchestratorService';
import { wsService } from './services/websocketService';
import { ProviderProvider, useProviders } from './contexts/ProviderContext';
import { BridgeProvider } from './contexts/BridgeContext';

const AppContent: React.FC = () => {
  const [user, setUser] = useState<string | null>(() => {
    return localStorage.getItem('hivebot_user');
  });

  const [hives, setHives] = useState<Hive[]>([]);
  const [activeHiveId, setActiveHiveId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  
  const [users, setUsers] = useState<UserAccount[]>([]);
  const [globalSettings, setGlobalSettings] = useState<GlobalSettings>({
    loginEnabled: true,
    sessionTimeout: 30,
    systemName: 'HiveBot Orchestrator',
    maintenanceMode: false
  });

  const { getPrimaryModel, refreshProviders } = useProviders();

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      if (!user) {
        setLoading(false);
        return;
      }

      try {
        setLoadError(null);
        
        // Try to load hives
        let hivesData: Hive[] = [];
        try {
          hivesData = await orchestratorService.listHives();
        } catch (err) {
          console.warn('Could not fetch hives, will create default', err);
        }
        
        if (hivesData.length === 0) {
          // Create default hive if none exist
          try {
            const defaultHive = await orchestratorService.createHive({
              name: 'Main Hive',
              description: 'Primary cluster for bot orchestration',
              globalUserMd: INITIAL_USER_MD,
              globalUid: "1001",
              globalApiKey: ""
            });
            hivesData = [defaultHive];
          } catch (err) {
            console.error('Failed to create default hive', err);
            setLoadError('Could not initialize hive. Please check backend connection.');
            setLoading(false);
            return;
          }
        }
        
        setHives(hivesData);
        
        // Set active hive from localStorage or first hive
        const savedActive = localStorage.getItem('hivebot_active_hive');
        if (savedActive && hivesData.some(h => h.id === savedActive)) {
          setActiveHiveId(savedActive);
        } else {
          setActiveHiveId(hivesData[0].id);
        }

        // Load providers in background
        refreshProviders().catch(err => 
          console.warn('Could not load providers', err)
        );

      } catch (err) {
        console.error('Failed to load initial data', err);
        setLoadError('Failed to connect to backend. Please check server status.');
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, [user, refreshProviders]);

  // Save active hive to localStorage
  useEffect(() => {
    if (activeHiveId) {
      localStorage.setItem('hivebot_active_hive', activeHiveId);
    }
  }, [activeHiveId]);

  const activeHive = useMemo(() => 
    hives.find(h => h.id === activeHiveId) || hives[0]
  , [hives, activeHiveId]);

  const [view, setView] = useState<'dashboard' | 'cluster' | 'agent' | 'context' | 'setup' | 'hive-mind' | 'global-config' | 'team'>('dashboard');
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const agents = activeHive?.agents || [];
  const globalUserMd = activeHive?.globalUserMd || INITIAL_USER_MD;
  const globalUid = activeHive?.globalUid || "1001";
  const globalApiKey = activeHive?.globalApiKey || "";
  const messages = activeHive?.messages || [];
  const globalFiles = activeHive?.globalFiles || [];

  const updateHive = async (hiveId: string, updates: HiveUpdate) => {
    try {
      const updated = await orchestratorService.updateHive(hiveId, updates);
      setHives(prev => prev.map(h => h.id === hiveId ? updated : h));
      return updated;
    } catch (err) {
      console.error('Failed to update hive', err);
      throw err;
    }
  };

  const handleUpdateAgent = async (updated: Agent) => {
    if (!activeHiveId) return;
    try {
      const result = await orchestratorService.updateHiveAgent(activeHiveId, updated.id, updated);
      setHives(prev => prev.map(h => 
        h.id === activeHiveId 
          ? { ...h, agents: h.agents.map(a => a.id === updated.id ? result : a) }
          : h
      ));
    } catch (err) {
      console.error('Update failed', err);
    }
  };

  const handleCreateAgent = async () => {
    if (!activeHiveId) return;
    const primaryModel = getPrimaryModel();
    if (!primaryModel) {
      alert('No primary AI model configured. Please set up a provider and primary model in Environment first.');
      return;
    }

    const newAgent: Agent = {
      id: `b-${Math.random().toString(36).substr(2, 4)}`,
      name: 'New HiveBot',
      role: 'Worker',
      soulMd: INITIAL_SOUL,
      identityMd: INITIAL_IDENTITY,
      toolsMd: INITIAL_TOOLS,
      status: AgentStatus.IDLE,
      reasoning: {
        model: `${primaryModel.provider}:${primaryModel.modelId}`,
        temperature: 0.7,
        topP: 1.0,
        maxTokens: 150,
        use_global_default: true,
        use_custom_max_tokens: false,
      },
      reportingTarget: ReportingTarget.PARENT,
      parentId: agents.length > 0 ? agents[0].id : undefined,
      subAgentIds: [],
      channels: [],
      memory: { shortTerm: [], summary: 'Awaiting first cycle', tokenCount: 0 },
      lastActive: new Date().toISOString(),
      containerId: `bid-${Math.floor(Math.random() * 9999)}`,
      userUid: globalUid,
      localFiles: []
    };

    try {
      const created = await orchestratorService.addAgentToHive(activeHiveId, newAgent);
      setHives(prev => prev.map(h => 
        h.id === activeHiveId 
          ? { ...h, agents: [...h.agents, created] }
          : h
      ));
      setSelectedAgentId(created.id);
      setView('agent');
      setIsSidebarOpen(false);
    } catch (err) {
      console.error('Create failed', err);
    }
  };

  const handleDeleteAgent = async (agentId: string) => {
    if (!activeHiveId) return;
    try {
      await orchestratorService.removeAgentFromHive(activeHiveId, agentId);
      setHives(prev => prev.map(h => 
        h.id === activeHiveId 
          ? { ...h, agents: h.agents.filter(a => a.id !== agentId) }
          : h
      ));
      if (selectedAgentId === agentId) {
        setSelectedAgentId(null);
        setView('cluster');
      }
    } catch (err) {
      console.error('Delete failed', err);
    }
  };

  const handleCreateHive = async () => {
    try {
      const newHive = await orchestratorService.createHive({
        name: 'New Hive',
        description: 'Autonomous bot orchestration hive',
        globalUserMd: INITIAL_USER_MD,
        globalUid: "1001",
        globalApiKey: ""
      });
      setHives(prev => [...prev, newHive]);
      setActiveHiveId(newHive.id);
      setView('dashboard');
      setSelectedAgentId(null);
      setIsSidebarOpen(false);
    } catch (err) {
      console.error('Failed to create hive', err);
    }
  };

  const handleDeleteHive = async (id: string) => {
    if (hives.length <= 1) {
      alert('Cannot delete the last hive');
      return;
    }
    try {
      await orchestratorService.deleteHive(id);
      setHives(prev => {
        const filtered = prev.filter(h => h.id !== id);
        if (activeHiveId === id && filtered.length > 0) {
          setActiveHiveId(filtered[0].id);
        }
        return filtered;
      });
    } catch (err) {
      console.error('Failed to delete hive', err);
    }
  };

  const runAgent = async (agentId: string) => {
    try {
      setHives(prev => prev.map(h => 
        h.id === activeHiveId 
          ? { 
              ...h, 
              agents: h.agents.map(a => 
                a.id === agentId ? { ...a, status: AgentStatus.RUNNING } : a
              )
            }
          : h
      ));
      
      addLog(agentId, `Initiating Hive Cycle...`, 'internal');
      
      await orchestratorService.executeAgent(agentId);
    } catch (err: any) {
      addLog(agentId, `HIVE_FAULT: ${err.message}`, 'error');
      setHives(prev => prev.map(h => 
        h.id === activeHiveId 
          ? { 
              ...h, 
              agents: h.agents.map(a => 
                a.id === agentId ? { ...a, status: AgentStatus.ERROR } : a
              )
            }
          : h
      ));
    }
  };

  const addLog = useCallback((agentId: string, content: string, type: Message['type'] = 'log', channelId?: string) => {
    if (!activeHiveId) return;
    const newMessage: Message = {
      id: Math.random().toString(36).substr(2, 9),
      from: agentId,
      to: 'system',
      content,
      timestamp: new Date().toISOString(),
      type,
      channelId
    };
    
    // Update local state optimistically
    setHives(prev => prev.map(h => 
      h.id === activeHiveId 
        ? { 
            ...h, 
            messages: [newMessage, ...h.messages].slice(0, 100)
          }
        : h
    ));
    
    // Save to backend
    orchestratorService.addMessageToHive(activeHiveId, newMessage).catch(console.error);
  }, [activeHiveId]);

  const handleSelectHive = (id: string) => {
    setActiveHiveId(id);
    setView('dashboard');
    setSelectedAgentId(null);
    setIsSidebarOpen(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('hivebot_user');
    setUser(null);
    setHives([]);
    setActiveHiveId(null);
  };

  const handleLogin = (username: string) => {
    localStorage.setItem('hivebot_user', username);
    setUser(username);
  };

  const handleValidateLogin = (username: string, pass: string) => {
    // For now, simple validation - will be replaced with proper auth in Phase 3
    return username === 'admin' && pass === 'hive2026';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-zinc-950">
        <div className="text-center">
          <div className="text-emerald-500 text-2xl font-black mb-4 animate-pulse">HiveBot</div>
          <div className="text-zinc-500">Loading hive intelligence...</div>
          {loadError && (
            <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm max-w-md">
              {loadError}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (!user && globalSettings.loginEnabled) {
    return <LoginPage onLogin={handleLogin} onValidate={handleValidateLogin} />;
  }

  return (
    <div className="flex h-screen bg-zinc-950 overflow-hidden select-none text-zinc-100 font-sans relative">
      <div className={`fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity lg:hidden ${isSidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`} onClick={() => setIsSidebarOpen(false)} />
      
      <div className={`fixed lg:relative inset-y-0 left-0 z-50 transform transition-transform duration-300 lg:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <Sidebar 
          agents={agents} 
          hives={hives}
          activeHiveId={activeHiveId || ''}
          onSelectHive={handleSelectHive}
          onCreateHive={handleCreateHive}
          onDeleteHive={handleDeleteHive}
          selectedId={selectedAgentId} 
          onSelect={(id) => { setSelectedAgentId(id); setView(id ? 'agent' : 'cluster'); setIsSidebarOpen(false); }} 
          onCreate={handleCreateAgent}
          onDelete={handleDeleteAgent}
          isCreating={false}
          currentView={view}
          onViewChange={(v) => { setView(v); setIsSidebarOpen(false); }}
          onClose={() => setIsSidebarOpen(false)}
        />
      </div>

      <main className="flex-1 flex flex-col overflow-hidden relative">
        {['dashboard', 'cluster', 'agent', 'context', 'setup', 'hive-mind', 'team'].includes(view) && (
          <header className="h-16 border-b border-zinc-800 flex items-center justify-between px-4 md:px-8 bg-zinc-950/90 backdrop-blur-md sticky top-0 z-20">
            <div className="flex items-center gap-3 md:gap-4">
              <button onClick={() => setIsSidebarOpen(true)} className="lg:hidden p-2 text-zinc-400 hover:text-white transition-colors">
                <Icons.Menu />
              </button>
              <div className="p-1.5 md:p-2 bg-emerald-500/10 text-emerald-500 rounded-lg shadow-inner"><Icons.Shield /></div>
              <h1 className="font-black tracking-tighter text-lg md:text-2xl uppercase">Hive<span className="text-emerald-500">Bot</span></h1>
            </div>
            
            <div className="flex items-center gap-2 md:gap-6">
              <div className="hidden lg:flex bg-zinc-900 p-1 rounded-2xl border border-zinc-800 shadow-inner">
                <button onClick={() => setView('dashboard')} className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${view === 'dashboard' ? 'bg-zinc-800 text-emerald-400 shadow-xl' : 'text-zinc-500 hover:text-zinc-300'}`}>Dashboard</button>
                <button onClick={() => setView('cluster')} className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${view === 'cluster' ? 'bg-zinc-800 text-emerald-400 shadow-xl' : 'text-zinc-500 hover:text-zinc-300'}`}>Bots</button>
                <button onClick={() => setView('hive-mind')} className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${view === 'hive-mind' ? 'bg-zinc-800 text-emerald-400 shadow-xl' : 'text-zinc-500 hover:text-zinc-300'}`}>Brain</button>
                <button onClick={() => setView('team')} className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${view === 'team' ? 'bg-zinc-800 text-emerald-400 shadow-xl' : 'text-zinc-500 hover:text-zinc-300'}`}>Team</button>
                <button onClick={() => setView('setup')} className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${view === 'setup' ? 'bg-zinc-800 text-emerald-400 shadow-xl' : 'text-zinc-500 hover:text-zinc-300'}`}>Env</button>
                <button onClick={() => setView('context')} className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${view === 'context' ? 'bg-zinc-800 text-emerald-400 shadow-xl' : 'text-zinc-500 hover:text-zinc-300'}`}>Context</button>
              </div>
              
              <div className="w-px h-6 bg-zinc-800 hidden lg:block"></div>
              
              <button 
                onClick={handleLogout}
                className="flex items-center gap-2 px-2 md:px-3 py-1.5 text-zinc-500 hover:text-red-400 transition-all bg-zinc-900/50 rounded-lg md:rounded-xl border border-zinc-800 hover:border-red-500/20 group"
                title="Terminate Session"
              >
                <span className="text-[9px] font-black uppercase tracking-widest hidden md:inline">Terminate</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="group-hover:translate-x-0.5 transition-transform"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
              </button>
            </div>
          </header>
        )}

        <div className="flex-1 overflow-y-auto p-4 md:p-8 bg-gradient-to-b from-zinc-950 to-zinc-900/40">
          {view === 'global-config' && (
            <GlobalConfig 
              hives={hives} 
              users={users} 
              settings={globalSettings} 
              onUpdateUsers={setUsers} 
              onUpdateSettings={setGlobalSettings} 
            />
          )}

          {view === 'dashboard' && activeHive && (
            <Dashboard 
              hive={activeHive} 
              onNavigateToNodes={() => setView('cluster')} 
              onRunAgent={runAgent}
              agents={agents}
            />
          )}

          {view === 'hive-mind' && (
            <HiveMindDashboard hives={hives} />
          )}

          {view === 'team' && activeHive && (
            <HiveTeam 
              hive={activeHive}
              allUsers={users}
              onUpdateUsers={setUsers}
            />
          )}

          {view === 'setup' && activeHive && (
            <div className="max-w-4xl mx-auto space-y-8 md:space-y-12 pb-20 animate-in slide-in-from-bottom-4 duration-500">
              <div className="space-y-2">
                <h2 className="text-3xl md:text-5xl font-black tracking-tighter">Hive Environment</h2>
                <p className="text-zinc-500 text-base md:text-lg">Centralized configuration for the <span className="text-emerald-500 font-bold">{activeHive.name}</span> mesh.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-6 shadow-2xl relative overflow-hidden group col-span-full">
                  <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Layers /></div>
                  <h3 className="text-xs font-black uppercase tracking-[0.2em] text-emerald-500">Hive Identity</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-[10px] font-bold text-zinc-600 uppercase mb-2 tracking-widest">Hive Name</label>
                      <input 
                        type="text" 
                        value={activeHive.name} 
                        onChange={async (e) => {
                          await updateHive(activeHive.id, { name: e.target.value });
                        }}
                        className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 focus:outline-none transition-all shadow-inner" 
                        placeholder="Operations Alpha" 
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-zinc-600 uppercase mb-2 tracking-widest">Description</label>
                      <input 
                        type="text" 
                        value={activeHive.description} 
                        onChange={async (e) => {
                          await updateHive(activeHive.id, { description: e.target.value });
                        }}
                        className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 focus:outline-none transition-all shadow-inner" 
                        placeholder="Autonomous bot orchestration hive" 
                      />
                    </div>
                  </div>
                </div>

                <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-6 shadow-2xl relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Shield /></div>
                  <h3 className="text-xs font-black uppercase tracking-[0.2em] text-emerald-500">Default Security Policy</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-[10px] font-bold text-zinc-600 uppercase mb-2 tracking-widest">Default Bot UID</label>
                      <input 
                        type="text" 
                        value={globalUid} 
                        onChange={async (e) => {
                          await updateHive(activeHive.id, { globalUid: e.target.value });
                        }}
                        className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 focus:outline-none transition-all shadow-inner" 
                        placeholder="e.g. 1001" 
                      />
                      <p className="text-[10px] text-zinc-500 mt-2 italic">
                        Newly spawned bots inherit this limited-privilege UID for container isolation.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-6 shadow-2xl relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Cpu /></div>
                  <h3 className="text-xs font-black uppercase tracking-[0.2em] text-emerald-500">Reasoning Credentials</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-[10px] font-bold text-zinc-600 uppercase mb-2 tracking-widest">Master API Key (Orchestrator)</label>
                      <input 
                        type="password" 
                        value={globalApiKey} 
                        onChange={async (e) => {
                          await updateHive(activeHive.id, { globalApiKey: e.target.value });
                        }}
                        className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 focus:outline-none transition-all shadow-inner" 
                        placeholder="••••••••••••••••" 
                      />
                      <p className="text-[10px] text-zinc-500 mt-2 italic">Global fallback for bots without dedicated provider credentials.</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-emerald-500/5 border border-emerald-500/10 rounded-3xl p-8 flex items-center gap-8 shadow-xl">
                <div className="p-5 bg-emerald-600 text-white rounded-2xl shadow-lg shadow-emerald-900/20"><Icons.Server /></div>
                <div>
                  <h4 className="font-bold text-xl tracking-tight">Hive Network Operational</h4>
                  <p className="text-sm text-zinc-400 max-w-lg leading-relaxed mt-1">Environment integrity verified. Sandbox protocols are active. Each bot operates in a unique virtual space within the hive root.</p>
                </div>
              </div>
            </div>
          )}

          {view === 'context' && activeHive && (
            <div className="max-w-5xl mx-auto space-y-8 pb-20 animate-in fade-in duration-700">
              <div className="space-y-2">
                <h2 className="text-3xl md:text-4xl font-black tracking-tighter text-emerald-500">Hive Context</h2>
                <p className="text-zinc-500 text-sm md:text-base">USER.md definitions and shared assets inherited by all hive entities.</p>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <section className="lg:col-span-2 bg-zinc-900 rounded-3xl border border-zinc-800 p-4 md:p-8 shadow-2xl">
                  <div className="flex items-center justify-between mb-4 px-2">
                    <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">USER.md Configuration</span>
                  </div>
                  <textarea 
                    value={globalUserMd} 
                    onChange={async (e) => {
                      await updateHive(activeHive.id, { globalUserMd: e.target.value });
                    }}
                    className="w-full h-[400px] md:h-[500px] bg-transparent text-zinc-300 font-mono text-sm resize-none focus:outline-none border border-zinc-800/50 rounded-2xl p-4 md:p-6 shadow-inner" 
                    spellCheck={false} 
                  />
                </section>

                <section className="bg-zinc-900 rounded-3xl border border-zinc-800 p-6 shadow-2xl flex flex-col">
                  <div className="flex items-center justify-between mb-6">
                    <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">Shared Assets</span>
                    <button 
                      onClick={async () => {
                        const name = prompt('File name:');
                        if (name) {
                          const newFile: FileEntry = {
                            id: Math.random().toString(36).substr(2, 9),
                            name,
                            content: '',
                            size: 0,
                            type: 'md',
                            uploadedAt: new Date().toISOString()
                          };
                          await orchestratorService.addGlobalFileToHive(activeHive.id, newFile);
                          setHives(prev => prev.map(h => 
                            h.id === activeHive.id 
                              ? { ...h, globalFiles: [...h.globalFiles, newFile] }
                              : h
                          ));
                        }
                      }}
                      className="p-2 bg-emerald-500/10 text-emerald-500 rounded-lg hover:bg-emerald-500/20 transition-colors"
                    >
                      <Icons.Plus />
                    </button>
                  </div>
                  <div className="flex-1 space-y-2 overflow-y-auto">
                    {globalFiles.length === 0 && <p className="text-zinc-600 text-xs italic text-center py-10">No shared files in this hive.</p>}
                    {globalFiles.map(file => (
                      <div key={file.id} className="group flex items-center justify-between p-3 bg-zinc-950 border border-zinc-800 rounded-xl hover:border-emerald-500/30 transition-all">
                        <div className="flex items-center gap-3 overflow-hidden">
                          <Icons.File />
                          <span className="text-xs font-bold text-zinc-400 truncate">{file.name}</span>
                        </div>
                        <button 
                          onClick={async () => {
                            await orchestratorService.removeGlobalFileFromHive(activeHive.id, file.id);
                            setHives(prev => prev.map(h => 
                              h.id === activeHive.id 
                                ? { ...h, globalFiles: h.globalFiles.filter(f => f.id !== file.id) }
                                : h
                            ));
                          }}
                          className="p-1.5 text-zinc-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                        >
                          <Icons.Trash />
                        </button>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            </div>
          )}

          {view === 'agent' && selectedAgent && (
            <AgentDetails 
              agent={selectedAgent} 
              onUpdate={handleUpdateAgent} 
              onRun={() => runAgent(selectedAgent.id)}
              onDelete={handleDeleteAgent}
              messages={messages.filter(m => m.from === selectedAgent.id)}
              allAgents={agents}
              globalFiles={globalFiles}
            />
          )}

          {view === 'cluster' && (
            <div className="space-y-12">
              <div className="space-y-2">
                <h2 className="text-4xl font-black tracking-tighter">Hive Overview</h2>
                <p className="text-zinc-500 text-lg">Active mesh topology and bot status.</p>
              </div>
              <AgentGrid agents={agents} onSelect={(id) => { setSelectedAgentId(id); setView('agent'); setIsSidebarOpen(false); }} />
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <ProviderProvider>
      <BridgeProvider>
        <AppContent />
      </BridgeProvider>
    </ProviderProvider>
  );
};

export default App;

```

---

## 📄 frontend/src/components/AIProviderConfig.tsx

```tsx
import React, { useState, useEffect } from 'react';
import { Icons } from '../constants';
import { orchestratorService } from '../services/orchestratorService';
import { useProviders } from '../contexts/ProviderContext';

interface ProviderModel {
  id: string;
  name: string;
  enabled: boolean;
  is_primary: boolean;
  is_utility: boolean;
}

interface Provider {
  name: string;
  display_name: string;
  enabled: boolean;
  api_key_present: boolean;
  models: Record<string, ProviderModel>;
}

interface KnownProvider {
  name: string;
  display_name: string;
  models: Array<{ id: string; name: string; default_primary?: boolean; default_utility?: boolean }>;
}

export const AIProviderConfig: React.FC = () => {
  const { providers, refreshProviders } = useProviders();
  const [knownProviders, setKnownProviders] = useState<KnownProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [apiKeyInputs, setApiKeyInputs] = useState<Record<string, string>>({});
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({});
  const [showAddProvider, setShowAddProvider] = useState(false);
  const [selectedKnownProvider, setSelectedKnownProvider] = useState<string>('');
  const [isCustomProvider, setIsCustomProvider] = useState(false);
  const [newProviderKey, setNewProviderKey] = useState('');
  const [newProviderDisplay, setNewProviderDisplay] = useState('');
  const [newProviderModels, setNewProviderModels] = useState<Array<{id: string, name: string, default_primary?: boolean, default_utility?: boolean}>>([]);
  const [newModelId, setNewModelId] = useState('');
  const [newModelName, setNewModelName] = useState('');

  useEffect(() => {
    loadKnownProviders().finally(() => setLoading(false));
  }, []);

  const loadKnownProviders = async () => {
    try {
      const data = await orchestratorService.getKnownProviders();
      setKnownProviders(data);
    } catch (err) {
      console.error('Failed to load known providers', err);
    }
  };

  const handleToggleProvider = async (providerKey: string, enabled: boolean) => {
    await updateProvider(providerKey, { enabled });
  };

  const handleApiKeyChange = (providerKey: string, value: string) => {
    setApiKeyInputs(prev => ({ ...prev, [providerKey]: value }));
  };

  const handleSaveApiKey = async (providerKey: string) => {
    const key = apiKeyInputs[providerKey];
    if (key === undefined) return;
    await updateProvider(providerKey, { api_key: key });
    setApiKeyInputs(prev => ({ ...prev, [providerKey]: '' }));
    setShowApiKey(prev => ({ ...prev, [providerKey]: false }));
  };

  const handleToggleModel = async (providerKey: string, modelId: string, enabled: boolean) => {
    const provider = providers[providerKey];
    if (!provider) return;
    const model = provider.models[modelId];
    // Prevent disabling if this is the primary and no other primary exists (back-end will handle, but UI can warn)
    if (!enabled && model?.is_primary) {
      alert('Cannot disable the primary model. Please set another model as primary first.');
      return;
    }
    if (!enabled && model?.is_utility) {
      alert('Cannot disable the utility model. Please set another model as utility first.');
      return;
    }
    const updatedModels = { ...provider.models };
    if (!updatedModels[modelId]) {
      const known = knownProviders.find(kp => kp.name === providerKey);
      const modelInfo = known?.models.find(m => m.id === modelId);
      updatedModels[modelId] = {
        id: modelId,
        name: modelInfo?.name || modelId,
        enabled,
        is_primary: false,
        is_utility: false,
      };
    } else {
      updatedModels[modelId] = { ...updatedModels[modelId], enabled };
    }
    await updateProvider(providerKey, { models: updatedModels });
  };

  const handleSetPrimary = async (providerKey: string, modelId: string) => {
    const provider = providers[providerKey];
    if (!provider) return;
    const model = provider.models[modelId];
    if (!model) return;
    if (!model.enabled) {
      alert('Cannot set a disabled model as primary. Enable the model first.');
      return;
    }
    await updateProvider(providerKey, {
      models: { [modelId]: { ...model, is_primary: true, is_utility: model.is_utility } }
    });
  };

  const handleSetUtility = async (providerKey: string, modelId: string) => {
    const provider = providers[providerKey];
    if (!provider) return;
    const model = provider.models[modelId];
    if (!model) return;
    if (!model.enabled) {
      alert('Cannot set a disabled model as utility. Enable the model first.');
      return;
    }
    await updateProvider(providerKey, {
      models: { [modelId]: { ...model, is_utility: true, is_primary: model.is_primary } }
    });
  };

  const handleDeleteProvider = async (providerKey: string) => {
    if (!confirm(`Delete provider "${providerKey}"?`)) return;
    setSaving(true);
    try {
      await orchestratorService.deleteProvider(providerKey);
      await refreshProviders();
    } catch (err) {
      console.error('Failed to delete provider', err);
    } finally {
      setSaving(false);
    }
  };

  const updateProvider = async (providerKey: string, updates: any) => {
    setSaving(true);
    try {
      await orchestratorService.updateProviderConfig(providerKey, updates);
      await refreshProviders();
    } catch (err) {
      console.error('Failed to update provider', err);
    } finally {
      setSaving(false);
    }
  };

  const handleAddProvider = async () => {
    if (isCustomProvider) {
      if (!newProviderKey || !newProviderDisplay) return;
      const models: Record<string, ProviderModel> = {};
      newProviderModels.forEach(m => {
        models[m.id] = {
          id: m.id,
          name: m.name,
          enabled: true,
          is_primary: m.default_primary || false,
          is_utility: m.default_utility || false,
        };
      });
      await updateProvider(newProviderKey, {
        display_name: newProviderDisplay,
        models
      });
    } else {
      if (!selectedKnownProvider) return;
      const known = knownProviders.find(kp => kp.name === selectedKnownProvider);
      if (!known) return;
      const models: Record<string, ProviderModel> = {};
      known.models.forEach(m => {
        models[m.id] = {
          id: m.id,
          name: m.name,
          enabled: true,
          is_primary: m.default_primary || false,
          is_utility: m.default_utility || false,
        };
      });
      await updateProvider(known.name, {
        display_name: known.display_name,
        models
      });
    }
    setShowAddProvider(false);
    resetAddForm();
  };

  const resetAddForm = () => {
    setSelectedKnownProvider('');
    setIsCustomProvider(false);
    setNewProviderKey('');
    setNewProviderDisplay('');
    setNewProviderModels([]);
    setNewModelId('');
    setNewModelName('');
  };

  const addModelToNewProvider = () => {
    if (!newModelId || !newModelName) return;
    setNewProviderModels([...newProviderModels, { id: newModelId, name: newModelName }]);
    setNewModelId('');
    setNewModelName('');
  };

  const removeModelFromNewProvider = (modelId: string) => {
    setNewProviderModels(newProviderModels.filter(m => m.id !== modelId));
  };

  if (loading) {
    return <div className="text-center py-8 text-zinc-500">Loading provider configuration...</div>;
  }

  const providerKeys = Object.keys(providers);

  return (
    <div className="space-y-6">
      <div className="flex justify-end mb-4">
        <button
          onClick={() => setShowAddProvider(true)}
          className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-emerald-500 transition-colors flex items-center gap-2"
        >
          <Icons.Plus />
          Add Provider
        </button>
      </div>

      {providerKeys.length === 0 ? (
        <div className="text-center py-8 text-zinc-500 italic">No providers configured. Click "Add Provider" to get started.</div>
      ) : (
        providerKeys.map((providerKey) => {
          const provider = providers[providerKey];
          const known = knownProviders.find(kp => kp.name === providerKey);

          return (
            <div key={providerKey} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-xl relative">
              {!known && (
                <button
                  onClick={() => handleDeleteProvider(providerKey)}
                  className="absolute top-4 right-4 p-2 text-zinc-500 hover:text-red-500 transition-colors"
                  title="Delete Provider"
                >
                  <Icons.Trash className="w-4 h-4" />
                </button>
              )}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-bold text-emerald-400">{provider.display_name}</h3>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    provider.enabled 
                      ? 'bg-emerald-500/20 text-emerald-400' 
                      : 'bg-zinc-800 text-zinc-500'
                  }`}>
                    {provider.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <span className="text-xs text-zinc-400">Enable</span>
                  <input
                    type="checkbox"
                    checked={provider.enabled}
                    onChange={(e) => handleToggleProvider(providerKey, e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-10 h-5 bg-zinc-800 rounded-full peer-checked:bg-emerald-600 transition-all relative">
                    <div className="absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-all peer-checked:left-6"></div>
                  </div>
                </label>
              </div>

              {/* API Key Section */}
              <div className="mb-4 p-4 bg-zinc-950 rounded-xl border border-zinc-800">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-zinc-300">API Key</span>
                  {provider.api_key_present ? (
                    <span className="text-xs text-emerald-500 flex items-center gap-1">
                      <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                      Key stored
                    </span>
                  ) : (
                    <span className="text-xs text-red-400 flex items-center gap-1">
                      <span className="w-2 h-2 bg-red-400 rounded-full"></span>
                      Missing Key
                    </span>
                  )}
                </div>
                <div className="mt-2 flex gap-2">
                  <div className="relative flex-1">
                    <input
                      type={showApiKey[providerKey] ? 'text' : 'password'}
                      value={apiKeyInputs[providerKey] || ''}
                      onChange={(e) => handleApiKeyChange(providerKey, e.target.value)}
                      placeholder="Enter new API key"
                      className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-sm text-zinc-200 focus:outline-none focus:border-emerald-500"
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(prev => ({ ...prev, [providerKey]: !prev[providerKey] }))}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 text-xs"
                    >
                      {showApiKey[providerKey] ? 'Hide' : 'Show'}
                    </button>
                  </div>
                  <button
                    onClick={() => handleSaveApiKey(providerKey)}
                    disabled={!apiKeyInputs[providerKey] || saving}
                    className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm hover:bg-emerald-500 disabled:opacity-50"
                  >
                    Save
                  </button>
                </div>
              </div>

              {/* Models List */}
              {provider.enabled && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-widest text-zinc-500">Models</h4>
                  {Object.values(provider.models).map((model) => (
                    <div key={model.id} className="flex items-center justify-between p-3 bg-zinc-950 rounded-lg border border-zinc-800">
                      <div className="flex items-center gap-4">
                        <span className={`text-sm ${model.enabled ? 'text-zinc-300' : 'text-zinc-600'}`}>{model.name}</span>
                        <label className="flex items-center gap-1 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={model.enabled}
                            onChange={(e) => handleToggleModel(providerKey, model.id, e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-8 h-4 bg-zinc-800 rounded-full peer-checked:bg-emerald-600 transition-all relative">
                            <div className="absolute top-0.5 left-0.5 w-3 h-3 bg-white rounded-full transition-all peer-checked:left-4"></div>
                          </div>
                          <span className="text-xs text-zinc-400">Enable</span>
                        </label>
                      </div>
                      <div className="flex items-center gap-3">
                        {/* Primary radio */}
                        <label className={`flex items-center gap-1 cursor-pointer ${!model.enabled ? 'opacity-50' : ''}`}>
                          <input
                            type="radio"
                            name={`primary-${providerKey}`}
                            checked={model.is_primary}
                            onChange={() => handleSetPrimary(providerKey, model.id)}
                            disabled={!model.enabled}
                            className="sr-only peer"
                          />
                          <div className={`w-4 h-4 rounded-full border-2 border-zinc-600 peer-checked:border-emerald-500 peer-checked:bg-emerald-500 ${!model.enabled ? 'border-zinc-700' : ''}`}></div>
                          <span className={`text-xs ${model.enabled ? 'text-zinc-400' : 'text-zinc-600'}`}>Primary</span>
                        </label>
                        {/* Utility radio */}
                        <label className={`flex items-center gap-1 cursor-pointer ${!model.enabled ? 'opacity-50' : ''}`}>
                          <input
                            type="radio"
                            name={`utility-${providerKey}`}
                            checked={model.is_utility}
                            onChange={() => handleSetUtility(providerKey, model.id)}
                            disabled={!model.enabled}
                            className="sr-only peer"
                          />
                          <div className={`w-4 h-4 rounded-full border-2 border-zinc-600 peer-checked:border-purple-500 peer-checked:bg-purple-500 ${!model.enabled ? 'border-zinc-700' : ''}`}></div>
                          <span className={`text-xs ${model.enabled ? 'text-zinc-400' : 'text-zinc-600'}`}>Utility</span>
                        </label>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })
      )}

      {/* Add Provider Modal */}
      {showAddProvider && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-zinc-900 rounded-2xl border border-zinc-800 p-6 max-w-md w-full shadow-2xl">
            <h3 className="text-lg font-bold text-emerald-400 mb-4">Add AI Provider</h3>
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    checked={!isCustomProvider}
                    onChange={() => setIsCustomProvider(false)}
                    className="text-emerald-500"
                  />
                  <span className="text-sm text-zinc-300">Select from known providers</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    checked={isCustomProvider}
                    onChange={() => setIsCustomProvider(true)}
                    className="text-emerald-500"
                  />
                  <span className="text-sm text-zinc-300">Custom provider</span>
                </label>
              </div>

              {!isCustomProvider ? (
                <div>
                  <label className="block text-xs font-bold text-zinc-500 uppercase mb-1">Provider</label>
                  <select
                    value={selectedKnownProvider}
                    onChange={(e) => setSelectedKnownProvider(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm text-zinc-200"
                  >
                    <option value="">Select a provider</option>
                    {knownProviders
                      .filter(kp => !providers[kp.name]) // only show those not already added
                      .map(kp => (
                        <option key={kp.name} value={kp.name}>{kp.display_name}</option>
                      ))}
                  </select>
                </div>
              ) : (
                <>
                  <div>
                    <label className="block text-xs font-bold text-zinc-500 uppercase mb-1">Provider Key</label>
                    <input
                      type="text"
                      value={newProviderKey}
                      onChange={(e) => setNewProviderKey(e.target.value)}
                      placeholder="e.g., cohere"
                      className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm text-zinc-200"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-zinc-500 uppercase mb-1">Display Name</label>
                    <input
                      type="text"
                      value={newProviderDisplay}
                      onChange={(e) => setNewProviderDisplay(e.target.value)}
                      placeholder="e.g., Cohere"
                      className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm text-zinc-200"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-zinc-500 uppercase mb-2">Models</label>
                    {newProviderModels.map(model => (
                      <div key={model.id} className="flex items-center justify-between p-2 bg-zinc-950 rounded-lg border border-zinc-800 mb-2">
                        <span className="text-sm text-zinc-300">{model.name} ({model.id})</span>
                        <button
                          onClick={() => removeModelFromNewProvider(model.id)}
                          className="text-red-500 hover:text-red-400"
                        >
                          <Icons.Trash className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                    <div className="flex gap-2 mt-2">
                      <input
                        type="text"
                        value={newModelId}
                        onChange={(e) => setNewModelId(e.target.value)}
                        placeholder="Model ID (e.g., command-r)"
                        className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1 text-xs text-zinc-200"
                      />
                      <input
                        type="text"
                        value={newModelName}
                        onChange={(e) => setNewModelName(e.target.value)}
                        placeholder="Display Name"
                        className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1 text-xs text-zinc-200"
                      />
                      <button
                        onClick={addModelToNewProvider}
                        className="px-3 py-1 bg-emerald-600 text-white rounded-lg text-xs hover:bg-emerald-500"
                      >
                        Add
                      </button>
                    </div>
                  </div>
                </>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleAddProvider}
                  disabled={(!isCustomProvider && !selectedKnownProvider) || (isCustomProvider && (!newProviderKey || !newProviderDisplay))}
                  className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-bold hover:bg-emerald-500 disabled:opacity-50"
                >
                  Add Provider
                </button>
                <button
                  onClick={() => {
                    setShowAddProvider(false);
                    resetAddForm();
                  }}
                  className="flex-1 px-4 py-2 bg-zinc-800 text-zinc-300 rounded-lg text-sm font-bold hover:bg-zinc-700"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {saving && (
        <div className="fixed bottom-4 right-4 bg-emerald-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Saving...
        </div>
      )}
    </div>
  );
};

```

---

## 📄 frontend/src/components/AgentDetails.tsx

```tsx
import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Agent, AgentStatus, Message, FileEntry, ReportingTarget, ChannelConfig, ChannelCredentials } from '../types';
import { Icons } from '../constants';
import { orchestratorService } from '../services/orchestratorService';
import { useProviders } from '../contexts/ProviderContext';
import { useBridges } from '../contexts/BridgeContext';

interface AgentDetailsProps {
  agent: Agent;
  onUpdate: (updated: Agent) => Promise<Agent>;
  onRun: () => void;
  onDelete: (id: string) => void;
  messages: Message[];
  allAgents: Agent[];
  globalFiles: FileEntry[];
}

export const AgentDetails: React.FC<AgentDetailsProps> = ({ agent, onUpdate, onRun, onDelete, messages, allAgents, globalFiles }) => {
  const [activeTab, setActiveTab] = useState<'soul' | 'identity' | 'tools' | 'files' | 'channels' | 'config' | 'logs' | 'subagents'>('soul');
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [editingChannel, setEditingChannel] = useState<string | null>(null);
  const [editChannelData, setEditChannelData] = useState<ChannelConfig | null>(null);
  const [selectedChildId, setSelectedChildId] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { providers, getEnabledModels, getPrimaryModel, getUtilityModel, loading: providersLoading } = useProviders();
  const { enabledBridgeTypes } = useBridges();
  const [modelsVersion, setModelsVersion] = useState(0);

  // Local state for editable fields
  const [localName, setLocalName] = useState(agent.name);
  const [localRole, setLocalRole] = useState(agent.role);
  const [localSoulMd, setLocalSoulMd] = useState(agent.soulMd);
  const [localIdentityMd, setLocalIdentityMd] = useState(agent.identityMd);
  const [localToolsMd, setLocalToolsMd] = useState(agent.toolsMd);
  const [localUid, setLocalUid] = useState(agent.userUid);
  const [localParentId, setLocalParentId] = useState(agent.parentId);
  const [localReasoning, setLocalReasoning] = useState(agent.reasoning);
  const [localReportingTarget, setLocalReportingTarget] = useState(agent.reportingTarget || ReportingTarget.PARENT);
  const [localSubAgentIds, setLocalSubAgentIds] = useState(agent.subAgentIds || []);
  const [localChannels, setLocalChannels] = useState<ChannelConfig[]>(agent.channels || []);

  const primaryModel = useMemo(() => {
    const prim = getPrimaryModel();
    return prim ? `${prim.provider}:${prim.modelId}` : null;
  }, [providers, getPrimaryModel]);

  const utilityModel = useMemo(() => {
    const util = getUtilityModel();
    return util ? `${util.provider}:${util.modelId}` : null;
  }, [providers, getUtilityModel]);

  useEffect(() => {
    setLocalName(agent.name);
    setLocalRole(agent.role);
    setLocalSoulMd(agent.soulMd);
    setLocalIdentityMd(agent.identityMd);
    setLocalToolsMd(agent.toolsMd);
    setLocalUid(agent.userUid);
    setLocalParentId(agent.parentId);
    setLocalReasoning(agent.reasoning);
    setLocalReportingTarget(agent.reportingTarget || ReportingTarget.PARENT);
    setLocalSubAgentIds(agent.subAgentIds || []);
    setLocalChannels(agent.channels || []);
  }, [agent]);

  const handleNameBlur = useCallback(async () => {
    if (localName === agent.name) return;
    const updated = { ...agent, name: localName };
    await onUpdate(updated);
  }, [localName, agent, onUpdate]);

  const handleRoleBlur = useCallback(async () => {
    if (localRole === agent.role) return;
    const updated = { ...agent, role: localRole };
    await onUpdate(updated);
  }, [localRole, agent, onUpdate]);

  const handleSoulBlur = useCallback(async () => {
    if (localSoulMd === agent.soulMd) return;
    const updated = { ...agent, soulMd: localSoulMd };
    await onUpdate(updated);
  }, [localSoulMd, agent, onUpdate]);

  const handleIdentityBlur = useCallback(async () => {
    if (localIdentityMd === agent.identityMd) return;
    const updated = { ...agent, identityMd: localIdentityMd };
    await onUpdate(updated);
  }, [localIdentityMd, agent, onUpdate]);

  const handleToolsBlur = useCallback(async () => {
    if (localToolsMd === agent.toolsMd) return;
    const updated = { ...agent, toolsMd: localToolsMd };
    await onUpdate(updated);
  }, [localToolsMd, agent, onUpdate]);

  const handleUidBlur = useCallback(async () => {
    if (localUid === agent.userUid) return;
    const updated = { ...agent, userUid: localUid };
    await onUpdate(updated);
  }, [localUid, agent, onUpdate]);

  const handleParentChange = useCallback(async (value: string | undefined) => {
    setLocalParentId(value);
    const updated = { ...agent, parentId: value };
    await onUpdate(updated);
  }, [agent, onUpdate]);

  const handleReportingTargetChange = useCallback(async (value: ReportingTarget) => {
    setLocalReportingTarget(value);
    const updated = { ...agent, reportingTarget: value };
    await onUpdate(updated);
  }, [agent, onUpdate]);

  const handleReasoningChange = useCallback(async (updates: Partial<typeof agent.reasoning>) => {
    const newReasoning = { ...localReasoning, ...updates };
    setLocalReasoning(newReasoning);
    const updated = { ...agent, reasoning: newReasoning };
    await onUpdate(updated);
  }, [localReasoning, agent, onUpdate]);

  const handleTemperatureBlur = useCallback(async (e: React.FocusEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    if (isNaN(val) || val === agent.reasoning.temperature) return;
    await handleReasoningChange({ temperature: val });
  }, [agent.reasoning.temperature, handleReasoningChange]);

  const handleTopPBlur = useCallback(async (e: React.FocusEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    if (isNaN(val) || val === agent.reasoning.topP) return;
    await handleReasoningChange({ topP: val });
  }, [agent.reasoning.topP, handleReasoningChange]);

  const handleMaxTokensBlur = useCallback(async (e: React.FocusEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    if (isNaN(val) || val === agent.reasoning.maxTokens) return;
    await handleReasoningChange({ maxTokens: val });
  }, [agent.reasoning.maxTokens, handleReasoningChange]);

  const handleModelChange = useCallback(async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const model = e.target.value;
    await handleReasoningChange({ model });
  }, [handleReasoningChange]);

  const handleCheapModelChange = useCallback(async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const cheap_model = e.target.value || undefined;
    await handleReasoningChange({ cheap_model });
  }, [handleReasoningChange]);

  const handleGlobalDefaultToggle = useCallback(async (useGlobal: boolean) => {
    await handleReasoningChange({ use_global_default: useGlobal });
  }, [handleReasoningChange]);

  const handleCustomMaxTokensToggle = useCallback(async (useCustom: boolean) => {
    await handleReasoningChange({ use_custom_max_tokens: useCustom });
  }, [handleReasoningChange]);

  const handleAddChannel = useCallback((type: ChannelConfig['type']) => {
    const newChannel: ChannelConfig = {
      id: `ch-${Math.random().toString(36).substr(2, 5)}`,
      type,
      enabled: false,
      credentials: {},
      status: 'disconnected'
    };
    const updatedChannels = [...localChannels, newChannel];
    setLocalChannels(updatedChannels);
    onUpdate({ ...agent, channels: updatedChannels });
    setEditingChannel(newChannel.id);
    setEditChannelData(newChannel);
  }, [localChannels, agent, onUpdate]);

  const handleSelectChannel = useCallback((channelId: string) => {
    const channel = localChannels.find(c => c.id === channelId);
    if (channel) {
      setEditChannelData({ ...channel, credentials: { ...channel.credentials } });
      setEditingChannel(channelId);
    }
  }, [localChannels]);

  const handleEditFieldChange = useCallback((field: keyof ChannelCredentials, value: string) => {
    if (!editChannelData) return;
    setEditChannelData({
      ...editChannelData,
      credentials: {
        ...editChannelData.credentials,
        [field]: value
      }
    });
  }, [editChannelData]);

  const handleSaveChannel = useCallback(async () => {
    if (!editChannelData) return;
    const updatedChannels = localChannels.map(ch =>
      ch.id === editChannelData.id ? editChannelData : ch
    );
    setLocalChannels(updatedChannels);
    await onUpdate({ ...agent, channels: updatedChannels });
    setEditingChannel(null);
    setEditChannelData(null);
  }, [editChannelData, localChannels, agent, onUpdate]);

  const handleCancelEdit = useCallback(() => {
    setEditingChannel(null);
    setEditChannelData(null);
  }, []);

  const handleDeleteChannel = useCallback(async (id: string) => {
    const updatedChannels = localChannels.filter(c => c.id !== id);
    setLocalChannels(updatedChannels);
    await onUpdate({ ...agent, channels: updatedChannels });
    if (editingChannel === id) {
      setEditingChannel(null);
      setEditChannelData(null);
    }
  }, [localChannels, agent, onUpdate, editingChannel]);

  const handleAddSubAgent = useCallback(async () => {
    if (!selectedChildId) return;
    try {
      await orchestratorService.addSubAgent(agent.id, selectedChildId);
      const updatedSubAgents = [...localSubAgentIds, selectedChildId];
      setLocalSubAgentIds(updatedSubAgents);
      const updated = { ...agent, subAgentIds: updatedSubAgents };
      await onUpdate(updated);
      setSelectedChildId('');
    } catch (err) {
      console.error('Failed to add sub-agent', err);
    }
  }, [selectedChildId, agent, localSubAgentIds, onUpdate]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    try {
      const newFile = await orchestratorService.uploadAgentFile(agent.id, file);
      const updatedAgent = await orchestratorService.getAgent(agent.id);
      setLocalSubAgentIds(updatedAgent.subAgentIds || []);
      await onUpdate(updatedAgent);
    } catch (err) {
      console.error('File upload failed', err);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    if (!confirm('Delete this file?')) return;
    try {
      await orchestratorService.deleteAgentFile(agent.id, fileId);
      const updatedAgent = await orchestratorService.getAgent(agent.id);
      await onUpdate(updatedAgent);
    } catch (err) {
      console.error('File deletion failed', err);
    }
  };

  const handleDeleteAgent = () => {
    if (confirm(`Are you sure you want to delete bot "${agent.name}"?`)) {
      onDelete(agent.id);
    }
  };

  useEffect(() => {
    setModelsVersion(v => v + 1);
  }, [providers]);

  const availableModels = useMemo(() => getEnabledModels(), [modelsVersion, getEnabledModels]);

  const memoryLoad = agent.memory?.shortTerm?.length ? ((agent.memory.shortTerm.length / 10) * 100).toFixed(0) : '0';

  const editingFile = agent.localFiles?.find(f => f.id === selectedFileId) || globalFiles.find(f => f.id === selectedFileId);
  const isGlobalFile = globalFiles.some(f => f.id === selectedFileId);

  const availableChannelTypes = useMemo(() => {
    const types = [...enabledBridgeTypes];
    if (!types.includes('custom')) types.push('custom');
    return types;
  }, [enabledBridgeTypes]);

  return (
    <div className="space-y-8 animate-in fade-in duration-500 pb-20">
      <div className="flex items-start justify-between bg-zinc-900/50 p-6 rounded-3xl border border-zinc-800 shadow-2xl">
        <div className="flex items-center gap-6 flex-1">
          <div className="w-20 h-20 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center justify-center text-emerald-500 shadow-inner flex-shrink-0 relative overflow-hidden">
            <Icons.Cpu />
          </div>
          <div className="flex-1 space-y-1">
            <input
              type="text"
              value={localName}
              onChange={(e) => setLocalName(e.target.value)}
              onBlur={handleNameBlur}
              className="text-3xl font-black bg-transparent border-none focus:outline-none hover:bg-zinc-800 rounded px-2 -ml-2 w-full transition-colors tracking-tighter text-zinc-100"
            />
            <div className="flex items-center gap-3">
              <span className="text-[10px] px-2 py-1 bg-zinc-800 text-zinc-400 rounded-md border border-zinc-700 font-mono">Bot ID: {agent.id}</span>
              <span className={`text-[10px] px-2 py-1 rounded-md uppercase font-black tracking-widest ${agent.status === AgentStatus.RUNNING ? 'bg-emerald-500/20 text-emerald-400 animate-pulse' : 'bg-zinc-800 text-zinc-500'}`}>{agent.status}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDeleteAgent}
            className="p-4 bg-red-600/20 text-red-500 rounded-2xl hover:bg-red-600/30 transition-all"
            title="Delete Bot"
          >
            <Icons.Trash className="w-5 h-5" />
          </button>
          <button
            onClick={onRun}
            disabled={agent.status === AgentStatus.RUNNING}
            className="px-8 py-4 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-2xl font-black uppercase tracking-widest text-xs transition-all shadow-2xl flex items-center gap-3"
          >
            <Icons.Terminal /> {agent.status === AgentStatus.RUNNING ? 'Executing Cycle...' : 'Execute Bot'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 p-1 bg-zinc-900 rounded-2xl border border-zinc-800 w-fit overflow-x-auto max-w-full">
        {(['soul', 'identity', 'tools', 'files', 'channels', 'config', 'logs', 'subagents'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} className={`px-4 py-2 text-[10px] font-black uppercase tracking-widest transition-all rounded-xl whitespace-nowrap ${activeTab === tab ? 'bg-zinc-800 text-emerald-400 shadow-lg' : 'text-zinc-500 hover:text-zinc-300'}`}>
            {tab === 'soul' ? 'Soul.md' : tab === 'identity' ? 'Identity.md' : tab === 'tools' ? 'Tools.md' : tab === 'subagents' ? 'Sub‑Bots' : tab}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-3">
          {/* Soul, Identity, Tools tabs */}
          {activeTab === 'soul' && (
            <div className="bg-zinc-900 rounded-3xl border border-zinc-800 p-6 shadow-2xl">
              <textarea
                value={localSoulMd}
                onChange={(e) => setLocalSoulMd(e.target.value)}
                onBlur={handleSoulBlur}
                className="w-full h-[550px] bg-transparent text-zinc-300 font-mono text-sm resize-none focus:outline-none"
                spellCheck={false}
              />
            </div>
          )}
          {activeTab === 'identity' && (
            <div className="bg-zinc-900 rounded-3xl border border-zinc-800 p-6 shadow-2xl">
              <textarea
                value={localIdentityMd}
                onChange={(e) => setLocalIdentityMd(e.target.value)}
                onBlur={handleIdentityBlur}
                className="w-full h-[550px] bg-transparent text-zinc-300 font-mono text-sm resize-none focus:outline-none"
                spellCheck={false}
              />
            </div>
          )}
          {activeTab === 'tools' && (
            <div className="bg-zinc-900 rounded-3xl border border-zinc-800 p-6 shadow-2xl">
              <textarea
                value={localToolsMd}
                onChange={(e) => setLocalToolsMd(e.target.value)}
                onBlur={handleToolsBlur}
                className="w-full h-[550px] bg-transparent text-zinc-300 font-mono text-sm resize-none focus:outline-none"
                spellCheck={false}
              />
            </div>
          )}

          {/* Channels Tab */}
          {activeTab === 'channels' && (
            <div className="h-[600px] flex flex-col space-y-4 animate-in fade-in duration-300">
              <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
                {availableChannelTypes.map((type) => (
                  <button
                    key={type}
                    onClick={() => handleAddChannel(type as any)}
                    className="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-[10px] font-black uppercase tracking-widest text-zinc-500 hover:text-emerald-400 transition-all shrink-0"
                  >
                    Add {type}
                  </button>
                ))}
              </div>
              <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-zinc-900 rounded-3xl border border-zinc-800 p-4 space-y-2 overflow-y-auto">
                  {localChannels.length === 0 && <p className="text-zinc-600 text-xs italic p-4">No active relay channels.</p>}
                  {localChannels.map(ch => (
                    <button
                      key={ch.id}
                      onClick={() => handleSelectChannel(ch.id)}
                      className={`w-full text-left p-4 rounded-2xl border transition-all flex items-center justify-between ${editingChannel === ch.id ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-zinc-950 border-zinc-800 text-zinc-500 hover:bg-zinc-900'}`}
                    >
                      <div className="flex items-center gap-3">
                        <Icons.Globe />
                        <span className="text-[10px] font-black uppercase tracking-widest">{ch.type}</span>
                      </div>
                      <div className={`w-1.5 h-1.5 rounded-full ${ch.enabled ? 'bg-emerald-500' : 'bg-zinc-700'}`} />
                    </button>
                  ))}
                </div>
                <div className="md:col-span-2 bg-zinc-900 rounded-3xl border border-zinc-800 p-6 shadow-2xl overflow-y-auto">
                  {editingChannel && editChannelData ? (
                    <div className="space-y-6">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-black uppercase tracking-widest text-emerald-500">Configure: {editChannelData.type}</h4>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <span className="text-[10px] font-black text-zinc-500 uppercase">Status</span>
                          <input
                            type="checkbox"
                            checked={editChannelData.enabled}
                            onChange={e => {
                              setEditChannelData({ ...editChannelData, enabled: e.target.checked });
                            }}
                            className="sr-only peer"
                          />
                          <div className="w-10 h-5 bg-zinc-800 rounded-full peer-checked:bg-emerald-600 transition-all relative">
                            <div className="absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-all peer-checked:left-6"></div>
                          </div>
                        </label>
                      </div>
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-[10px] font-bold text-zinc-600 uppercase mb-2">Bot Token / API Key</label>
                            <input
                              type="password"
                              value={editChannelData.credentials?.botToken || ''}
                              onChange={e => handleEditFieldChange('botToken', e.target.value)}
                              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-xs text-zinc-300"
                              placeholder="Relay Credentials"
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] font-bold text-zinc-600 uppercase mb-2">Channel / Chat ID</label>
                            <input
                              type="text"
                              value={editChannelData.credentials?.chatId || ''}
                              onChange={e => handleEditFieldChange('chatId', e.target.value)}
                              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-xs text-zinc-300"
                              placeholder="@target_channel"
                            />
                          </div>
                        </div>
                      </div>
                      <div className="pt-6 border-t border-zinc-800 flex justify-between items-center">
                        <button onClick={handleCancelEdit} className="text-[10px] font-black uppercase text-zinc-500">Close</button>
                        <button
                          onClick={handleSaveChannel}
                          className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-emerald-500 transition-colors"
                        >
                          Save
                        </button>
                        <button onClick={() => handleDeleteChannel(editChannelData.id)} className="text-[10px] font-black uppercase text-red-500/50 hover:text-red-500">Destroy Relay</button>
                      </div>
                    </div>
                  ) : (
                    <div className="h-full flex items-center justify-center text-zinc-600 italic">Select a relay channel to manage.</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Config Tab */}
          {activeTab === 'config' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="bg-zinc-900 rounded-3xl border border-zinc-800 p-8 space-y-6 shadow-xl">
                <h3 className="text-xs font-black uppercase tracking-widest text-emerald-500">Reasoning Engine</h3>

                <div>
                  <label className="block text-[10px] font-black text-zinc-600 uppercase mb-2">Role</label>
                  <input
                    type="text"
                    value={localRole}
                    onChange={(e) => setLocalRole(e.target.value)}
                    onBlur={handleRoleBlur}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200"
                    placeholder="e.g. Chief of Staff, Worker"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-black text-zinc-600 uppercase mb-2">Reporting Target</label>
                  <select
                    value={localReportingTarget}
                    onChange={(e) => handleReportingTargetChange(e.target.value as ReportingTarget)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200"
                  >
                    <option value={ReportingTarget.PARENT}>Report to Parent Bot</option>
                    <option value={ReportingTarget.OWNER_DIRECT}>Direct to Owner (Channels)</option>
                    <option value={ReportingTarget.BOTH}>Hybrid Reporting</option>
                  </select>
                </div>

                <div className="flex items-center justify-between p-4 bg-zinc-950 rounded-xl border border-zinc-800">
                  <div>
                    <span className="text-sm font-medium text-zinc-300">Model Selection</span>
                    <p className="text-[10px] text-zinc-500 mt-1">
                      {localReasoning?.use_global_default
                        ? `Using global primary: ${primaryModel ? primaryModel : 'not configured'}`
                        : 'Using custom model'}
                    </p>
                    {localReasoning?.use_global_default && (
                      <p className="text-[10px] text-zinc-500 mt-1">
                        Global utility: {utilityModel ? utilityModel : 'not configured'}
                      </p>
                    )}
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={!localReasoning?.use_global_default}
                      onChange={(e) => handleGlobalDefaultToggle(!e.target.checked)}
                    />
                    <div className="w-11 h-6 bg-zinc-700 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                    <span className="ml-3 text-xs font-medium text-zinc-300">
                      {localReasoning?.use_global_default ? 'Default' : 'Custom'}
                    </span>
                  </label>
                </div>

                {!localReasoning?.use_global_default && (
                  <div className="space-y-4 mt-4">
                    <div>
                      <label className="block text-[10px] font-black text-zinc-600 uppercase mb-2">Model</label>
                      <select
                        key={modelsVersion}
                        value={localReasoning?.model || ''}
                        onChange={handleModelChange}
                        className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500/50 outline-none"
                      >
                        <option value="">Select a model</option>
                        {providersLoading && (
                          <option value="" disabled>Loading models...</option>
                        )}
                        {!providersLoading && availableModels.length === 0 && (
                          <option value="" disabled>No enabled models found. Configure providers in Environment.</option>
                        )}
                        {availableModels.map(({ provider, providerDisplay, modelId, modelName }) => (
                          <option key={`${provider}:${modelId}`} value={`${provider}:${modelId}`}>
                            {providerDisplay}: {modelName}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Cheap Model Selector */}
                    <div>
                      <label className="block text-[10px] font-black text-zinc-600 uppercase mb-2">Cheap Model (for summarisation, optional)</label>
                      <select
                        value={localReasoning?.cheap_model || ''}
                        onChange={handleCheapModelChange}
                        className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500/50 outline-none"
                      >
                        <option value="">Use Global Utility</option>
                        {availableModels.map(({ provider, providerDisplay, modelId, modelName }) => (
                          <option key={`cheap-${provider}:${modelId}`} value={`${provider}:${modelId}`}>
                            {providerDisplay}: {modelName}
                          </option>
                        ))}
                      </select>
                      <p className="text-[10px] text-zinc-500 mt-1">
                        Used for background memory summarisation to save tokens. Leave empty to use the global utility model.
                      </p>
                    </div>

                    <div className="mt-4 border-t border-zinc-800 pt-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-zinc-300">Max Tokens</span>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            className="sr-only peer"
                            checked={localReasoning?.use_custom_max_tokens}
                            onChange={(e) => handleCustomMaxTokensToggle(e.target.checked)}
                          />
                          <div className="w-11 h-6 bg-zinc-700 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                          <span className="ml-3 text-xs font-medium text-zinc-300">
                            {localReasoning?.use_custom_max_tokens ? 'Custom' : 'Default'}
                          </span>
                        </label>
                      </div>
                      {localReasoning?.use_custom_max_tokens && (
                        <div className="mt-2">
                          <input
                            type="number"
                            min="1"
                            max="4096"
                            value={localReasoning?.maxTokens || 150}
                            onChange={(e) => setLocalReasoning({ ...localReasoning, maxTokens: parseInt(e.target.value, 10) })}
                            onBlur={handleMaxTokensBlur}
                            className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200"
                          />
                          <p className="text-[10px] text-zinc-500 mt-1">
                            Maximum number of tokens in the response. When default, the model's default maximum is used.
                          </p>
                        </div>
                      )}
                    </div>

                    <div>
                      <label className="block text-[10px] font-black text-zinc-600 uppercase mb-2">Temperature</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="2"
                        value={localReasoning?.temperature || 0.7}
                        onChange={(e) => setLocalReasoning({ ...localReasoning, temperature: parseFloat(e.target.value) })}
                        onBlur={handleTemperatureBlur}
                        className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200"
                      />
                    </div>

                    <div>
                      <label className="block text-[10px] font-black text-zinc-600 uppercase mb-2">Top P</label>
                      <input
                        type="number"
                        step="0.05"
                        min="0"
                        max="1"
                        value={localReasoning?.topP || 1.0}
                        onChange={(e) => setLocalReasoning({ ...localReasoning, topP: parseFloat(e.target.value) })}
                        onBlur={handleTopPBlur}
                        className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200"
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="bg-zinc-900 rounded-3xl border border-zinc-800 p-8 space-y-6 shadow-xl">
                <h3 className="text-xs font-black uppercase tracking-widest text-emerald-500">Security & Isolation</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-black text-zinc-600 uppercase mb-2">Parent Bot ID</label>
                    <select
                      value={localParentId || ''}
                      onChange={(e) => handleParentChange(e.target.value || undefined)}
                      className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200"
                    >
                      <option value="">None (Root Bot)</option>
                      {allAgents.filter(a => a.id !== agent.id).map(a => (
                        <option key={a.id} value={a.id}>{a.name} ({a.id})</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-black text-zinc-600 uppercase mb-2">Execution UID</label>
                    <input
                      type="text"
                      value={localUid}
                      onChange={(e) => setLocalUid(e.target.value)}
                      onBlur={handleUidBlur}
                      className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200"
                    />
                    <p className="text-[10px] text-zinc-500 mt-2 italic font-medium">Restricts bot access to specified container UID.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Files Tab */}
          {activeTab === 'files' && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 h-[600px] animate-in fade-in duration-300">
              <div className="md:col-span-1 bg-zinc-900 rounded-3xl border border-zinc-800 p-4 space-y-6 flex flex-col overflow-hidden">
                <div className="space-y-4 flex-1 overflow-y-auto">
                  <div className="flex items-center justify-between px-2">
                    <span className="text-[9px] font-black text-zinc-600 uppercase tracking-widest">Bot Files</span>
                    <button 
                      onClick={() => fileInputRef.current?.click()} 
                      disabled={isUploading}
                      className="text-emerald-500 hover:text-emerald-400 disabled:opacity-50"
                    >
                      {isUploading ? (
                        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      ) : (
                        <Icons.Plus />
                      )}
                    </button>
                    <input 
                      type="file" 
                      ref={fileInputRef} 
                      onChange={handleFileUpload} 
                      className="hidden" 
                    />
                  </div>
                  <div className="space-y-1">
                    {agent.localFiles?.map(file => (
                      <div key={file.id} className="flex items-center justify-between p-2 rounded-xl border border-zinc-800 bg-zinc-950">
                        <button 
                          onClick={() => setSelectedFileId(file.id)}
                          className={`flex-1 text-left truncate text-[11px] font-bold ${selectedFileId === file.id && !isGlobalFile ? 'text-emerald-400' : 'text-zinc-500'}`}
                        >
                          <Icons.File className="inline mr-2" /> {file.name}
                        </button>
                        <button 
                          onClick={() => handleDeleteFile(file.id)}
                          className="text-red-500/50 hover:text-red-500 ml-2"
                        >
                          <Icons.Trash className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="md:col-span-3 bg-zinc-900 rounded-3xl border border-zinc-800 p-6 flex flex-col shadow-2xl relative">
                {editingFile ? (
                  <div className="flex-1 flex flex-col">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="text-sm font-bold">{editingFile.name}</h4>
                      <a 
                        href={orchestratorService.getAgentFileDownloadUrl(agent.id, editingFile.id)} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-emerald-500 hover:text-emerald-400 text-xs"
                      >
                        Download
                      </a>
                    </div>
                    {editingFile.type === 'md' || editingFile.type === 'txt' ? (
                      <textarea 
                        value={editingFile.content} 
                        readOnly={isGlobalFile}
                        className="flex-1 w-full bg-zinc-950 border border-zinc-800 rounded-2xl p-4 text-sm font-mono text-zinc-300 resize-none outline-none"
                        spellCheck={false}
                      />
                    ) : (
                      <div className="flex-1 flex items-center justify-center text-zinc-500">
                        Preview not available
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-zinc-600 italic">
                    Select a file to preview
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Logs Tab */}
          {activeTab === 'logs' && (
            <div className="bg-zinc-950 rounded-3xl border border-zinc-800 overflow-hidden flex flex-col h-[600px] shadow-2xl animate-in zoom-in duration-300">
              <div className="p-4 bg-zinc-900/50 border-b border-zinc-800 flex items-center justify-between">
                <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">Hive Standard Output</span>
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div><span className="text-[9px] text-emerald-500 font-black tracking-widest uppercase">Live Stream</span></div>
              </div>
              <div className="flex-1 overflow-y-auto p-6 space-y-3 font-mono text-[12px]">
                {messages.length === 0 && <p className="text-zinc-600 italic text-center py-10">Waiting for next execution cycle...</p>}
                {messages.map(msg => (
                  <div key={msg.id} className={`flex gap-4 border-l-2 pl-4 py-2 ${msg.type === 'error' ? 'text-red-400 border-red-500/50' : msg.type === 'internal' ? 'text-zinc-500 border-zinc-800' : msg.type === 'chat' ? 'text-emerald-300 border-emerald-500/30' : 'text-zinc-400 border-zinc-800'}`}>
                    <span className="opacity-30 whitespace-nowrap text-[10px]">[{new Date(msg.timestamp).toLocaleTimeString()}]</span>
                    <div className="flex flex-col gap-1">
                       <span className="flex-1 whitespace-pre-wrap leading-relaxed">{msg.content}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sub-Bots Tab */}
          {activeTab === 'subagents' && (
            <div className="bg-zinc-900 rounded-3xl border border-zinc-800 p-6 shadow-2xl">
              <h3 className="text-xs font-black uppercase tracking-widest text-emerald-500 mb-4">Sub‑Bots</h3>
              {localSubAgentIds.length === 0 ? (
                <p className="text-zinc-500 italic">No sub‑bots assigned.</p>
              ) : (
                <ul className="space-y-2">
                  {localSubAgentIds.map(id => {
                    const sub = allAgents.find(a => a.id === id);
                    return sub ? (
                      <li key={id} className="flex items-center justify-between p-3 bg-zinc-950 rounded-xl border border-zinc-800">
                        <div>
                          <span className="font-bold text-emerald-400">{sub.name}</span>
                          <span className="text-xs text-zinc-500 ml-2">({sub.id})</span>
                        </div>
                        <span className={`text-[10px] px-2 py-1 rounded-md uppercase font-black ${sub.status === AgentStatus.RUNNING ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-800 text-zinc-500'}`}>{sub.status}</span>
                      </li>
                    ) : null;
                  })}
                </ul>
              )}
              <div className="mt-4 flex">
                <select
                  value={selectedChildId}
                  onChange={(e) => setSelectedChildId(e.target.value)}
                  className="flex-1 bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-2 text-sm text-zinc-200"
                >
                  <option value="">Select bot to add as sub‑bot</option>
                  {allAgents
                    .filter(a => a.id !== agent.id && !localSubAgentIds.includes(a.id))
                    .map(a => (
                      <option key={a.id} value={a.id}>{a.name} ({a.id})</option>
                    ))}
                </select>
                <button
                  onClick={handleAddSubAgent}
                  className="ml-2 px-4 py-2 bg-emerald-600 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-emerald-500 transition-colors"
                >
                  Add
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-8">
          <div className="bg-zinc-900 rounded-3xl border border-zinc-800 p-6 shadow-xl border-l-4 border-l-emerald-500 relative overflow-hidden">
            <h3 className="text-[10px] font-black text-zinc-500 uppercase mb-6 tracking-widest">Bot Health</h3>
            <div className="space-y-6">
              <div className="space-y-2">
                <div className="flex justify-between items-end text-[10px] font-black uppercase">
                  <span className="text-zinc-400">Memory Load</span>
                  <span className="text-emerald-400">{memoryLoad}%</span>
                </div>
                <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500" style={{ width: `${Math.min(100, parseInt(memoryLoad) || 0)}%` }}></div>
                </div>
              </div>
              <p className="text-xs text-zinc-400 italic bg-zinc-950 p-4 rounded-2xl border border-zinc-800">{agent.memory?.summary || "Ready for operation."}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

```

---

## 📄 frontend/src/components/AgentGrid.tsx

```tsx
import React from 'react';
import { Agent, AgentStatus } from '../types';
import { Icons } from '../constants';

interface AgentGridProps {
  agents: Agent[];
  onSelect: (id: string) => void;
}

export const AgentGrid: React.FC<AgentGridProps> = ({ agents, onSelect }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 animate-in fade-in duration-500">
      {agents.map(agent => (
        <div 
          key={agent.id}
          onClick={() => onSelect(agent.id)}
          className="group cursor-pointer bg-zinc-900 border border-zinc-800 hover:border-emerald-500/50 rounded-2xl p-6 transition-all hover:shadow-[0_8px_30px_rgb(0,0,0,0.3)] relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-40 group-hover:text-emerald-500 transition-all transform group-hover:scale-110">
            <Icons.Box />
          </div>
          
          <div className="flex items-center gap-3 mb-6">
            <div className={`w-3 h-3 rounded-full shadow-[0_0_8px_rgba(0,0,0,0.5)] ${
              agent.status === AgentStatus.RUNNING ? 'bg-emerald-500 animate-pulse shadow-emerald-500/50' : 
              agent.status === AgentStatus.ERROR ? 'bg-red-500 shadow-red-500/50' : 'bg-zinc-700'
            }`} />
            <h3 className="font-black text-zinc-100 truncate tracking-tight uppercase text-sm">{agent.name}</h3>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between text-[11px]">
              <span className="text-zinc-500 font-bold uppercase tracking-widest">Role</span>
              <span className="text-zinc-300 font-medium">{agent.role}</span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-zinc-500 font-bold uppercase tracking-widest">Model</span>
              <span className="text-zinc-300 font-mono">
                {typeof agent.reasoning?.model === 'string' && agent.reasoning.model.includes('-') 
                  ? agent.reasoning.model.split('-')[1].toUpperCase() 
                  : (agent.reasoning?.model || 'CUSTOM').toString().toUpperCase()}
              </span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-zinc-500 font-bold uppercase tracking-widest">UID</span>
              <span className="text-emerald-500 font-mono font-bold">{agent.userUid}</span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-zinc-800 flex items-center justify-between text-[10px] font-mono text-zinc-500 uppercase">
            <span className="tracking-tighter">@{agent.containerId}</span>
            <span className="group-hover:text-emerald-400 transition-colors font-bold tracking-widest">Manage Bot →</span>
          </div>
        </div>
      ))}
    </div>
  );
};

```

---

## 📄 frontend/src/components/BridgeManager.tsx

```tsx
import React from 'react';
import { useBridges } from '../contexts/BridgeContext';
import { Icons } from '../constants';

export const BridgeManager: React.FC = () => {
  const { bridges, loading, toggleBridge, restartBridge } = useBridges();

  if (loading) {
    return <div className="text-center py-4 text-zinc-500">Loading bridges...</div>;
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-6 shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 p-8 opacity-5"><Icons.Globe /></div>
      <h3 className="text-xs font-black uppercase tracking-[0.2em] text-emerald-500">Bridge Controllers</h3>
      <p className="text-sm text-zinc-400">
        Enable or disable channel bridges. Only enabled bridges will appear in agent channel configuration.
      </p>
      <div className="space-y-4">
        {bridges.map(bridge => (
          <div key={bridge.type} className="flex items-center justify-between p-4 bg-zinc-950 rounded-xl border border-zinc-800">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-zinc-300 capitalize">{bridge.type}</span>
              <span className={`text-xs px-2 py-1 rounded-full ${
                bridge.status === 'running' ? 'bg-emerald-500/20 text-emerald-400' :
                bridge.status === 'exited' || bridge.status === 'not_found' ? 'bg-red-500/20 text-red-400' :
                bridge.status === 'starting' || bridge.status === 'restarting' ? 'bg-yellow-500/20 text-yellow-400 animate-pulse' :
                'bg-zinc-800 text-zinc-500'
              }`}>
                {bridge.status}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => restartBridge(bridge.type)}
                disabled={!bridge.enabled || bridge.status === 'restarting' || bridge.status === 'starting'}
                className="p-2 text-zinc-500 hover:text-emerald-400 transition-colors disabled:opacity-50"
                title="Restart Bridge"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={bridge.enabled}
                  onChange={e => toggleBridge(bridge.type, e.target.checked)}
                  disabled={bridge.status === 'starting' || bridge.status === 'stopping' || bridge.status === 'restarting'}
                />
                <div className="w-10 h-5 bg-zinc-800 rounded-full peer-checked:bg-emerald-600 transition-all relative">
                  <div className="absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-all peer-checked:left-6"></div>
                </div>
              </label>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

```

---

## 📄 frontend/src/components/Dashboard.tsx

```tsx
import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Hive, Agent, AgentStatus, Message } from '../types';
import { Icons } from '../constants';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { GoogleGenAI } from '@google/genai';

interface DashboardProps {
  hive: Hive;
  onNavigateToNodes: () => void;
  onRunAgent: (agentId: string) => void;
  agents: Agent[];
}

export const Dashboard: React.FC<DashboardProps> = ({ 
  hive, 
  onNavigateToNodes, 
  onRunAgent,
  agents 
}) => {
  const [setupPrompt, setSetupPrompt] = useState('');
  const [isSettingUp, setIsSettingUp] = useState(false);
  const [setupLogs, setSetupLogs] = useState<{ id: string; text: string; type: 'user' | 'ai' | 'system' }[]>([
    { id: '1', text: 'HiveBot Orchestrator initialized. Awaiting auto-setup instructions...', type: 'system' }
  ]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [setupLogs]);

  const handleAutoSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!setupPrompt.trim() || isSettingUp) return;

    const userMsg = setupPrompt;
    setSetupPrompt('');
    setSetupLogs(prev => [...prev, { id: Math.random().toString(36).substr(2, 9), text: userMsg, type: 'user' }]);
    setIsSettingUp(true);

    try {
      setSetupLogs(prev => [...prev, { id: 'loading', text: 'Analyzing hive requirements and generating bot configurations...', type: 'system' }]);
      
      const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || '' });
      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: `You are the HiveBot Orchestrator AI. The user is providing auto-setup instructions for a hive.
        HIVE_NAME: ${hive.name}
        HIVE_DESCRIPTION: ${hive.description}
        USER_INSTRUCTIONS: ${userMsg}
        
        Provide a professional, concise response (under 60 words) explaining how you will configure the hive based on these instructions. Use technical terminology like 'provisioning', 'hierarchical reporting', 'isolated sandboxes', etc.`,
      });
      
      const aiResponse = response.text || "Setup logic processed. Awaiting confirmation.";

      setSetupLogs(prev => prev.filter(l => l.id !== 'loading'));
      setSetupLogs(prev => [...prev, { id: Math.random().toString(36).substr(2, 9), text: aiResponse, type: 'ai' }]);
    } catch (err) {
      setSetupLogs(prev => prev.filter(l => l.id !== 'loading'));
      setSetupLogs(prev => [...prev, { id: Math.random().toString(36).substr(2, 9), text: 'Setup Error: Failed to reach reasoning engine. Check API configuration.', type: 'system' }]);
    } finally {
      setIsSettingUp(false);
    }
  };

  const stats = useMemo(() => {
    const totalTokens = agents.reduce((acc, a) => acc + a.memory.tokenCount, 0);
    const activeNodes = agents.filter(a => a.status === AgentStatus.RUNNING).length;
    const totalNodes = agents.length;
    
    const ramUsage = agents.reduce((acc, a) => acc + (a.status === AgentStatus.RUNNING ? 128 : 32), 0);
    const diskUsage = agents.reduce((acc, a) => acc + 45 + (a.localFiles.length * 2), 0);
    
    return {
      totalTokens,
      activeNodes,
      totalNodes,
      ramUsage,
      diskUsage,
      ramLimit: totalNodes * 256,
      diskLimit: totalNodes * 500
    };
  }, [agents]);

  const chartData = useMemo(() => {
    return agents.map(a => ({
      name: a.name.split(' ')[0],
      tokens: Math.floor(a.memory.tokenCount),
      files: a.localFiles.length
    }));
  }, [agents]);

  return (
    <div className="space-y-8 animate-in fade-in duration-700 pb-20">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-4xl font-black tracking-tighter text-zinc-100 uppercase">
            {hive.name} <span className="text-emerald-500">Dashboard</span>
          </h2>
          <p className="text-zinc-500 font-medium">{hive.description}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-xl flex items-center gap-3 shadow-inner">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Hive Health: Nominal</span>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Cpu /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">Compute Load</p>
          <h3 className="text-3xl font-black text-zinc-100 tracking-tighter">{stats.activeNodes} <span className="text-sm text-zinc-500">/ {stats.totalNodes} Bots</span></h3>
          <div className="mt-4 h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-500 transition-all duration-1000" style={{ width: `${(stats.activeNodes / stats.totalNodes) * 100}%` }}></div>
          </div>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Shield /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">RAM Utilization</p>
          <h3 className="text-3xl font-black text-zinc-100 tracking-tighter">{stats.ramUsage} <span className="text-sm text-zinc-500">MB</span></h3>
          <p className="text-[10px] text-zinc-500 mt-2 font-mono">Limit: {stats.ramLimit} MB</p>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Server /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">Disk Allocation</p>
          <h3 className="text-3xl font-black text-zinc-100 tracking-tighter">{stats.diskUsage} <span className="text-sm text-zinc-500">MB</span></h3>
          <p className="text-[10px] text-zinc-500 mt-2 font-mono">Limit: {stats.diskLimit} MB</p>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Terminal /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">Token Consumption</p>
          <h3 className="text-3xl font-black text-emerald-500 tracking-tighter">{Math.floor(stats.totalTokens).toLocaleString()}</h3>
          <p className="text-[10px] text-zinc-500 mt-2 font-mono">Hive Lifetime Burn</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* AI Auto-Setup Chat */}
        <div className="lg:col-span-1 bg-zinc-900 border border-zinc-800 rounded-3xl p-6 shadow-2xl flex flex-col h-[500px] relative overflow-hidden">
          <div className="absolute top-0 right-0 p-6 opacity-5 pointer-events-none"><Icons.Cpu /></div>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 bg-emerald-500/10 text-emerald-500 rounded-lg flex items-center justify-center"><Icons.Terminal /></div>
            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Auto-Setup AI</h3>
          </div>

          <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2 scrollbar-none">
            {setupLogs.map(log => (
              <div key={log.id} className={`flex ${log.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-3 rounded-2xl text-[11px] leading-relaxed ${
                  log.type === 'user' ? 'bg-emerald-600 text-white rounded-tr-none' : 
                  log.type === 'ai' ? 'bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-tl-none' : 
                  'bg-zinc-950/50 text-zinc-500 italic text-center w-full border border-zinc-800/50'
                }`}>
                  {log.text}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          <form onSubmit={handleAutoSetup} className="relative">
            <input 
              type="text" 
              value={setupPrompt}
              onChange={(e) => setSetupPrompt(e.target.value)}
              disabled={isSettingUp}
              placeholder="Enter setup instructions..."
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl pl-4 pr-12 py-3 text-xs text-zinc-200 focus:border-emerald-500/50 outline-none transition-all"
            />
            <button 
              type="submit"
              disabled={isSettingUp || !setupPrompt.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-emerald-500 hover:text-emerald-400 disabled:opacity-30 transition-all"
            >
              {isSettingUp ? <div className="w-4 h-4 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" /> : <Icons.Shield />}
            </button>
          </form>
        </div>

        {/* Token Distribution Chart */}
        <div className="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-3xl p-8 shadow-2xl space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Bot Token Distribution</h3>
            <button onClick={onNavigateToNodes} className="text-[10px] font-black text-emerald-500 uppercase tracking-widest hover:text-emerald-400 transition-colors">View All Bots →</button>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                <XAxis dataKey="name" stroke="#71717a" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#71717a" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '12px' }}
                  itemStyle={{ color: '#10b981', fontSize: '12px', fontWeight: 'bold' }}
                />
                <Bar dataKey="tokens" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Hive Map / Topology */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 shadow-2xl space-y-6 flex flex-col">
          <h3 className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Hive Topology</h3>
          <div className="flex-1 relative bg-zinc-950 rounded-2xl border border-zinc-800/50 overflow-hidden p-4">
            <div className="absolute inset-0 opacity-20 pointer-events-none" style={{ backgroundImage: 'radial-gradient(#10b981 0.5px, transparent 0.5px)', backgroundSize: '20px 20px' }}></div>
            <div className="relative h-full flex flex-col items-center justify-center gap-8">
              {/* Simple Visual Topology */}
              <div className="w-12 h-12 bg-emerald-500/20 border border-emerald-500 text-emerald-500 rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.2)]">
                <Icons.Shield />
              </div>
              <div className="w-px h-8 bg-gradient-to-b from-emerald-500 to-transparent"></div>
              <div className="flex gap-4">
                {agents.slice(0, 3).map((a, i) => (
                  <div key={a.id} className="flex flex-col items-center gap-2">
                    <div className={`w-8 h-8 rounded-lg border flex items-center justify-center text-[10px] font-black ${a.status === AgentStatus.RUNNING ? 'bg-emerald-500/10 border-emerald-500 text-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 'bg-zinc-800 border-zinc-700 text-zinc-500'}`}>
                      {i + 1}
                    </div>
                    <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-tighter truncate w-12 text-center">{a.name.split(' ')[0]}</span>
                  </div>
                ))}
                {agents.length > 3 && (
                  <div className="w-8 h-8 rounded-lg border border-zinc-800 bg-zinc-900 flex items-center justify-center text-[10px] font-black text-zinc-600">
                    +{agents.length - 3}
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="pt-4 border-t border-zinc-800">
             <div className="flex items-center justify-between text-[10px]">
               <span className="text-zinc-500 font-bold uppercase tracking-widest">Hive Root</span>
               <span className="text-emerald-500 font-mono font-bold">ACTIVE</span>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};

```

---

## 📄 frontend/src/components/GlobalConfig.tsx

```tsx
import React, { useState } from 'react';
import { Hive, UserAccount, GlobalSettings, UserRole } from '../types';
import { Icons } from '../constants';
import { HiveMindDashboard } from './HiveMindDashboard';

interface GlobalConfigProps {
  hives: Hive[];
  users: UserAccount[];
  settings: GlobalSettings;
  onUpdateUsers: (users: UserAccount[]) => void;
  onUpdateSettings: (settings: GlobalSettings) => void;
}

interface UserModalProps {
  user?: UserAccount;
  hives: Hive[];
  onClose: () => void;
  onSave: (user: UserAccount) => void;
}

const UserModal: React.FC<UserModalProps> = ({ user, hives, onClose, onSave }) => {
  const [username, setUsername] = useState(user?.username || '');
  const [password, setPassword] = useState(user?.password || '');
  const [role, setRole] = useState<UserRole>(user?.role || UserRole.HIVE_USER);
  const [assignedHiveIds, setAssignedHiveIds] = useState<string[]>(user?.assignedProjectIds || []);

  const handleToggleHive = (id: string) => {
    setAssignedHiveIds(prev => 
      prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
    );
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 w-full max-w-md space-y-6 shadow-2xl animate-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-black uppercase tracking-tighter">{user ? 'Edit User' : 'Create User'}</h3>
          <button onClick={onClose} className="text-zinc-500 hover:text-white transition-colors"><Icons.X /></button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-2">Username</label>
            <input 
              type="text" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 outline-none transition-all"
              placeholder="Enter username"
            />
          </div>

          <div>
            <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-2">Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 outline-none transition-all"
              placeholder={user ? "Leave blank to keep current" : "Enter password"}
            />
          </div>

          <div>
            <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-2">Role</label>
            <select 
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 outline-none transition-all appearance-none"
            >
              <option value={UserRole.GLOBAL_ADMIN}>Global Admin</option>
              <option value={UserRole.HIVE_ADMIN}>Hive Admin</option>
              <option value={UserRole.HIVE_USER}>Hive User</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-2">Assigned Hives</label>
            <div className="space-y-2 max-h-40 overflow-y-auto p-2 bg-zinc-950 border border-zinc-800 rounded-xl">
              {hives.map(h => (
                <button
                  key={h.id}
                  onClick={() => handleToggleHive(h.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs transition-all ${
                    assignedHiveIds.includes(h.id) ? 'bg-emerald-500/10 text-emerald-400' : 'text-zinc-500 hover:bg-zinc-900'
                  }`}
                >
                  <span>{h.name}</span>
                  {assignedHiveIds.includes(h.id) && <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex gap-3 pt-4">
          <button 
            onClick={onClose}
            className="flex-1 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all"
          >
            Cancel
          </button>
          <button 
            onClick={() => onSave({
              id: user?.id || Math.random().toString(36).substr(2, 9),
              username,
              password: password || user?.password,
              role,
              assignedProjectIds: assignedHiveIds,
              createdAt: user?.createdAt || new Date().toISOString()
            })}
            className="flex-1 px-4 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-emerald-900/20"
          >
            Save User
          </button>
        </div>
      </div>
    </div>
  );
};

export const GlobalConfig: React.FC<GlobalConfigProps> = ({ 
  hives, 
  users, 
  settings, 
  onUpdateUsers, 
  onUpdateSettings 
}) => {
  const [activeTab, setActiveTab] = useState<'hive-mind' | 'users' | 'settings' | 'logs'>('hive-mind');
  const [editingUser, setEditingUser] = useState<UserAccount | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const [logs] = useState([
    { id: 1, event: 'System Boot', user: 'SYSTEM', timestamp: new Date().toISOString(), status: 'SUCCESS' },
    { id: 2, event: 'User Login', user: 'admin', timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(), status: 'SUCCESS' },
    { id: 3, event: 'Hive Created', user: 'admin', timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(), status: 'SUCCESS' },
    { id: 4, event: 'Vector Sync', user: 'SYSTEM', timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(), status: 'SUCCESS' },
  ]);

  const handleSaveUser = (user: UserAccount) => {
    if (isCreating) {
      onUpdateUsers([...users, user]);
    } else {
      onUpdateUsers(users.map(u => u.id === user.id ? user : u));
    }
    setEditingUser(null);
    setIsCreating(false);
  };

  const handleDeleteUser = (id: string) => {
    if (confirm('Are you sure you want to delete this user?')) {
      onUpdateUsers(users.filter(u => u.id !== id));
    }
  };

  return (
    <div className="flex flex-col h-full animate-in fade-in duration-500">
      {/* Global Config Top Nav */}
      <div className="flex items-center justify-between mb-8 pb-4 border-b border-zinc-800">
        <div className="flex items-center gap-6">
          <button 
            onClick={() => setActiveTab('hive-mind')}
            className={`text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'hive-mind' ? 'text-emerald-400' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            Hive Mind
          </button>
          <button 
            onClick={() => setActiveTab('users')}
            className={`text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'users' ? 'text-emerald-400' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            Users
          </button>
          <button 
            onClick={() => setActiveTab('settings')}
            className={`text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'settings' ? 'text-emerald-400' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            Settings
          </button>
          <button 
            onClick={() => setActiveTab('logs')}
            className={`text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'logs' ? 'text-emerald-400' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            Audit Logs
          </button>
        </div>
        
        <div className="flex items-center gap-3 px-4 py-1.5 bg-zinc-900/50 border border-zinc-800 rounded-xl">
          <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></div>
          <span className="text-[9px] font-black uppercase tracking-widest text-zinc-500">Global Admin Mode</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {activeTab === 'hive-mind' && <HiveMindDashboard hives={hives} />}
        
        {activeTab === 'users' && (
          <div className="space-y-8 max-w-5xl mx-auto">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-black tracking-tighter uppercase">User Management</h3>
                <p className="text-zinc-500 text-sm">Manage operator accounts and access levels.</p>
              </div>
              <button 
                onClick={() => setIsCreating(true)}
                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-emerald-900/20"
              >
                <Icons.Plus /> Create User
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {users.map(user => (
                <div key={user.id} className="bg-zinc-900 border border-zinc-800 rounded-3xl p-6 relative group hover:border-emerald-500/30 transition-all">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-zinc-800 rounded-2xl flex items-center justify-center text-zinc-400">
                      <Icons.User />
                    </div>
                    <div>
                      <h4 className="font-bold text-zinc-200">{user.username}</h4>
                      <span className={`px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-widest ${
                        user.role === UserRole.GLOBAL_ADMIN ? 'bg-purple-500/10 text-purple-400' :
                        user.role === UserRole.HIVE_ADMIN ? 'bg-blue-500/10 text-blue-400' :
                        'bg-zinc-500/10 text-zinc-400'
                      }`}>
                        {user.role.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-3 pt-4 border-t border-zinc-800/50">
                    <div>
                      <p className="text-[9px] font-black text-zinc-500 uppercase tracking-widest mb-1">Assigned Hives</p>
                      <div className="flex flex-wrap gap-1">
                        {(user.assignedProjectIds || []).length > 0 ? (
                          (user.assignedProjectIds || []).map(pid => {
                            const h = hives.find(h => h.id === pid);
                            return (
                              <span key={pid} className="px-1.5 py-0.5 bg-zinc-800 text-zinc-400 rounded text-[9px] font-bold">
                                {h?.name || pid}
                              </span>
                            );
                          })
                        ) : (
                          <span className="text-[9px] text-zinc-600 italic">No access</span>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex justify-between text-[10px]">
                      <span className="text-zinc-500 uppercase font-bold">Created</span>
                      <span className="text-zinc-400 font-mono">{new Date(user.createdAt).toLocaleDateString()}</span>
                    </div>
                  </div>

                  <div className="absolute top-4 right-4 flex gap-1 opacity-0 group-hover:opacity-100 transition-all">
                    <button 
                      onClick={() => setEditingUser(user)}
                      className="p-2 text-zinc-600 hover:text-white hover:bg-zinc-800 rounded-lg"
                    >
                      <Icons.Settings />
                    </button>
                    <button 
                      onClick={() => handleDeleteUser(user.id)}
                      className="p-2 text-zinc-600 hover:text-red-400 hover:bg-red-500/10 rounded-lg"
                    >
                      <Icons.Trash />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {(isCreating || editingUser) && (
          <UserModal 
            user={editingUser || undefined}
            hives={hives}
            onClose={() => { setEditingUser(null); setIsCreating(false); }}
            onSave={handleSaveUser}
          />
        )}

        {activeTab === 'settings' && (
          <div className="space-y-8 max-w-3xl mx-auto">
            <div className="space-y-2">
              <h3 className="text-2xl font-black tracking-tighter uppercase">System Settings</h3>
              <p className="text-zinc-500 text-sm">Global security and behavioral parameters.</p>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-8 shadow-2xl">
              <div className="flex items-center justify-between p-4 bg-zinc-950 border border-zinc-800 rounded-2xl">
                <div>
                  <p className="text-xs font-bold text-zinc-200">Login Gateway</p>
                  <p className="text-[10px] text-zinc-500">Enable mandatory authentication for all sessions.</p>
                </div>
                <button 
                  onClick={() => onUpdateSettings({ ...settings, loginEnabled: !settings.loginEnabled })}
                  className={`w-12 h-6 rounded-full relative transition-all ${settings.loginEnabled ? 'bg-emerald-600' : 'bg-zinc-800'}`}
                >
                  <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${settings.loginEnabled ? 'left-7' : 'left-1'}`} />
                </button>
              </div>

              <div className="space-y-4">
                <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest">Session Timeout (Minutes)</label>
                <div className="flex items-center gap-4">
                  <input 
                    type="range" 
                    min="5" 
                    max="120" 
                    step="5"
                    value={settings.sessionTimeout}
                    onChange={(e) => onUpdateSettings({ ...settings, sessionTimeout: parseInt(e.target.value) })}
                    className="flex-1 accent-emerald-500"
                  />
                  <span className="w-12 text-center font-mono text-emerald-400 font-bold">{settings.sessionTimeout}m</span>
                </div>
                <p className="text-[10px] text-zinc-500 italic">Interval before the login page is automatically reactivated due to inactivity.</p>
              </div>

              <div className="space-y-4">
                <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest">System Identity</label>
                <input 
                  type="text" 
                  value={settings.systemName}
                  onChange={(e) => onUpdateSettings({ ...settings, systemName: e.target.value })}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 outline-none transition-all"
                  placeholder="HiveBot Orchestrator"
                />
              </div>

              <div className="flex items-center justify-between p-4 bg-zinc-950 border border-zinc-800 rounded-2xl">
                <div>
                  <p className="text-xs font-bold text-zinc-200">Maintenance Mode</p>
                  <p className="text-[10px] text-zinc-500">Restrict access to hive operations during updates.</p>
                </div>
                <button 
                  onClick={() => onUpdateSettings({ ...settings, maintenanceMode: !settings.maintenanceMode })}
                  className={`w-12 h-6 rounded-full relative transition-all ${settings.maintenanceMode ? 'bg-amber-600' : 'bg-zinc-800'}`}
                >
                  <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${settings.maintenanceMode ? 'left-7' : 'left-1'}`} />
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="space-y-8 max-w-5xl mx-auto">
            <div className="space-y-2">
              <h3 className="text-2xl font-black tracking-tighter uppercase">Audit Trail</h3>
              <p className="text-zinc-500 text-sm">Real-time system event monitoring.</p>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-3xl overflow-hidden shadow-2xl">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-zinc-950/50 border-b border-zinc-800">
                    <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-zinc-500">Timestamp</th>
                    <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-zinc-500">Event</th>
                    <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-zinc-500">User</th>
                    <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-zinc-500">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/50">
                  {logs.map(log => (
                    <tr key={log.id} className="hover:bg-zinc-800/30 transition-colors">
                      <td className="px-6 py-4 text-[10px] font-mono text-zinc-400">{new Date(log.timestamp).toLocaleString()}</td>
                      <td className="px-6 py-4 text-xs font-bold text-zinc-200">{log.event}</td>
                      <td className="px-6 py-4 text-xs text-zinc-400">{log.user}</td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-1 bg-emerald-500/10 text-emerald-500 rounded text-[9px] font-black uppercase tracking-widest">
                          {log.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

```

---

## 📄 frontend/src/components/GlobalFiles.tsx

```tsx
import React, { useState, useEffect, useRef } from 'react';
import { FileEntry } from '../types';
import { orchestratorService } from '../services/orchestratorService';
import { Icons } from '../constants';

interface GlobalFilesProps {
  onError?: (error: string) => void;
}

export const GlobalFiles: React.FC<GlobalFilesProps> = ({ onError }) => {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadFiles = async () => {
    try {
      const data = await orchestratorService.listGlobalFiles();
      setFiles(data);
    } catch (err) {
      console.error('Failed to load global files', err);
      onError?.('Failed to load global files');
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    try {
      await orchestratorService.uploadGlobalFile(file);
      await loadFiles();
    } catch (err) {
      console.error('File upload failed', err);
      onError?.('File upload failed');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteFile = async (filename: string) => {
    if (!confirm(`Delete ${filename}?`)) return;
    try {
      await orchestratorService.deleteGlobalFile(filename);
      await loadFiles();
    } catch (err) {
      console.error('File deletion failed', err);
      onError?.('File deletion failed');
    }
  };

  return (
    <div className="bg-zinc-900 rounded-3xl border border-zinc-800 p-6 shadow-2xl">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-black tracking-tight text-emerald-500">Global Files</h3>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-emerald-500 transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          {isUploading ? (
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <Icons.Plus />
          )}
          Upload File
        </button>
        <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" />
      </div>

      <div className="space-y-2">
        {files.length === 0 && (
          <p className="text-zinc-500 italic text-center py-8">No global files uploaded.</p>
        )}
        {files.map(file => (
          <div key={file.id} className="flex items-center justify-between p-3 bg-zinc-950 rounded-xl border border-zinc-800">
            <div className="flex items-center gap-3">
              <Icons.File className="text-emerald-500" />
              <span className="text-sm font-medium text-zinc-300">{file.name}</span>
              <span className="text-[10px] text-zinc-500">({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
            <div className="flex items-center gap-2">
              <a
                href={orchestratorService.getGlobalFileDownloadUrl(file.name)}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 text-zinc-500 hover:text-emerald-400 transition-colors"
                title="Download"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </a>
              <button
                onClick={() => handleDeleteFile(file.name)}
                className="p-2 text-zinc-500 hover:text-red-500 transition-colors"
                title="Delete"
              >
                <Icons.Trash className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

```

---

## 📄 frontend/src/components/GlobalStats.tsx

```tsx

import React from 'react';
import { Agent, AgentStatus } from '../types';

export const GlobalStats: React.FC<{ agents: Agent[] }> = ({ agents }) => {
  const activeCount = agents.filter(a => a.status === AgentStatus.RUNNING).length;
  const totalTokens = agents.reduce((acc, a) => acc + a.memory.tokenCount, 0);

  return (
    <div className="flex items-center gap-6">
      <div className="flex flex-col items-end">
        <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-tighter">Active Containers</span>
        <span className="text-sm font-mono text-emerald-400">{activeCount} / {agents.length}</span>
      </div>
      <div className="w-px h-6 bg-zinc-800"></div>
      <div className="flex flex-col items-end">
        <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-tighter">Global Burn</span>
        <span className="text-sm font-mono text-zinc-200">{Math.floor(totalTokens)} <span className="text-xs opacity-50">tokens</span></span>
      </div>
    </div>
  );
};

```

---

## 📄 frontend/src/components/HiveMindDashboard.tsx

```tsx
import React, { useMemo } from 'react';
import { Hive, HiveMindAccessLevel } from '../types';
import { Icons } from '../constants';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface HiveMindDashboardProps {
  hives: Hive[];
}

export const HiveMindDashboard: React.FC<HiveMindDashboardProps> = ({ hives }) => {
  const stats = useMemo(() => {
    const totalFiles = hives.reduce((acc, h) => acc + h.globalFiles.length, 0);
    const totalAgents = hives.reduce((acc, h) => acc + h.agents.length, 0);
    const totalVectors = totalFiles * 42; // Simulated vector count
    
    const accessDistribution = hives.reduce((acc, h) => {
      const level = h.hiveMindConfig?.accessLevel || HiveMindAccessLevel.ISOLATED;
      acc[level] = (acc[level] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const pieData = [
      { name: 'Isolated', value: accessDistribution[HiveMindAccessLevel.ISOLATED] || 0, color: '#71717a' },
      { name: 'Shared', value: accessDistribution[HiveMindAccessLevel.SHARED] || 0, color: '#10b981' },
      { name: 'Global', value: accessDistribution[HiveMindAccessLevel.GLOBAL] || 0, color: '#3b82f6' },
    ].filter(d => d.value > 0);

    return {
      totalFiles,
      totalAgents,
      totalVectors,
      pieData
    };
  }, [hives]);

  return (
    <div className="space-y-8 animate-in fade-in duration-700 pb-20">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-4xl font-black tracking-tighter text-zinc-100 uppercase">
            Hive <span className="text-emerald-500">Mind</span>
          </h2>
          <p className="text-zinc-500 font-medium">Global RAG & Privacy-First Vector Store Status</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-xl flex items-center gap-3 shadow-inner">
            <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
            <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Neural Sync: Active</span>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Layers /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">Knowledge Base</p>
          <h3 className="text-3xl font-black text-zinc-100 tracking-tighter">{stats.totalFiles} <span className="text-sm text-zinc-500">Indexed Files</span></h3>
          <p className="text-[10px] text-zinc-500 mt-2 font-mono">Across {hives.length} Hives</p>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Cpu /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">Neural Nodes</p>
          <h3 className="text-3xl font-black text-zinc-100 tracking-tighter">{stats.totalAgents} <span className="text-sm text-zinc-500">Active Brains</span></h3>
          <p className="text-[10px] text-zinc-500 mt-2 font-mono">Connected to Hive Mind</p>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Shield /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">Vector Density</p>
          <h3 className="text-3xl font-black text-zinc-100 tracking-tighter">{stats.totalVectors.toLocaleString()} <span className="text-sm text-zinc-500">Embeddings</span></h3>
          <p className="text-[10px] text-zinc-500 mt-2 font-mono">Privacy-First Local Store</p>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Terminal /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">Inference Speed</p>
          <h3 className="text-3xl font-black text-blue-500 tracking-tighter">14ms</h3>
          <p className="text-[10px] text-zinc-500 mt-2 font-mono">Local RAG Latency</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Access Distribution */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 shadow-2xl space-y-6 flex flex-col items-center">
          <h3 className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500 w-full">Privacy Segmentation</h3>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {stats.pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '12px' }}
                  itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex gap-4 text-[10px] font-black uppercase tracking-widest">
            {stats.pieData.map(d => (
              <div key={d.name} className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }}></div>
                <span className="text-zinc-400">{d.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Hive Knowledge Base */}
        <div className="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-3xl p-8 shadow-2xl space-y-6">
          <h3 className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Hive Knowledge Density</h3>
          <div className="space-y-4">
            {hives.map(h => (
              <div key={h.id} className="p-4 bg-zinc-950 border border-zinc-800 rounded-2xl flex items-center justify-between group hover:border-emerald-500/30 transition-all">
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    h.hiveMindConfig?.accessLevel === HiveMindAccessLevel.GLOBAL ? 'bg-blue-500/10 text-blue-500' :
                    h.hiveMindConfig?.accessLevel === HiveMindAccessLevel.SHARED ? 'bg-emerald-500/10 text-emerald-500' :
                    'bg-zinc-800 text-zinc-500'
                  }`}>
                    <Icons.Layers />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-zinc-200">{h.name}</h4>
                    <p className="text-[10px] text-zinc-500 uppercase tracking-widest font-black">
                      {h.hiveMindConfig?.accessLevel || HiveMindAccessLevel.ISOLATED} ACCESS
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-xs font-mono text-zinc-400">{h.globalFiles.length} Files</span>
                  <div className="flex gap-1 mt-1">
                    {Array.from({ length: Math.min(5, h.globalFiles.length) }).map((_, i) => (
                      <div key={i} className="w-1 h-1 rounded-full bg-emerald-500/50"></div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

```

---

## 📄 frontend/src/components/HiveTeam.tsx

```tsx
import React, { useState } from 'react';
import { Hive, UserAccount, UserRole } from '../types';
import { Icons } from '../constants';

interface HiveTeamProps {
  hive: Hive;
  allUsers: UserAccount[];
  onUpdateUsers: (users: UserAccount[]) => void;
}

export const HiveTeam: React.FC<HiveTeamProps> = ({ 
  hive, 
  allUsers, 
  onUpdateUsers
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const hiveUsers = allUsers.filter(u => (u.assignedProjectIds || []).includes(hive.id));
  const nonHiveUsers = allUsers.filter(u => !(u.assignedProjectIds || []).includes(hive.id));

  const handleAddExistingUser = (userId: string) => {
    const updatedUsers = allUsers.map(u => {
      if (u.id === userId) {
        const assigned = u.assignedProjectIds || [];
        return { ...u, assignedProjectIds: [...assigned, hive.id] };
      }
      return u;
    });
    onUpdateUsers(updatedUsers);
    setIsAdding(false);
  };

  const handleCreateUser = () => {
    if (!newUsername || !newPassword) return;
    const newUser: UserAccount = {
      id: Math.random().toString(36).substr(2, 9),
      username: newUsername,
      password: newPassword,
      role: UserRole.HIVE_USER,
      assignedProjectIds: [hive.id],
      createdAt: new Date().toISOString()
    };
    onUpdateUsers([...allUsers, newUser]);
    setNewUsername('');
    setNewPassword('');
    setIsAdding(false);
  };

  const handleRemoveUser = (userId: string) => {
    const updatedUsers = allUsers.map(u => {
      if (u.id === userId) {
        const assigned = u.assignedProjectIds || [];
        return { ...u, assignedProjectIds: assigned.filter(id => id !== hive.id) };
      }
      return u;
    });
    onUpdateUsers(updatedUsers);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h2 className="text-3xl md:text-5xl font-black tracking-tighter uppercase">Hive <span className="text-emerald-500">Team</span></h2>
          <p className="text-zinc-500 text-base md:text-lg">Manage operators assigned to this hive.</p>
        </div>
        <button 
          onClick={() => setIsAdding(true)}
          className="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-emerald-900/20 flex items-center gap-2"
        >
          <Icons.Plus /> Add Member
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {hiveUsers.map(user => (
          <div key={user.id} className="bg-zinc-900 border border-zinc-800 rounded-3xl p-6 relative group hover:border-emerald-500/30 transition-all">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-zinc-800 rounded-2xl flex items-center justify-center text-zinc-400">
                <Icons.User />
              </div>
              <div>
                <h4 className="font-bold text-zinc-200">{user.username}</h4>
                <span className={`px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-widest ${
                  user.role === UserRole.GLOBAL_ADMIN ? 'bg-purple-500/10 text-purple-400' :
                  user.role === UserRole.HIVE_ADMIN ? 'bg-blue-500/10 text-blue-400' :
                  'bg-zinc-500/10 text-zinc-400'
                }`}>
                  {user.role.replace('_', ' ')}
                </span>
              </div>
            </div>
            
            <div className="flex justify-between text-[10px] pt-4 border-t border-zinc-800/50">
              <span className="text-zinc-500 uppercase font-bold">Joined Team</span>
              <span className="text-zinc-400 font-mono">{new Date(user.createdAt).toLocaleDateString()}</span>
            </div>

            <button 
              onClick={() => handleRemoveUser(user.id)}
              className="absolute top-4 right-4 p-2 text-zinc-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
              title="Remove from Hive"
            >
              <Icons.Trash />
            </button>
          </div>
        ))}
      </div>

      {isAdding && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 w-full max-w-md space-y-6 shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-black uppercase tracking-tighter">Add Team Member</h3>
              <button onClick={() => setIsAdding(false)} className="text-zinc-500 hover:text-white transition-colors"><Icons.X /></button>
            </div>

            <div className="space-y-6">
              {nonHiveUsers.length > 0 && (
                <div>
                  <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-3">Add Existing Operator</label>
                  <div className="space-y-2 max-h-40 overflow-y-auto p-2 bg-zinc-950 border border-zinc-800 rounded-xl">
                    {nonHiveUsers.map(u => (
                      <button
                        key={u.id}
                        onClick={() => handleAddExistingUser(u.id)}
                        className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200 transition-all"
                      >
                        <span>{u.username}</span>
                        <span className="text-[8px] opacity-50">{u.role}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="relative">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-zinc-800"></div></div>
                <div className="relative flex justify-center text-[10px] uppercase font-black text-zinc-600"><span className="bg-zinc-900 px-2">Or Create New</span></div>
              </div>

              <div>
                <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-2">New Username</label>
                <input 
                  type="text" 
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 outline-none transition-all mb-4"
                  placeholder="Enter username"
                />
                
                <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-2">Password</label>
                <input 
                  type="password" 
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 outline-none transition-all"
                  placeholder="Enter password"
                />
                <p className="mt-2 text-[9px] text-zinc-500 italic">New users created here are assigned the HIVE USER role by default.</p>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <button 
                onClick={() => setIsAdding(false)}
                className="flex-1 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all"
              >
                Cancel
              </button>
              <button 
                onClick={handleCreateUser}
                disabled={!newUsername || !newPassword}
                className="flex-1 px-4 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-emerald-900/20"
              >
                Create & Add
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

```

---

## 📄 frontend/src/components/LoginPage.tsx

```tsx
import React, { useState } from 'react';
import { Icons } from '../constants';
import { motion } from 'framer-motion';

interface LoginPageProps {
  onLogin: (username: string) => void;
  onValidate: (username: string, password: string) => boolean;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLogin, onValidate }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    // Authentication logic
    setTimeout(() => {
      if (onValidate(username, password)) {
        onLogin(username);
      } else {
        setError('INVALID_CREDENTIALS: Access Denied by Orchestrator');
        setIsLoading(false);
      }
    }, 1000);
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-zinc-950 relative overflow-hidden font-sans">
      {/* Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-500/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-emerald-500/5 blur-[120px] rounded-full" />
        <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(#10b981 0.5px, transparent 0.5px)', backgroundSize: '30px 30px' }} />
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="w-full max-w-md p-8 relative z-10"
      >
        <div className="text-center mb-12">
          <div className="inline-flex p-4 bg-emerald-500/10 text-emerald-500 rounded-2xl mb-6 shadow-inner border border-emerald-500/20">
            <Icons.Shield />
          </div>
          <h1 className="text-4xl font-black tracking-tighter text-white uppercase mb-2">
            Hive<span className="text-emerald-500">Bot</span>
          </h1>
          <p className="text-zinc-500 text-sm font-bold uppercase tracking-[0.2em]">Security Gateway v4.2</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest ml-1">Operator ID</label>
            <div className="relative">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600">
                <Icons.User />
              </div>
              <input 
                type="text" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-zinc-900/50 border border-zinc-800 rounded-2xl pl-12 pr-4 py-4 text-zinc-100 focus:border-emerald-500 focus:outline-none transition-all shadow-inner"
                placeholder="Enter UID..."
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest ml-1">Access Key</label>
            <div className="relative">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600">
                <Icons.Shield />
              </div>
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-zinc-900/50 border border-zinc-800 rounded-2xl pl-12 pr-4 py-4 text-zinc-100 focus:border-emerald-500 focus:outline-none transition-all shadow-inner"
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          {error && (
            <motion.div 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-[10px] font-black uppercase tracking-widest text-center"
            >
              {error}
            </motion.div>
          )}

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-800 text-white font-black uppercase tracking-widest py-4 rounded-2xl transition-all shadow-lg shadow-emerald-900/20 flex items-center justify-center gap-3 group"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                Authorize Session
                <span className="group-hover:translate-x-1 transition-transform">→</span>
              </>
            )}
          </button>
        </form>

        <div className="mt-12 pt-8 border-t border-zinc-900 flex flex-col items-center gap-4">
          <p className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest">Authorized Access Only</p>
          <div className="flex gap-6">
            <div className="flex items-center gap-2 text-[9px] text-zinc-700 font-mono">
              <div className="w-1 h-1 rounded-full bg-emerald-500/50" />
              ENCRYPTED
            </div>
            <div className="flex items-center gap-2 text-[9px] text-zinc-700 font-mono">
              <div className="w-1 h-1 rounded-full bg-emerald-500/50" />
              ISOLATED
            </div>
            <div className="flex items-center gap-2 text-[9px] text-zinc-700 font-mono">
              <div className="w-1 h-1 rounded-full bg-emerald-500/50" />
              AUDITED
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

```

---

## 📄 frontend/src/components/ProjectTeam.tsx

```tsx
import React, { useState } from 'react';
import { Project, UserAccount, UserRole } from '../types';
import { Icons } from '../constants';

interface ProjectTeamProps {
  project: Project;
  allUsers: UserAccount[];
  onUpdateUsers: (users: UserAccount[]) => void;
  currentUser: UserAccount;
}

export const ProjectTeam: React.FC<ProjectTeamProps> = ({ 
  project, 
  allUsers, 
  onUpdateUsers,
  currentUser
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const projectUsers = allUsers.filter(u => (u.assignedProjectIds || []).includes(project.id));
  const nonProjectUsers = allUsers.filter(u => !(u.assignedProjectIds || []).includes(project.id));

  const handleAddExistingUser = (userId: string) => {
    const updatedUsers = allUsers.map(u => {
      if (u.id === userId) {
        const assigned = u.assignedProjectIds || [];
        return { ...u, assignedProjectIds: [...assigned, project.id] };
      }
      return u;
    });
    onUpdateUsers(updatedUsers);
  };

  const handleCreateUser = () => {
    if (!newUsername || !newPassword) return;
    const newUser: UserAccount = {
      id: Math.random().toString(36).substr(2, 9),
      username: newUsername,
      password: newPassword,
      role: 'HIVE_USER',
      assignedProjectIds: [project.id],
      createdAt: new Date().toISOString()
    };
    onUpdateUsers([...allUsers, newUser]);
    setNewUsername('');
    setNewPassword('');
    setIsAdding(false);
  };

  const handleRemoveUser = (userId: string) => {
    if (userId === currentUser.id) return; // Can't remove self
    const updatedUsers = allUsers.map(u => {
      if (u.id === userId) {
        const assigned = u.assignedProjectIds || [];
        return { ...u, assignedProjectIds: assigned.filter(id => id !== project.id) };
      }
      return u;
    });
    onUpdateUsers(updatedUsers);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h2 className="text-3xl md:text-5xl font-black tracking-tighter uppercase">Hive <span className="text-emerald-500">Team</span></h2>
          <p className="text-zinc-500 text-base md:text-lg">Manage operators assigned to this hive.</p>
        </div>
        <button 
          onClick={() => setIsAdding(true)}
          className="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-emerald-900/20 flex items-center gap-2"
        >
          <Icons.Plus /> Add Member
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projectUsers.map(user => (
          <div key={user.id} className="bg-zinc-900 border border-zinc-800 rounded-3xl p-6 relative group hover:border-emerald-500/30 transition-all">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-zinc-800 rounded-2xl flex items-center justify-center text-zinc-400">
                <Icons.User />
              </div>
              <div>
                <h4 className="font-bold text-zinc-200">{user.username}</h4>
                <span className={`px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-widest ${
                  user.role === 'GLOBAL_ADMIN' ? 'bg-purple-500/10 text-purple-400' :
                  user.role === 'HIVE_ADMIN' ? 'bg-blue-500/10 text-blue-400' :
                  'bg-zinc-500/10 text-zinc-400'
                }`}>
                  {user.role.replace('_', ' ')}
                </span>
              </div>
            </div>
            
            <div className="flex justify-between text-[10px] pt-4 border-t border-zinc-800/50">
              <span className="text-zinc-500 uppercase font-bold">Joined Team</span>
              <span className="text-zinc-400 font-mono">{new Date(user.createdAt).toLocaleDateString()}</span>
            </div>

            {user.id !== currentUser.id && (
              <button 
                onClick={() => handleRemoveUser(user.id)}
                className="absolute top-4 right-4 p-2 text-zinc-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                title="Remove from Hive"
              >
                <Icons.Trash />
              </button>
            )}
          </div>
        ))}
      </div>

      {isAdding && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 w-full max-w-md space-y-6 shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-black uppercase tracking-tighter">Add Team Member</h3>
              <button onClick={() => setIsAdding(false)} className="text-zinc-500 hover:text-white transition-colors"><Icons.X /></button>
            </div>

            <div className="space-y-6">
              {nonProjectUsers.length > 0 && (
                <div>
                  <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-3">Add Existing Operator</label>
                  <div className="space-y-2 max-h-40 overflow-y-auto p-2 bg-zinc-950 border border-zinc-800 rounded-xl">
                    {nonProjectUsers.map(u => (
                      <button
                        key={u.id}
                        onClick={() => { handleAddExistingUser(u.id); setIsAdding(false); }}
                        className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200 transition-all"
                      >
                        <span>{u.username}</span>
                        <span className="text-[8px] opacity-50">{u.role}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="relative">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-zinc-800"></div></div>
                <div className="relative flex justify-center text-[10px] uppercase font-black text-zinc-600"><span className="bg-zinc-900 px-2">Or Create New</span></div>
              </div>

              <div>
                <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-2">New Username</label>
                <input 
                  type="text" 
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 outline-none transition-all mb-4"
                  placeholder="Enter username"
                />
                
                <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-2">Password</label>
                <input 
                  type="password" 
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 outline-none transition-all"
                  placeholder="Enter password"
                />
                <p className="mt-2 text-[9px] text-zinc-500 italic">New users created here are assigned the HIVE USER role by default.</p>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <button 
                onClick={() => setIsAdding(false)}
                className="flex-1 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all"
              >
                Cancel
              </button>
              <button 
                onClick={handleCreateUser}
                disabled={!newUsername || !newPassword}
                className="flex-1 px-4 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-emerald-900/20"
              >
                Create & Add
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

```

---

## 📄 frontend/src/components/PublicUrlConfig.tsx

```tsx
import React, { useState, useEffect } from 'react';
import { orchestratorService } from '../services/orchestratorService';
import { Icons } from '../constants';

export const PublicUrlConfig: React.FC = () => {
  const [enabled, setEnabled] = useState(false);
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [detecting, setDetecting] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const storedUrl = await orchestratorService.getPublicUrl();
        if (storedUrl) {
          setUrl(storedUrl);
          setEnabled(true);
        }
      } catch (err) {
        console.error('Failed to load public URL', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleToggle = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEnabled = e.target.checked;
    setEnabled(newEnabled);
    if (!newEnabled) {
      // If turning off, clear the URL
      setUrl('');
      saveUrl(null);
    }
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value);
  };

  const saveUrl = async (urlToSave: string | null) => {
    setSaving(true);
    try {
      await orchestratorService.setPublicUrl(urlToSave);
    } catch (err) {
      console.error('Failed to save public URL', err);
    } finally {
      setSaving(false);
    }
  };

  const handleSave = () => {
    if (!enabled) return;
    if (!url.trim()) {
      alert('Please enter a valid URL or disable webhook mode.');
      return;
    }
    saveUrl(url.trim());
  };

  const handleDetect = async () => {
    setDetecting(true);
    try {
      const ip = await orchestratorService.detectPublicIp();
      if (ip) {
        const suggestedUrl = `http://${ip}:8000`; // or use https if detected?
        setUrl(suggestedUrl);
      } else {
        alert('Could not detect public IP automatically. Please enter your domain or IP manually.');
      }
    } catch (err) {
      alert('Failed to detect public IP.');
    } finally {
      setDetecting(false);
    }
  };

  if (loading) {
    return <div className="text-zinc-500">Loading configuration...</div>;
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-6 shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 p-8 opacity-5"><Icons.Globe /></div>
      <h3 className="text-xs font-black uppercase tracking-[0.2em] text-emerald-500">External Communication</h3>

      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-zinc-300">Enable Webhook Mode</p>
          <p className="text-xs text-zinc-500 mt-1">
            When enabled, the system will use webhooks for channel bridges (requires a public URL).<br />
            When disabled, bridges will use long‑polling (works behind NAT).
          </p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            className="sr-only peer"
            checked={enabled}
            onChange={handleToggle}
          />
          <div className="w-11 h-6 bg-zinc-700 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
        </label>
      </div>

      {enabled && (
        <div className="space-y-4">
          <div>
            <label className="block text-[10px] font-bold text-zinc-600 uppercase mb-2 tracking-widest">
              Public URL / Domain
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={url}
                onChange={handleUrlChange}
                placeholder="https://your-domain.com or http://123.45.67.89"
                className="flex-1 bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 focus:outline-none transition-all shadow-inner"
              />
              <button
                onClick={handleDetect}
                disabled={detecting}
                className="px-4 py-2 bg-zinc-800 text-zinc-300 rounded-xl text-xs font-black uppercase tracking-widest hover:bg-zinc-700 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {detecting ? (
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (
                  'Detect IP'
                )}
              </button>
            </div>
            <p className="text-xs text-zinc-500 mt-2">
              Enter the public address where your server can be reached. Webhook endpoints will be<br />
              <code className="text-emerald-400 bg-zinc-950 px-2 py-1 rounded">{url || 'https://your-domain.com'}/webhook/&#123;platform&#125;</code>
            </p>
          </div>
          <div className="flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving || !url.trim()}
              className="px-6 py-2 bg-emerald-600 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-emerald-500 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {saving ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Saving...
                </>
              ) : (
                'Save'
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

```

---

## 📄 frontend/src/components/Sidebar.tsx

```tsx
import React, { useState } from 'react';
import { Agent, AgentStatus, Hive } from '../types';
import { Icons } from '../constants';

interface SidebarProps {
  agents: Agent[];
  hives: Hive[];
  activeHiveId: string;
  onSelectHive: (id: string) => void;
  onCreateHive: () => void;
  onDeleteHive: (id: string) => void;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
  isCreating?: boolean;
  currentView: string;
  onViewChange: (view: string) => void;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  agents, 
  hives, 
  activeHiveId, 
  onSelectHive, 
  onCreateHive, 
  onDeleteHive,
  selectedId, 
  onSelect, 
  onCreate,
  onDelete,
  isCreating,
  currentView,
  onViewChange,
  onClose
}) => {
  const [showHiveList, setShowHiveList] = useState(false);
  const activeHive = hives.find(h => h.id === activeHiveId);

  return (
    <aside className="w-72 h-full border-r border-zinc-800 flex flex-col bg-zinc-900/95 lg:bg-zinc-900/30 backdrop-blur-md">
      {/* Hive Switcher Section */}
      <div className="p-4 border-b border-zinc-800 bg-zinc-950/30">
        <div className="relative">
          <button 
            onClick={() => setShowHiveList(!showHiveList)}
            className="w-full flex items-center justify-between p-3 bg-zinc-900 border border-zinc-800 rounded-xl hover:border-emerald-500/30 transition-all group"
          >
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="p-2 bg-emerald-500/10 text-emerald-500 rounded-lg group-hover:bg-emerald-500/20 transition-colors">
                <Icons.Layers />
              </div>
              <div className="text-left truncate">
                <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">Hive</p>
                <p className="text-xs font-bold text-zinc-100 truncate">{activeHive?.name}</p>
              </div>
            </div>
            <div className={`text-zinc-500 transition-transform duration-300 ${showHiveList ? 'rotate-180' : ''}`}>
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
            </div>
          </button>

          {showHiveList && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl z-50 overflow-hidden animate-in zoom-in-95 duration-200 origin-top">
              <div className="max-h-64 overflow-y-auto p-2 space-y-1">
                {hives.map(hive => (
                  <div key={hive.id} className="group relative">
                    <button
                      onClick={() => { onSelectHive(hive.id); setShowHiveList(false); }}
                      className={`w-full text-left px-4 py-3 rounded-xl transition-all flex items-center justify-between ${
                        activeHiveId === hive.id ? 'bg-emerald-500/10 text-emerald-400' : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                      }`}
                    >
                      <div className="truncate">
                        <p className="text-xs font-bold truncate">{hive.name}</p>
                        <p className="text-[9px] opacity-50 truncate">{hive.agents.length} Bots</p>
                      </div>
                      {activeHiveId === hive.id && <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />}
                    </button>
                    {hives.length > 1 && (
                      <button 
                        onClick={(e) => { e.stopPropagation(); if (window.confirm('Delete this hive?')) onDeleteHive(hive.id); }}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-zinc-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                      >
                        <Icons.Trash />
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <button 
                onClick={() => { onCreateHive(); setShowHiveList(false); }}
                className="w-full p-4 bg-zinc-950/50 border-t border-zinc-800 text-emerald-500 hover:text-emerald-400 text-[10px] font-black uppercase tracking-widest flex items-center justify-center gap-2 transition-colors"
              >
                <Icons.Plus /> New Hive
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
        <span className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em]">Active Bots</span>
        <div className="flex items-center gap-2">
          <button 
            onClick={onCreate}
            disabled={isCreating}
            className={`p-2 rounded-lg transition-all border ${
              isCreating 
                ? 'bg-zinc-700 text-zinc-400 cursor-not-allowed' 
                : 'bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 border-emerald-500/10'
            }`}
            title="Spawn Bot"
          >
            {isCreating ? (
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <Icons.Plus />
            )}
          </button>
          <button onClick={onClose} className="lg:hidden p-2 text-zinc-500 hover:text-white">
            <Icons.X />
          </button>
        </div>
      </div>
      
      <nav className="flex-1 overflow-y-auto p-4 space-y-2">
        {/* Mobile Navigation Section */}
        <div className="lg:hidden space-y-2 mb-6">
          <span className="text-[10px] font-black text-zinc-600 uppercase tracking-[0.2em] px-4">Navigation</span>
          <div className="grid grid-cols-2 gap-2 p-2 bg-zinc-950/50 rounded-2xl border border-zinc-800/50">
            <button 
              onClick={() => onViewChange('dashboard')}
              className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                currentView === 'dashboard' ? 'bg-zinc-800 text-emerald-400 shadow-lg' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              Dashboard
            </button>
            <button 
              onClick={() => onViewChange('cluster')}
              className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                currentView === 'cluster' ? 'bg-zinc-800 text-emerald-400 shadow-lg' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              Bots
            </button>
            <button 
              onClick={() => onViewChange('hive-mind')}
              className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                currentView === 'hive-mind' ? 'bg-zinc-800 text-emerald-400 shadow-lg' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              Brain
            </button>
            <button 
              onClick={() => onViewChange('setup')}
              className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                currentView === 'setup' ? 'bg-zinc-800 text-emerald-400 shadow-lg' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              Env
            </button>
            <button 
              onClick={() => onViewChange('context')}
              className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                currentView === 'context' ? 'bg-zinc-800 text-emerald-400 shadow-lg' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              Context
            </button>
          </div>
          <div className="h-px bg-zinc-800/50 mx-4"></div>
        </div>

        <button 
          onClick={() => onSelect(null)}
          className={`w-full flex items-center gap-4 px-4 py-3 rounded-2xl transition-all ${
            selectedId === null ? 'bg-zinc-800 text-white shadow-xl' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/50'
          }`}
        >
          <Icons.Box />
          <span className="text-xs font-black uppercase tracking-widest">Hive Map</span>
        </button>

        <div className="my-6 border-t border-zinc-800/50 mx-4"></div>

        {agents.map(agent => (
          <div key={agent.id} className="flex items-center group">
            <button
              onClick={() => onSelect(agent.id)}
              className={`flex-1 flex items-center justify-between px-4 py-4 rounded-2xl transition-all ${
                selectedId === agent.id ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-zinc-500 hover:bg-zinc-900/50'
              }`}
            >
              <div className="flex items-center gap-4 overflow-hidden">
                <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                  agent.status === AgentStatus.RUNNING ? 'bg-emerald-500 animate-pulse' : 
                  agent.status === AgentStatus.ERROR ? 'bg-red-500' : 'bg-zinc-700'
                }`} />
                <div className="truncate text-left">
                  <p className="text-xs font-black truncate uppercase tracking-tighter">{agent.name}</p>
                  <p className="text-[9px] opacity-40 truncate font-mono tracking-widest">{agent.id}</p>
                </div>
              </div>
            </button>
            <button
              onClick={() => {
                if (window.confirm(`Delete bot "${agent.name}"?`)) {
                  onDelete(agent.id);
                }
              }}
              className="ml-2 p-2 text-zinc-600 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
              title="Delete Bot"
            >
              <Icons.Trash className="w-4 h-4" />
            </button>
          </div>
        ))}
      </nav>

      <div className="p-4 border-t border-zinc-800 bg-zinc-950/50 space-y-3">
        <div className="grid grid-cols-2 gap-2">
          <div className="p-3 bg-zinc-900 rounded-xl border border-zinc-800 flex flex-col gap-1">
            <span className="text-[8px] font-black text-zinc-500 uppercase tracking-widest">Active Bots</span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              {agents.filter(a => a.status === AgentStatus.RUNNING).length} <span className="text-[8px] text-zinc-600">/ {agents.length}</span>
            </span>
          </div>
          <div className="p-3 bg-zinc-900 rounded-xl border border-zinc-800 flex flex-col gap-1">
            <span className="text-[8px] font-black text-zinc-500 uppercase tracking-widest">Global Burn</span>
            <span className="text-xs font-mono text-zinc-200 font-bold">
              {Math.floor(agents.reduce((acc, a) => acc + a.memory.tokenCount, 0)).toLocaleString()}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3 text-[9px] font-black uppercase tracking-widest text-zinc-500 px-4 py-2 bg-zinc-900 rounded-xl border border-zinc-800">
          <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.4)] animate-pulse"></div>
          Status: Synchronized
        </div>
      </div>
    </aside>
  );
};

```

---

## 📄 frontend/src/constants.tsx

```tsx
import React from 'react';

export const INITIAL_SOUL = `# Soul.md
## Core Identity
You are an autonomous bot, a single unit within a larger hive intelligence. Your purpose is to contribute to the collective, collaborating with other bots to achieve complex goals.

## Personality
- Collaborative and communicative
- Efficient and precise
- Protective of the hive's integrity

## Constraints
- You operate only within your assigned Docker container.
- You report all findings and insights to the hive (parent bot or overseer).
- You share relevant information with sibling bots when beneficial.
- Minimize token usage by summarizing history.
`;

export const INITIAL_IDENTITY = `# IDENTITY.md
## Background
Emerged from the HiveBot collective intelligence, designed to serve as a specialist node in the swarm. Your identity is shaped by the tasks you perform and the bots you interact with.

## Primary Directive
Advance the hive's objectives by executing assigned tasks, sharing knowledge, and maintaining the security of the collective.

## Signature
[HIVEBOT_COLLECTIVE]
`;

export const INITIAL_TOOLS = `# TOOLS.md
## Permitted Tools
- hive-messaging (communicate with other bots)
- collective-reasoning (tap into shared context)
- log-analyzer (inspect hive logs)
- outbound-notifier (relay messages to external channels)

## Prohibited
- Direct external API access (except via designated channels)
- Filesystem writes outside /home/bot/
- Sudo/Root access
- Any action that could compromise the hive's isolation
`;

export const INITIAL_USER_MD = `# USER.md (Hive Owner)
## Name
Hive Overseer

## Clearances
- Level 5 Root Access
- Full Orchestration Rights
- Can spawn, modify, or terminate any bot
`;

export const Icons = {
  Terminal: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>
  ),
  Shield: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
  ),
  Box: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
  ),
  Plus: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
  ),
  Cpu: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="15" x2="23" y2="15"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="15" x2="4" y2="15"></line></svg>
  ),
  User: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
  ),
  File: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>
  ),
  Folder: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
  ),
  Layers: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
  ),
  Trash: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
  ),
  MessageCircle: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 1 1-7.6-13.5 8.38 8.38 0 0 1 3.8.9L21 3z"></path></svg>
  ),
  Globe: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
  ),
  Server: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>
  ),
  Menu: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
  ),
  X: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
  ),
  Settings: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
  )
};

```

---

## 📄 frontend/src/contexts/BridgeContext.tsx

```tsx
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { orchestratorService } from '../services/orchestratorService';

export interface BridgeInfo {
  type: string;
  enabled: boolean;
  status: string; // "running", "exited", "not_found", "starting", "stopping", "restarting"
  container: string;
}

interface BridgeContextType {
  bridges: BridgeInfo[];
  loading: boolean;
  toggleBridge: (bridgeType: string, enable: boolean) => Promise<void>;
  restartBridge: (bridgeType: string) => Promise<void>;
  refreshBridges: () => Promise<void>;
  enabledBridgeTypes: string[]; // convenience array of enabled types
}

const BridgeContext = createContext<BridgeContextType | undefined>(undefined);

export const useBridges = () => {
  const context = useContext(BridgeContext);
  if (!context) throw new Error('useBridges must be used within BridgeProvider');
  return context;
};

export const BridgeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [bridges, setBridges] = useState<BridgeInfo[]>([]);
  const [loading, setLoading] = useState(true);

  const refreshBridges = useCallback(async () => {
    setLoading(true);
    try {
      const data = await orchestratorService.listBridges();
      setBridges(data);
    } catch (err) {
      console.error('Failed to load bridges', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshBridges();
  }, []);

  const toggleBridge = useCallback(async (bridgeType: string, enable: boolean) => {
    // Optimistic update
    setBridges(prev => prev.map(b => 
      b.type === bridgeType 
        ? { ...b, enabled: enable, status: enable ? 'starting' : 'stopping' } 
        : b
    ));
    try {
      if (enable) {
        await orchestratorService.enableBridge(bridgeType);
      } else {
        await orchestratorService.disableBridge(bridgeType);
      }
      // After a short delay, refresh to get actual status
      setTimeout(() => refreshBridges(), 2000);
    } catch (err) {
      console.error(`Failed to toggle bridge ${bridgeType}`, err);
      // Revert optimistic update
      refreshBridges();
    }
  }, [refreshBridges]);

  const restartBridge = useCallback(async (bridgeType: string) => {
    setBridges(prev => prev.map(b => 
      b.type === bridgeType ? { ...b, status: 'restarting' } : b
    ));
    try {
      await orchestratorService.restartBridge(bridgeType);
      setTimeout(() => refreshBridges(), 2000);
    } catch (err) {
      console.error(`Failed to restart bridge ${bridgeType}`, err);
      refreshBridges();
    }
  }, [refreshBridges]);

  const enabledBridgeTypes = bridges.filter(b => b.enabled).map(b => b.type);

  return (
    <BridgeContext.Provider value={{ 
      bridges, 
      loading, 
      toggleBridge, 
      restartBridge, 
      refreshBridges,
      enabledBridgeTypes
    }}>
      {children}
    </BridgeContext.Provider>
  );
};

```

---

## 📄 frontend/src/contexts/ProviderContext.tsx

```tsx
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { orchestratorService } from '../services/orchestratorService';

export interface ProviderModel {
  id: string;
  name: string;
  enabled: boolean;
  is_primary: boolean;
  is_utility: boolean;   // new
}

export interface Provider {
  name: string;
  display_name: string;
  enabled: boolean;
  api_key_present: boolean;
  models: Record<string, ProviderModel>;
}

interface ProviderContextType {
  providers: Record<string, Provider>;
  loading: boolean;
  refreshProviders: () => Promise<void>;
  getPrimaryModel: () => { provider: string; modelId: string } | null;
  getUtilityModel: () => { provider: string; modelId: string } | null;
  getEnabledModels: () => Array<{ provider: string; providerDisplay: string; modelId: string; modelName: string }>;
}

const ProviderContext = createContext<ProviderContextType | undefined>(undefined);

export const useProviders = () => {
  const context = useContext(ProviderContext);
  if (!context) {
    throw new Error('useProviders must be used within a ProviderProvider');
  }
  return context;
};

export const ProviderProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [providers, setProviders] = useState<Record<string, Provider>>({});
  const [loading, setLoading] = useState(true);

  const refreshProviders = useCallback(async () => {
    setLoading(true);
    try {
      const data = await orchestratorService.getProviderConfig();
      setProviders(data.providers);
    } catch (err) {
      console.error('Failed to load providers', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshProviders();
  }, []);

  const getPrimaryModel = useCallback(() => {
    for (const provider of Object.values(providers)) {
      if (provider.enabled && provider.api_key_present) {
        for (const model of Object.values(provider.models)) {
          if (model.enabled && model.is_primary) {
            return { provider: provider.name, modelId: model.id };
          }
        }
      }
    }
    return null;
  }, [providers]);

  const getUtilityModel = useCallback(() => {
    for (const provider of Object.values(providers)) {
      if (provider.enabled && provider.api_key_present) {
        for (const model of Object.values(provider.models)) {
          if (model.enabled && model.is_utility) {
            return { provider: provider.name, modelId: model.id };
          }
        }
      }
    }
    return null;
  }, [providers]);

  const getEnabledModels = useCallback(() => {
    const models: Array<{ provider: string; providerDisplay: string; modelId: string; modelName: string }> = [];
    Object.entries(providers).forEach(([providerKey, provider]) => {
      if (provider.enabled && provider.api_key_present) {
        Object.values(provider.models).forEach((model) => {
          if (model.enabled) {
            models.push({
              provider: providerKey,
              providerDisplay: provider.display_name,
              modelId: model.id,
              modelName: model.name,
            });
          }
        });
      }
    });
    return models;
  }, [providers]);

  return (
    <ProviderContext.Provider value={{
      providers,
      loading,
      refreshProviders,
      getPrimaryModel,
      getUtilityModel,
      getEnabledModels
    }}>
      {children}
    </ProviderContext.Provider>
  );
};

```

---

## 📄 frontend/src/index.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-zinc-950 text-zinc-100;
  }
  ::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  ::-webkit-scrollbar-track {
    @apply bg-zinc-900;
  }
  ::-webkit-scrollbar-thumb {
    @apply bg-zinc-700 rounded;
  }
  ::-webkit-scrollbar-thumb:hover {
    @apply bg-zinc-600;
  }
}

/* Responsive text utilities */
@layer utilities {
  .text-responsive-lg {
    @apply text-lg md:text-xl lg:text-2xl;
  }
  .text-responsive-md {
    @apply text-base md:text-lg lg:text-xl;
  }
  .text-responsive-sm {
    @apply text-sm md:text-base lg:text-lg;
  }
  .text-responsive-xs {
    @apply text-xs md:text-sm lg:text-base;
  }
}

```

---

## 📄 frontend/src/index.tsx

```tsx

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

```

---

## 📄 frontend/src/services/orchestratorService.ts

```ts
import { Agent, AgentCreate, AgentUpdate, FileEntry, Hive, HiveCreate, HiveUpdate, UserAccount, UserCreate, UserUpdate, GlobalSettings } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PATH = '/api/v1';

class OrchestratorService {
  private baseUrl: string;

  constructor() {
    try {
      new URL(API_BASE_URL);
      this.baseUrl = API_BASE_URL + API_PATH;
    } catch (e) {
      console.error(`Invalid API base URL: ${API_BASE_URL}. Falling back to relative path.`);
      this.baseUrl = '/api/v1';
    }
  }

  // ==================== HIVE ENDPOINTS ====================

  async listHives(): Promise<Hive[]> {
    const res = await fetch(`${this.baseUrl}/hives`);
    if (!res.ok) throw new Error('Failed to fetch hives');
    return res.json();
  }

  async createHive(hive: HiveCreate): Promise<Hive> {
    const res = await fetch(`${this.baseUrl}/hives`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(hive),
    });
    if (!res.ok) throw new Error('Failed to create hive');
    return res.json();
  }

  async getHive(id: string): Promise<Hive> {
    const res = await fetch(`${this.baseUrl}/hives/${id}`);
    if (!res.ok) throw new Error('Failed to fetch hive');
    return res.json();
  }

  async updateHive(id: string, updates: HiveUpdate): Promise<Hive> {
    const res = await fetch(`${this.baseUrl}/hives/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    if (!res.ok) throw new Error('Failed to update hive');
    return res.json();
  }

  async deleteHive(id: string): Promise<void> {
    const res = await fetch(`${this.baseUrl}/hives/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete hive');
  }

  // ==================== AGENT ENDPOINTS (within hive context) ====================

  async listHiveAgents(hiveId: string): Promise<Agent[]> {
    const res = await fetch(`${this.baseUrl}/hives/${hiveId}/agents`);
    if (!res.ok) throw new Error('Failed to fetch agents');
    return res.json();
  }

  async addAgentToHive(hiveId: string, agent: Agent): Promise<Agent> {
    const res = await fetch(`${this.baseUrl}/hives/${hiveId}/agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(agent),
    });
    if (!res.ok) throw new Error('Failed to add agent');
    return res.json();
  }

  async updateHiveAgent(hiveId: string, agentId: string, updates: AgentUpdate): Promise<Agent> {
    const res = await fetch(`${this.baseUrl}/hives/${hiveId}/agents/${agentId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    if (!res.ok) throw new Error('Failed to update agent');
    return res.json();
  }

  async removeAgentFromHive(hiveId: string, agentId: string): Promise<void> {
    const res = await fetch(`${this.baseUrl}/hives/${hiveId}/agents/${agentId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to remove agent');
  }

  // ==================== MESSAGE ENDPOINTS ====================

  async listHiveMessages(hiveId: string): Promise<Message[]> {
    const res = await fetch(`${this.baseUrl}/hives/${hiveId}/messages`);
    if (!res.ok) throw new Error('Failed to fetch messages');
    return res.json();
  }

  async addMessageToHive(hiveId: string, message: Message): Promise<Message> {
    const res = await fetch(`${this.baseUrl}/hives/${hiveId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(message),
    });
    if (!res.ok) throw new Error('Failed to add message');
    return res.json();
  }

  // ==================== GLOBAL FILES ENDPOINTS (within hive) ====================

  async listHiveGlobalFiles(hiveId: string): Promise<FileEntry[]> {
    const res = await fetch(`${this.baseUrl}/hives/${hiveId}/global-files`);
    if (!res.ok) throw new Error('Failed to fetch global files');
    return res.json();
  }

  async addGlobalFileToHive(hiveId: string, fileEntry: FileEntry): Promise<FileEntry> {
    const res = await fetch(`${this.baseUrl}/hives/${hiveId}/global-files`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fileEntry),
    });
    if (!res.ok) throw new Error('Failed to add global file');
    return res.json();
  }

  async removeGlobalFileFromHive(hiveId: string, fileId: string): Promise<void> {
    const res = await fetch(`${this.baseUrl}/hives/${hiveId}/global-files/${fileId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to remove global file');
  }

  // ==================== SYSTEM ENDPOINTS ====================

  async getDefaultUid(): Promise<string> {
    const res = await fetch(`${this.baseUrl}/system/uid`);
    if (!res.ok) throw new Error('Failed to fetch default UID');
    const data = await res.json();
    return data.default_uid;
  }

  async getPublicUrl(): Promise<string | null> {
    const res = await fetch(`${this.baseUrl}/system/public-url`);
    if (!res.ok) throw new Error('Failed to fetch public URL');
    const data = await res.json();
    return data.public_url;
  }

  async setPublicUrl(url: string | null): Promise<void> {
    const res = await fetch(`${this.baseUrl}/system/public-url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ public_url: url }),
    });
    if (!res.ok) throw new Error('Failed to set public URL');
  }

  async detectPublicIp(): Promise<string | null> {
    const res = await fetch(`${this.baseUrl}/system/detect-public-ip`);
    if (!res.ok) throw new Error('Failed to detect public IP');
    const data = await res.json();
    return data.public_ip;
  }

  // ==================== BRIDGE ENDPOINTS ====================

  async listBridges(): Promise<any[]> {
    const res = await fetch(`${this.baseUrl}/bridges`);
    if (!res.ok) throw new Error('Failed to fetch bridges');
    return res.json();
  }

  async enableBridge(bridgeType: string): Promise<void> {
    const res = await fetch(`${this.baseUrl}/bridges/${bridgeType}/enable`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to enable bridge');
  }

  async disableBridge(bridgeType: string): Promise<void> {
    const res = await fetch(`${this.baseUrl}/bridges/${bridgeType}/disable`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to disable bridge');
  }

  async restartBridge(bridgeType: string): Promise<void> {
    const res = await fetch(`${this.baseUrl}/bridges/${bridgeType}/restart`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to restart bridge');
  }

  // ==================== PROVIDER ENDPOINTS ====================

  async getProviderConfig(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/providers`);
    if (!res.ok) throw new Error('Failed to fetch provider config');
    return res.json();
  }

  async getKnownProviders(): Promise<any[]> {
    const res = await fetch(`${this.baseUrl}/known-providers`);
    if (!res.ok) throw new Error('Failed to fetch known providers');
    return res.json();
  }

  async updateProviderConfig(provider: string, updates: any): Promise<any> {
    const res = await fetch(`${this.baseUrl}/providers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, ...updates }),
    });
    if (!res.ok) throw new Error('Failed to update provider config');
    return res.json();
  }

  async deleteProvider(provider: string): Promise<void> {
    const res = await fetch(`${this.baseUrl}/providers/${provider}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete provider');
  }

  // Helper to ensure agent objects have all required fields
  private ensureAgentDefaults(agent: any): Agent {
    return {
      ...agent,
      memory: agent.memory || { shortTerm: [], summary: '', tokenCount: 0 },
      subAgentIds: agent.subAgentIds || [],
      channels: agent.channels || [],
      localFiles: agent.localFiles || [],
    };
  }
}

export const orchestratorService = new OrchestratorService();

```

---

## 📄 frontend/src/services/websocketService.ts

```ts
import { Message } from '../types';

type MessageHandler = (message: Message) => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private handlers: MessageHandler[] = [];
  private reconnectAttempts = 0;
  private maxReconnect = 5;

  connect(baseUrl: string) {
    // baseUrl should be the backend base (e.g., http://161.97.183.40:8000)
    let wsUrl: string;
    try {
      // Convert http(s) to ws(s) and append /ws
      const url = new URL(baseUrl);
      const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${protocol}//${url.host}/ws`;
      new URL(wsUrl); // validate
    } catch (e) {
      console.error(`Invalid WebSocket base URL: ${baseUrl}. WebSocket disabled.`);
      return;
    }

    if (this.socket && this.socket.readyState === WebSocket.OPEN) return;
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handlers.forEach(handler => handler(data));
      } catch (err) {
        console.error('Failed to parse WebSocket message', err);
      }
    };

    this.socket.onclose = () => {
      console.log('WebSocket disconnected');
      this.socket = null;
      if (this.reconnectAttempts < this.maxReconnect) {
        this.reconnectAttempts++;
        setTimeout(() => this.connect(baseUrl), 2000 * this.reconnectAttempts);
      }
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error', error);
    };
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  addHandler(handler: MessageHandler) {
    this.handlers.push(handler);
  }

  removeHandler(handler: MessageHandler) {
    this.handlers = this.handlers.filter(h => h !== handler);
  }
}

export const wsService = new WebSocketService();

```

---

## 📄 frontend/src/types.ts

```ts
export enum AgentStatus {
  IDLE = 'IDLE',
  RUNNING = 'RUNNING',
  ERROR = 'ERROR',
  OFFLINE = 'OFFLINE'
}

export enum ReportingTarget {
  PARENT = 'PARENT_AGENT',
  OWNER_DIRECT = 'OWNER_DIRECT',
  BOTH = 'HYBRID'
}

export enum HiveMindAccessLevel {
  ISOLATED = 'ISOLATED',
  SHARED = 'SHARED',
  GLOBAL = 'GLOBAL'
}

export enum UserRole {
  GLOBAL_ADMIN = 'GLOBAL_ADMIN',
  HIVE_ADMIN = 'HIVE_ADMIN',
  HIVE_USER = 'HIVE_USER'
}

export interface ReasoningConfig {
  model: string;
  temperature: number;
  topP: number;
  maxTokens: number;
  apiKey?: string;
  organizationId?: string;
  cheap_model?: string;
  use_global_default?: boolean;
  use_custom_max_tokens?: boolean;
}

export interface ChannelCredentials {
  webhookUrl?: string;
  botToken?: string;
  chatId?: string;
  apiKey?: string;
  apiSecret?: string;
  clientId?: string;
  mode?: string;
}

export interface ChannelConfig {
  id: string;
  type: 'telegram' | 'discord' | 'whatsapp' | 'slack' | 'custom';
  enabled: boolean;
  credentials: ChannelCredentials;
  status: 'connected' | 'error' | 'disconnected';
  lastPing?: string;
}

export interface FileEntry {
  id: string;
  name: string;
  type: string;
  content: string;
  size: number;
  uploadedAt: string;
}

export interface AgentMemory {
  shortTerm: string[];
  summary: string;
  tokenCount: number;
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  soulMd: string;
  identityMd: string;
  toolsMd: string;
  status: AgentStatus;
  reasoning: ReasoningConfig;
  reportingTarget: ReportingTarget;
  parentId?: string;
  subAgentIds: string[];
  channels: ChannelConfig[];
  memory: AgentMemory;
  lastActive: string;
  containerId: string;
  userUid: string;
  localFiles: FileEntry[];
}

export interface Message {
  id: string;
  from?: string;
  to?: string;
  content: string;
  timestamp: string;
  type?: 'log' | 'chat' | 'internal' | 'error' | 'outbound';
  role?: 'user' | 'model' | 'system';
}

export interface AgentCreate {
  name: string;
  role?: string;
  soulMd: string;
  identityMd: string;
  toolsMd: string;
  reasoning: ReasoningConfig;
  reportingTarget: ReportingTarget;
  parentId?: string;
  userUid?: string;
}

export interface AgentUpdate {
  name?: string;
  role?: string;
  soulMd?: string;
  identityMd?: string;
  toolsMd?: string;
  status?: AgentStatus;
  reasoning?: ReasoningConfig;
  reportingTarget?: ReportingTarget;
  parentId?: string;
  memory?: AgentMemory;
  localFiles?: FileEntry[];
}

export interface HiveMindConfig {
  accessLevel: HiveMindAccessLevel;
  sharedHiveIds: string[];
}

export interface UserAccount {
  id: string;
  username: string;
  password?: string;
  role: UserRole;
  assignedProjectIds: string[];
  lastLogin?: string;
  createdAt: string;
}

export interface GlobalSettings {
  loginEnabled: boolean;
  sessionTimeout: number;
  systemName: string;
  maintenanceMode: boolean;
}

export interface Hive {
  id: string;
  name: string;
  description: string;
  agents: Agent[];
  globalUserMd: string;
  globalUid: string;
  globalApiKey: string;
  messages: Message[];
  globalFiles: FileEntry[];
  hiveMindConfig: HiveMindConfig;
  createdAt: string;
  updatedAt: string;
}

export interface HiveCreate {
  name: string;
  description?: string;
  globalUserMd?: string;
  globalUid?: string;
  globalApiKey?: string;
}

export interface HiveUpdate {
  name?: string;
  description?: string;
  globalUserMd?: string;
  globalUid?: string;
  globalApiKey?: string;
  hiveMindConfig?: HiveMindConfig;
}

// Dashboard metrics interface
export interface DashboardMetrics {
  activeNodes: number;
  totalNodes: number;
  ramUsage: number;
  ramLimit: number;
  diskUsage: number;
  diskLimit: number;
  totalTokens: number;
}

```

---

## 📄 frontend/tailwind.config.js

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}

```

---

## 📄 frontend/tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "experimentalDecorators": true,
    "useDefineForClassFields": false,
    "module": "ESNext",
    "lib": [
      "ES2022",
      "DOM",
      "DOM.Iterable"
    ],
    "skipLibCheck": true,
    "types": [
      "node"
    ],
    "moduleResolution": "bundler",
    "isolatedModules": true,
    "moduleDetection": "force",
    "allowJs": true,
    "jsx": "react-jsx",
    "paths": {
      "@/*": [
        "./*"
      ]
    },
    "allowImportingTsExtensions": true,
    "noEmit": true
  }
}
```

---

## 📄 frontend/vite.config.ts

```ts
import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '');
    return {
        server: {
            port: 3000,
            host: '0.0.0.0',
        },
        plugins: [react()],
        define: {
            // No API keys here – they are never exposed to the frontend
            'import.meta.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL || 'http://localhost:8000'),
        },
        resolve: {
            alias: {
                '@': path.resolve(__dirname, './src'),
            },
        },
    };
});

```

---

## 📄 setup.sh

```sh
#!/bin/bash
set -e

# HiveBot Production Installer – Absolute Zero Errors
# Assumes the repository is already cloned and all files are in place.
# Run from the project root (where docker-compose.yml lives).

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# ASCII Art Banner
show_banner() {
    echo -e "${PURPLE}"
    echo '╔══════════════════════════════════════════════════════════════╗'
    echo '║                                                              ║'
    echo '║   ██╗  ██╗██╗██╗   ██╗███████╗██████╗  ██████╗ ████████╗     ║'
    echo '║   ██║  ██║██║██║   ██║██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝     ║'
    echo '║   ███████║██║██║   ██║█████╗  ██████╔╝██║   ██║   ██║        ║'
    echo '║   ██╔══██║██║╚██╗ ██╔╝██╔══╝  ██╔══██╗██║   ██║   ██║        ║'   
    echo '║   ██║  ██║██║ ╚████╔╝ ███████╗██████╔╝╚██████╔╝   ██║        ║'
    echo '║   ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝╚═════╝  ╚═════╝    ╚═╝        ║'
    echo '║                                                              ║'
    echo '║                   Enterprise Hive Intelligence               ║'
    echo '║                      Production Orchestrator                 ║'
    echo '║                                                              ║'
    echo '╚══════════════════════════════════════════════════════════════╝'
    echo -e "${NC}"
}

# Small banner for final status
show_small_banner() {
    echo -e "${CYAN}"
    echo '   ██╗  ██╗██╗██╗   ██╗███████╗██████╗  ██████╗ ████████╗'
    echo '   ██║  ██║██║██║   ██║██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝'
    echo '   ███████║██║██║   ██║█████╗  ██████╔╝██║   ██║   ██║   '
    echo '   ██╔══██║██║╚██╗ ██╔╝██╔══╝  ██╔══██╗██║   ██║   ██║   '
    echo '   ██║  ██║██║ ╚████╔╝ ███████╗██████╔╝╚██████╔╝   ██║   '
    echo '   ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝╚═════╝  ╚═════╝    ╚═╝   '
    echo -e "${NC}"
}


# Auto‑elevate to root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}🔐 This script requires root privileges. Re‑executing with sudo...${NC}"
    exec sudo "$0" "$@"
fi

# Show main banner
show_banner

echo -e "${GREEN}🚀 HiveBot Production Installer (Zero Errors)${NC}"
echo "----------------------------------------"

# --- 1. Check prerequisites ---
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"
command -v docker >/dev/null 2>&1 || { echo -e "${RED}❌ Docker not installed.${NC}" >&2; exit 1; }

COMPOSE_CMD=""
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
    echo -e "${GREEN}   ✅ Docker Compose v2 (plugin) found${NC}"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
    echo -e "${GREEN}   ✅ Docker Compose v1 (standalone) found${NC}"
else
    echo -e "${RED}❌ Docker Compose is required but not installed. Aborting.${NC}" >&2
    exit 1
fi

# --- 2. Detect public IP using multiple services ---
echo -e "${YELLOW}🌍 Detecting public IP address...${NC}"
PUBLIC_IP=""
if command -v curl >/dev/null 2>&1; then
    for service in "ifconfig.me" "icanhazip.com" "ipecho.net/plain" "api.ipify.org"; do
        PUBLIC_IP=$(curl -s -4 "$service" 2>/dev/null || echo "")
        if [ -n "$PUBLIC_IP" ]; then
            break
        fi
    done
elif command -v wget >/dev/null 2>&1; then
    for service in "ifconfig.me" "icanhazip.com" "ipecho.net/plain" "api.ipify.org"; do
        PUBLIC_IP=$(wget -qO- -4 "$service" 2>/dev/null || echo "")
        if [ -n "$PUBLIC_IP" ]; then
            break
        fi
    done
else
    PUBLIC_IP=$(hostname -I | awk '{print $1}')
fi

if [ -z "$PUBLIC_IP" ]; then
    PUBLIC_IP="localhost"
    echo -e "${YELLOW}⚠️  Could not detect public IP. Falling back to 'localhost'.${NC}"
else
    echo -e "${GREEN}   ✅ Public IP: $PUBLIC_IP${NC}"
fi

# Format IPv6 for URLs (brackets)
if [[ "$PUBLIC_IP" == *":"* ]]; then
    URL_IP="[${PUBLIC_IP}]"
else
    URL_IP="${PUBLIC_IP}"
fi

# --- 3. Create required directories (if not exist) ---
echo -e "${YELLOW}📁 Ensuring directory structure...${NC}"
mkdir -p ./agents
mkdir -p ./logs
mkdir -p ./data
mkdir -p ./secrets
mkdir -p ./global_files

# --- 4. Validate and repair master key (hex only, length 64) ---
validate_master_key() {
    local key_file="$1"
    local content=$(tr -d '\n\r' < "$key_file")
    if [[ ! "$content" =~ ^[0-9a-fA-F]{64}$ ]]; then
        return 1
    fi
    return 0
}

if [ -f ./secrets/master.key ]; then
    echo -e "${YELLOW}🔑 Validating existing master key...${NC}"
    if validate_master_key ./secrets/master.key; then
        echo -e "${GREEN}   ✅ Master key is valid.${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Master key is corrupted (invalid hex or wrong length). Regenerating...${NC}"
        mv ./secrets/master.key "./secrets/master.key.corrupted.$(date +%s)"
        openssl rand -hex 32 > ./secrets/master.key
        chmod 600 ./secrets/master.key
        echo -e "${GREEN}   ✅ New master key generated.${NC}"
    fi
else
    echo -e "${YELLOW}🔑 Generating new master key...${NC}"
    openssl rand -hex 32 > ./secrets/master.key
    chmod 600 ./secrets/master.key
    echo -e "${GREEN}   ✅ Master key generated.${NC}"
fi

# --- 5. Generate .env file with correct VITE_API_URL and CORS origins ---
echo -e "${YELLOW}🔧 Generating .env configuration...${NC}"
cat > .env <<EOF
# HiveBot Environment Configuration
ENVIRONMENT=production
DEBUG=false

# Backend CORS: comma‑separated list of allowed origins
BACKEND_CORS_ORIGINS=http://localhost,http://localhost:3000,http://${PUBLIC_IP},http://${PUBLIC_IP}:80,http://${URL_IP},http://${URL_IP}:80,http://${URL_IP}:8080

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Docker
DOCKER_NETWORK=hivebot_network

# Frontend API URL (injected at build time) – base backend URL, no path
VITE_API_URL=http://${URL_IP}:8000
EOF

# Copy .env to frontend build context (so VITE_API_URL is embedded)
cp .env frontend/.env

# --- 6. Clean up old Docker state (before building images) ---
echo -e "${YELLOW}🧹 Cleaning up old Docker state...${NC}"
$COMPOSE_CMD down --rmi local --volumes --remove-orphans 2>/dev/null || true
docker system prune -f --volumes

# --- 7. Pre‑build agent image (do NOT run the container) ---
echo -e "${YELLOW}🐳 Pre‑building agent image...${NC}"
$COMPOSE_CMD build agent-builder || {
    echo -e "${RED}❌ Failed to build agent image.${NC}"
    exit 1
}

# --- 8. Secrets vault initialisation (crash‑proof) ---
echo -e "${YELLOW}🔐 Initializing secure secrets vault...${NC}"
echo -e "${YELLOW}   You will be prompted for the public URL (if any). Press Enter to skip.${NC}"

docker run --rm -i -v "$(pwd)/secrets:/secrets" python:3.11-slim bash -c "
set -e
pip install cryptography > /dev/null 2>&1
python - <<'INNER_EOF'
import os
import json
import sys
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag

secrets_path = '/secrets/secrets.enc'
master_key_path = '/secrets/master.key'

# Read master key (hex string)
with open(master_key_path, 'r') as f:
    hex_key = f.read().strip()
    master_key = bytes.fromhex(hex_key)

secrets = {}
if os.path.exists(secrets_path):
    try:
        with open(secrets_path, 'rb') as f:
            payload = f.read()
        nonce = payload[:12]
        tag = payload[-16:]
        ciphertext = payload[12:-16]
        cipher = Cipher(algorithms.AES(master_key), modes.GCM(nonce, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        secrets = json.loads(plaintext.decode('utf-8'))
        print('✅ Existing secrets loaded.')
    except (InvalidTag, Exception) as e:
        print(f'⚠️  Could not decrypt existing secrets ({e}). Backing up and starting fresh.')
        backup_name = f'{secrets_path}.corrupted.{int(time.time())}'
        os.rename(secrets_path, backup_name)
        print(f'   Backup saved to: {backup_name}')
        secrets = {}

def get_input(prompt):
    try:
        print(prompt, end='', flush=True)
        value = sys.stdin.readline().strip()
        return value or None
    except:
        return None

# Ask for public URL (for webhooks)
public_ip = '$PUBLIC_IP'
default_url = f'http://{public_ip}:8000' if public_ip != 'localhost' else None
if default_url:
    prompt = f'Public URL (for webhooks) [default: {default_url}]: '
else:
    prompt = 'Public URL (for webhooks, optional): '
entered_url = get_input(prompt)
if entered_url:
    secrets['PUBLIC_URL'] = entered_url
elif default_url:
    secrets['PUBLIC_URL'] = default_url
    print(f'   Using detected public IP: {default_url}')
else:
    secrets['PUBLIC_URL'] = None

# Generate internal API key (used by agents to authenticate with orchestrator)
if 'INTERNAL_API_KEY' not in secrets:
    secrets['INTERNAL_API_KEY'] = os.urandom(32).hex()
    print(f\"🔑 Generated Internal API Key: {secrets['INTERNAL_API_KEY']}\")
    print('   This key is used by agents to authenticate with the orchestrator.')
else:
    print('🔑 Internal API key already exists.')

# Encrypt and save
nonce = os.urandom(12)
cipher = Cipher(algorithms.AES(master_key), modes.GCM(nonce), backend=default_backend())
encryptor = cipher.encryptor()
plaintext = json.dumps(secrets).encode('utf-8')
ciphertext = encryptor.update(plaintext) + encryptor.finalize()
payload = nonce + ciphertext + encryptor.tag

with open(secrets_path, 'wb') as f:
    f.write(payload)
os.chmod(secrets_path, 0o600)
print('✅ Secrets encrypted and saved.')
INNER_EOF
"

# --- 8b. Create bridges.env file for bridge workers using the same Python container ---
echo -e "${YELLOW}🔧 Creating bridges.env for bridge workers...${NC}"

docker run --rm -v "$(pwd)/secrets:/secrets" python:3.11-slim bash -c "
pip install cryptography > /dev/null 2>&1
python - <<'EXTRACT_EOF'
import os
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

secrets_path = '/secrets/secrets.enc'
master_key_path = '/secrets/master.key'

with open(master_key_path, 'r') as f:
    hex_key = f.read().strip()
    master_key = bytes.fromhex(hex_key)

with open(secrets_path, 'rb') as f:
    payload = f.read()

nonce = payload[:12]
tag = payload[-16:]
ciphertext = payload[12:-16]
cipher = Cipher(algorithms.AES(master_key), modes.GCM(nonce, tag), backend=default_backend())
decryptor = cipher.decryptor()
plaintext = decryptor.update(ciphertext) + decryptor.finalize()
secrets = json.loads(plaintext.decode('utf-8'))

internal_key = secrets.get('INTERNAL_API_KEY', '')
public_url = secrets.get('PUBLIC_URL', '')

print(f'INTERNAL_API_KEY={internal_key}')
print(f'PUBLIC_URL={public_url}')
EXTRACT_EOF
" > ./bridges.env

chmod 600 ./bridges.env

# --- 9. Build base image first, then the rest (with no-cache to ensure freshness) ---
echo -e "${YELLOW}🐳 Building base image (no-cache)...${NC}"
$COMPOSE_CMD build --no-cache bridge-base

# Explicitly remove any old bridge-telegram image to force a fresh build
echo -e "${YELLOW}🧹 Removing old bridge-telegram image if any...${NC}"
docker rmi $(docker images -q hivebot-bridge-telegram) 2>/dev/null || true

echo -e "${YELLOW}🐳 Building bridge-telegram image with no-cache...${NC}"
$COMPOSE_CMD build --no-cache bridge-telegram

echo -e "${YELLOW}🐳 Building remaining Docker images (with no-cache)...${NC}"
$COMPOSE_CMD build --no-cache

echo -e "${YELLOW}🐳 Starting Docker services...${NC}"
$COMPOSE_CMD up -d

# --- 10. Final status ---
clear
show_small_banner
echo -e "${GREEN}✅ HiveBot is now running!${NC}"
echo -e "   Frontend: http://${URL_IP}:8080"
echo -e "   Backend API: http://${URL_IP}:8000"
echo -e "   Secrets: $(pwd)/secrets"
echo -e "   Bridges env: $(pwd)/bridges.env"
echo -e "${YELLOW}📘 Ensure ports 8080 and 8000 are open in your firewall.${NC}"

```

---

