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
import time
from typing import Dict, Optional

import redis.asyncio as redis
import httpx
from fastapi import FastAPI, Request, HTTPException
import uvicorn

from .registry import get_bridge_class, register_bridge
from .base import BaseChannelBridge

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
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


async def fetch_agents_with_channel(retries=5, delay=2) -> list[dict]:
    """Fetch all agents that have this channel type enabled, with retries."""
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{BACKEND_API_URL}/agents",
                    params={"channel_type": CHANNEL_TYPE},
                    headers={"Authorization": f"Bearer {INTERNAL_API_KEY}"},
                    timeout=10.0
                )
                resp.raise_for_status()
                data = resp.json()
                logger.debug(f"Fetched {len(data)} agents")
                return data
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}/{retries} failed to fetch agents: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))  # exponential backoff
            else:
                logger.error("All attempts failed, exiting.")
                sys.exit(1)


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


async def listen_for_outbound():
    """Subscribe to report:owner and forward messages to bridges."""
    pubsub_out = redis_client.pubsub()
    await pubsub_out.subscribe("report:owner")
    logger.info("Subscribed to report:owner")

    async for msg in pubsub_out.listen():
        if msg["type"] != "message":
            continue
        logger.debug(f"Received message on report:owner: {msg['data']}")
        try:
            data = json.loads(msg["data"])
            agent_id = data.get("agent_id")
            response = data.get("response")
            if not agent_id or not response:
                logger.warning("Message missing agent_id or response")
                continue
            bridge = active_bridges.get(agent_id)
            if bridge:
                logger.info(f"Forwarding message to agent {agent_id}")
                await bridge.send_message(response)
            else:
                logger.debug(f"No active bridge for agent {agent_id} (message ignored)")
        except Exception as e:
            logger.exception("Error processing outbound message")


async def main_loop():
    """Main worker loop."""
    global redis_client, webhook_server_task
    redis_client = await redis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)
    logger.info("Connected to Redis")

    # Initial load with retries
    agents = await fetch_agents_with_channel()
    await apply_config(agents)

    # Start listening for config updates
    config_task = asyncio.create_task(listen_for_config_updates())

    # Start webhook server if PUBLIC_URL is set
    if PUBLIC_URL:
        webhook_server_task = asyncio.create_task(start_webhook_server())
    else:
        logger.info("PUBLIC_URL not set, webhook server disabled (polling only)")

    # Listen for outbound messages
    outbound_task = asyncio.create_task(listen_for_outbound())

    # Wait for shutdown signal
    await shutdown_event.wait()
    config_task.cancel()
    outbound_task.cancel()
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
