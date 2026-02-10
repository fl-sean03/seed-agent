"""
Telegram Connector — python-telegram-bot based.

Listens for messages via Telegram Bot API (long polling).
Normalizes events to standard message format.

Requires: python-telegram-bot
Install: pip install seed-agent[telegram]

Config (connectors.yml):
  - name: telegram-main
    type: telegram
    token: ${TELEGRAM_BOT_TOKEN}
    allowed_chats: [123456789]   # Optional: filter to specific chat IDs
"""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Any

from connectors.base.connector import Connector
from connectors.base.message import (
    ConnectorInfo,
    Content,
    Conversation,
    Message,
    OutgoingMessage,
    Sender,
)

try:
    from telegram import Update
    from telegram.ext import Application, MessageHandler, filters, ContextTypes
    _HAS_TELEGRAM = True
except ImportError:
    _HAS_TELEGRAM = False


class TelegramConnector(Connector):
    """Telegram connector using python-telegram-bot."""

    connector_type = "telegram"

    def connect(self) -> None:
        if not _HAS_TELEGRAM:
            raise ImportError(
                "Telegram connector requires python-telegram-bot. "
                "Install: pip install seed-agent[telegram]"
            )

        self._token = self.get_config("token", env_key="TELEGRAM_BOT_TOKEN")
        if not self._token:
            raise ValueError(
                "Telegram connector requires a bot token. "
                "Set TELEGRAM_BOT_TOKEN env var or configure in connectors.yml."
            )

        self._allowed_chats = set(self.config.get("allowed_chats", []))
        self._poll_interval = self.config.get("outbox_poll_interval", 2.0)

        self._app = Application.builder().token(self._token).build()
        self._loop: asyncio.AbstractEventLoop | None = None

        # Register handlers
        self._app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        )

    def disconnect(self) -> None:
        self.logger.info("Telegram connector disconnecting")

    def send_message(self, msg: OutgoingMessage) -> bool:
        if not self._loop:
            return False
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._async_send(msg), self._loop
            )
            return future.result(timeout=10)
        except Exception as e:
            self.logger.error(f"Failed to send: {e}")
            return False

    async def _async_send(self, msg: OutgoingMessage) -> bool:
        kwargs: dict[str, Any] = {
            "chat_id": int(msg.conversation_id),
            "text": msg.text,
        }
        if msg.thread_id:
            kwargs["reply_to_message_id"] = int(msg.thread_id)
        await self._app.bot.send_message(**kwargs)
        return True

    def run_loop(self) -> None:
        # Start outbox poller in background
        poller = threading.Thread(target=self._poll_outbox_loop, daemon=True)
        poller.start()

        # Run the telegram bot (blocks)
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._run_polling())

    async def _run_polling(self) -> None:
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling()
        self.logger.info("Telegram polling started")

        # Wait until stopped
        while self._running:
            await asyncio.sleep(1)

        await self._app.updater.stop()
        await self._app.stop()
        await self._app.shutdown()

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        if not message or not message.text:
            return

        chat = update.effective_chat
        if not chat:
            return

        # Chat filter
        if self._allowed_chats and chat.id not in self._allowed_chats:
            return

        user = update.effective_user

        # Map Telegram chat types
        conv_type = "dm" if chat.type == "private" else "channel"

        msg = Message(
            connector=ConnectorInfo(type="telegram", instance=self.name),
            sender=Sender(
                id=str(user.id) if user else "unknown",
                username=user.username or "" if user else "unknown",
                display_name=user.full_name if user else "Unknown",
            ),
            content=Content(text=message.text),
            conversation=Conversation(
                id=str(chat.id),
                type=conv_type,
                name=chat.title or chat.username or str(chat.id),
                thread_id=str(message.message_thread_id) if message.message_thread_id else None,
            ),
            metadata={
                "message_id": message.message_id,
                "chat_type": chat.type,
            },
        )
        self.write_to_inbox(msg)

    def _poll_outbox_loop(self) -> None:
        while self._running:
            try:
                self.process_outbox()
            except Exception as e:
                self.logger.error(f"Outbox poll error: {e}")
            time.sleep(self._poll_interval)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed Agent Telegram Connector")
    parser.add_argument("--seed-home", default=".", help="Seed home directory")
    parser.add_argument("--name", default="telegram-main", help="Connector instance name")
    args = parser.parse_args()

    connector = TelegramConnector(name=args.name, seed_home=args.seed_home)
    connector.run()
