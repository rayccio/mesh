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
