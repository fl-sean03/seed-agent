"""
Slack Connector — Socket Mode (no public URL required).

Listens for messages, mentions, and reactions via Slack Socket Mode.
Normalizes events to standard message format and writes to inbox.
Polls outbox and sends responses via Slack API.

Requires: slack-bolt, slack-sdk
Install: pip install seed-agent[slack]

Config (connectors.yml):
  - name: slack-main
    type: slack
    bot_token: ${SLACK_BOT_TOKEN}
    app_token: ${SLACK_APP_TOKEN}
    channels: ["C0ADZ0C6BK8"]
"""

from __future__ import annotations

import os
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
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler
except ImportError:
    raise ImportError(
        "Slack connector requires slack-bolt. Install: pip install seed-agent[slack]"
    )


class SlackConnector(Connector):
    """Slack connector using Socket Mode for real-time events."""

    connector_type = "slack"

    def connect(self) -> None:
        bot_token = self.get_config("bot_token", env_key="SLACK_BOT_TOKEN")
        self._app_token = self.get_config("app_token", env_key="SLACK_APP_TOKEN")

        if not bot_token or not self._app_token:
            raise ValueError(
                "Slack connector requires bot_token and app_token. "
                "Set SLACK_BOT_TOKEN and SLACK_APP_TOKEN env vars or configure in connectors.yml."
            )

        self._app = App(token=bot_token)
        self._allowed_channels = set(self.config.get("channels", []))
        self._poll_interval = self.config.get("outbox_poll_interval", 2.0)

        # Get bot user ID to filter self-messages
        try:
            result = self._app.client.auth_test()
            self._bot_user_id = result["user_id"]
            self.logger.info(f"Authenticated as bot user: {self._bot_user_id}")
        except Exception as e:
            self.logger.error(f"Auth failed: {e}")
            raise

        # Register event handlers
        self._register_handlers()

    def disconnect(self) -> None:
        self.logger.info("Slack connector disconnecting")

    def send_message(self, msg: OutgoingMessage) -> bool:
        try:
            kwargs: dict[str, Any] = {
                "channel": msg.conversation_id,
                "text": msg.text,
            }
            if msg.thread_id:
                kwargs["thread_ts"] = msg.thread_id
            self._app.client.chat_postMessage(**kwargs)
            return True
        except Exception as e:
            self.logger.error(f"Failed to send: {e}")
            return False

    def run_loop(self) -> None:
        # Start outbox poller in background
        poller = threading.Thread(target=self._poll_outbox_loop, daemon=True)
        poller.start()

        # Start Socket Mode handler (blocks)
        handler = SocketModeHandler(self._app, self._app_token)
        handler.start()

    def _is_allowed(self, channel: str, channel_type: str = "") -> bool:
        """Check if channel is allowed (DMs always allowed)."""
        if channel_type in ("im", "mpim"):
            return True
        if not self._allowed_channels:
            return True  # No filter = allow all
        return channel in self._allowed_channels

    def _normalize_event(self, event: dict, event_type: str = "message") -> Message | None:
        """Convert a Slack event to a standard Message."""
        user = event.get("user", "unknown")

        # Skip self-messages
        if user == self._bot_user_id:
            return None

        channel = event.get("channel", "")
        channel_type = event.get("channel_type", "")

        if not self._is_allowed(channel, channel_type):
            return None

        # Map Slack channel types
        conv_type = "channel"
        if channel_type in ("im", "mpim"):
            conv_type = "dm"

        return Message(
            connector=ConnectorInfo(type="slack", instance=self.name),
            sender=Sender(
                id=user,
                username=user,
                display_name=event.get("user_profile", {}).get("display_name", user),
            ),
            content=Content(text=event.get("text", "")),
            conversation=Conversation(
                id=channel,
                type=conv_type,
                name=channel,
                thread_id=event.get("thread_ts"),
            ),
            metadata={
                "slack_ts": event.get("ts", ""),
                "event_type": event_type,
            },
        )

    def _register_handlers(self) -> None:
        @self._app.event("message")
        def handle_message(event: dict, say: Any) -> None:
            if event.get("subtype") in ("bot_message", "message_changed", "message_deleted"):
                return
            msg = self._normalize_event(event, "message")
            if msg:
                self.write_to_inbox(msg)

        @self._app.event("app_mention")
        def handle_mention(event: dict, say: Any) -> None:
            msg = self._normalize_event(event, "mention")
            if msg:
                msg.metadata["priority"] = "high"
                self.write_to_inbox(msg)

        @self._app.event("reaction_added")
        def handle_reaction(event: dict, say: Any) -> None:
            msg = Message(
                connector=ConnectorInfo(type="slack", instance=self.name),
                sender=Sender(
                    id=event.get("user", "unknown"),
                    username=event.get("user", "unknown"),
                ),
                content=Content(
                    text=f":{event.get('reaction', '')}:",
                    media_type="reaction",
                ),
                conversation=Conversation(
                    id=event.get("item", {}).get("channel", ""),
                    type="channel",
                ),
                metadata={
                    "event_type": "reaction",
                    "item": event.get("item", {}),
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

    parser = argparse.ArgumentParser(description="Seed Agent Slack Connector")
    parser.add_argument("--seed-home", default=".", help="Seed home directory")
    parser.add_argument("--name", default="slack-main", help="Connector instance name")
    args = parser.parse_args()

    connector = SlackConnector(name=args.name, seed_home=args.seed_home)
    connector.run()
