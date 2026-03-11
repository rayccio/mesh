from fastapi import APIRouter
from ....known_providers import KNOWN_PROVIDERS

router = APIRouter()

@router.get("")
async def get_known_providers():
    """Return the list of known AI providers and their default models."""
    return KNOWN_PROVIDERS
