"""
Discord Connector — discord.py based.

Listens for messages in configured guilds/channels.
Normalizes events to standard message format.

Requires: discord.py
Install: pip install seed-agent[discord]

Config (connectors.yml):
  - name: discord-main
    type: discord
    token: ${DISCORD_TOKEN}
    guilds: [123456789]        # Optional: filter to specific guilds
    channels: [987654321]      # Optional: filter to specific channels
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
    import discord
    _HAS_DISCORD = True
except ImportError:
    _HAS_DISCORD = False


class DiscordConnector(Connector):
    """Discord connector using discord.py."""

    connector_type = "discord"

    def connect(self) -> None:
        if not _HAS_DISCORD:
            raise ImportError(
                "Discord connector requires discord.py. Install: pip install seed-agent[discord]"
            )

        self._token = self.get_config("token", env_key="DISCORD_TOKEN")
        if not self._token:
            raise ValueError(
                "Discord connector requires a bot token. "
                "Set DISCORD_TOKEN env var or configure in connectors.yml."
            )

        self._allowed_guilds = set(self.config.get("guilds", []))
        self._allowed_channels = set(self.config.get("channels", []))
        self._poll_interval = self.config.get("outbox_poll_interval", 2.0)

        # Set up discord client
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        self._client = discord.Client(intents=intents)
        self._loop: asyncio.AbstractEventLoop | None = None

        self._register_handlers()

    def disconnect(self) -> None:
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._client.close(), self._loop)
        self.logger.info("Discord connector disconnecting")

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
        channel = self._client.get_channel(int(msg.conversation_id))
        if not channel:
            self.logger.error(f"Channel not found: {msg.conversation_id}")
            return False

        if msg.thread_id:
            # Reply in thread
            try:
                thread = channel.get_thread(int(msg.thread_id))
                if thread:
                    await thread.send(msg.text)
                    return True
            except Exception:
                pass

        await channel.send(msg.text)
        return True

    def run_loop(self) -> None:
        # Start outbox poller in background
        poller = threading.Thread(target=self._poll_outbox_loop, daemon=True)
        poller.start()

        # Run discord client (blocks)
        self._client.run(self._token, log_handler=None)

    def _is_allowed(self, message: Any) -> bool:
        """Check guild/channel filters."""
        if isinstance(message.channel, discord.DMChannel):
            return True
        if self._allowed_guilds and message.guild.id not in self._allowed_guilds:
            return False
        if self._allowed_channels and message.channel.id not in self._allowed_channels:
            return False
        return True

    def _register_handlers(self) -> None:
        @self._client.event
        async def on_ready() -> None:
            self._loop = asyncio.get_event_loop()
            self.logger.info(f"Connected as {self._client.user}")

        @self._client.event
        async def on_message(message: discord.Message) -> None:
            # Skip own messages
            if message.author == self._client.user:
                return

            if not self._is_allowed(message):
                return

            # Determine conversation type
            if isinstance(message.channel, discord.DMChannel):
                conv_type = "dm"
                conv_name = f"DM-{message.author.name}"
            else:
                conv_type = "channel"
                conv_name = f"#{message.channel.name}"

            msg = Message(
                connector=ConnectorInfo(type="discord", instance=self.name),
                sender=Sender(
                    id=str(message.author.id),
                    username=message.author.name,
                    display_name=message.author.display_name,
                ),
                content=Content(
                    text=message.content,
                    attachments=[
                        {"url": a.url, "filename": a.filename}
                        for a in message.attachments
                    ],
                ),
                conversation=Conversation(
                    id=str(message.channel.id),
                    type=conv_type,
                    name=conv_name,
                    thread_id=str(message.thread.id) if hasattr(message, "thread") and message.thread else None,
                ),
                metadata={
                    "guild_id": str(message.guild.id) if message.guild else None,
                    "is_mention": self._client.user in message.mentions if self._client.user else False,
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

    parser = argparse.ArgumentParser(description="Seed Agent Discord Connector")
    parser.add_argument("--seed-home", default=".", help="Seed home directory")
    parser.add_argument("--name", default="discord-main", help="Connector instance name")
    args = parser.parse_args()

    connector = DiscordConnector(name=args.name, seed_home=args.seed_home)
    connector.run()
