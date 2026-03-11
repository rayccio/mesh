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
