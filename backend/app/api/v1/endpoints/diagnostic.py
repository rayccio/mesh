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
