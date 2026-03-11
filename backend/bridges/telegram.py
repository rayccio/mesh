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
