from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional
import logging
from ....models.types import Hive, HiveCreate, HiveUpdate, Agent, Message, FileEntry
from ....services.hive_manager import HiveManager
from ....services.agent_manager import AgentManager
from ....services.docker_service import DockerService

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_hive_manager():
    docker_service = DockerService()
    agent_manager = AgentManager(docker_service)
    return HiveManager(agent_manager)

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
    """List all agents in a hive (deprecated – will be empty after migration)"""
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
    """Add an agent to a hive (deprecated)"""
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
    """Update an agent in a hive (deprecated)"""
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
    """Remove an agent from a hive (deprecated)"""
    hive = await manager.remove_agent(hive_id, agent_id)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive or agent not found")

# --- NEW: Get agents currently executing tasks for this hive ---
@router.get("/{hive_id}/active-agents", response_model=List[Agent])
async def get_hive_active_agents(
    hive_id: str,
    manager: HiveManager = Depends(get_hive_manager)
):
    """Get agents currently executing tasks for this hive."""
    hive = await manager.get_hive(hive_id)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive not found")
    return await manager.get_active_agents(hive_id)

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
