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
