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
