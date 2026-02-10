"""
Webhook Connector — Generic HTTP endpoint using Flask.

Accepts POST requests with JSON payloads, normalizes to standard format.
Enables integration with any platform that can send HTTP webhooks.

Requires: flask
Install: pip install seed-agent[webhook]

Config (connectors.yml):
  - name: webhook-main
    type: webhook
    host: 0.0.0.0
    port: 8080
    secret: ${WEBHOOK_SECRET}    # Optional: verify X-Webhook-Secret header
    path: /webhook               # Endpoint path

Expected POST body:
{
    "sender": "username",
    "text": "message text",
    "channel": "channel-name",     # optional
    "thread_id": "thread-id",      # optional
    "metadata": {}                 # optional
}
"""

from __future__ import annotations

import hashlib
import hmac
import json
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
    from flask import Flask, request, jsonify
except ImportError:
    raise ImportError(
        "Webhook connector requires Flask. Install: pip install seed-agent[webhook]"
    )


class WebhookConnector(Connector):
    """Generic HTTP webhook connector using Flask."""

    connector_type = "webhook"

    def connect(self) -> None:
        self._host = self.get_config("host", "0.0.0.0")
        self._port = int(self.get_config("port", 8080))
        self._secret = self.get_config("secret", env_key="WEBHOOK_SECRET")
        self._path = self.get_config("path", "/webhook")
        self._poll_interval = self.config.get("outbox_poll_interval", 2.0)

        # Response callbacks for synchronous webhook replies
        self._pending_responses: dict[str, str] = {}

        self._flask_app = Flask(f"seed-webhook-{self.name}")
        self._register_routes()
        self.logger.info(f"Webhook endpoint: http://{self._host}:{self._port}{self._path}")

    def disconnect(self) -> None:
        self.logger.info("Webhook connector disconnecting")

    def send_message(self, msg: OutgoingMessage) -> bool:
        # For webhooks, "sending" means storing for the next poll
        # or calling back a registered callback URL
        callback_url = msg.metadata.get("callback_url")
        if callback_url:
            try:
                import urllib.request
                req = urllib.request.Request(
                    callback_url,
                    data=json.dumps({"text": msg.text}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                urllib.request.urlopen(req, timeout=10)
                return True
            except Exception as e:
                self.logger.error(f"Callback failed: {e}")
                return False
        else:
            # Store for /response endpoint polling
            self._pending_responses[msg.conversation_id] = msg.text
            return True

    def run_loop(self) -> None:
        # Start outbox poller
        poller = threading.Thread(target=self._poll_outbox_loop, daemon=True)
        poller.start()

        # Run Flask (blocks)
        self._flask_app.run(
            host=self._host,
            port=self._port,
            debug=False,
            use_reloader=False,
        )

    def _verify_secret(self, req_secret: str | None) -> bool:
        """Verify webhook secret if configured."""
        if not self._secret:
            return True
        if not req_secret:
            return False
        return hmac.compare_digest(req_secret, self._secret)

    def _register_routes(self) -> None:
        @self._flask_app.post(self._path)
        def handle_webhook() -> tuple:
            # Verify secret
            req_secret = request.headers.get("X-Webhook-Secret")
            if not self._verify_secret(req_secret):
                return jsonify({"error": "unauthorized"}), 401

            data = request.get_json(silent=True)
            if not data:
                return jsonify({"error": "invalid JSON"}), 400

            text = data.get("text", "")
            if not text:
                return jsonify({"error": "text required"}), 400

            sender = data.get("sender", "webhook-user")
            channel = data.get("channel", "webhook")

            msg = Message(
                connector=ConnectorInfo(type="webhook", instance=self.name),
                sender=Sender(
                    id=sender,
                    username=sender,
                    display_name=data.get("display_name", sender),
                ),
                content=Content(text=text),
                conversation=Conversation(
                    id=channel,
                    type="channel",
                    name=channel,
                    thread_id=data.get("thread_id"),
                ),
                metadata=data.get("metadata", {}),
            )

            filepath = self.write_to_inbox(msg)
            return jsonify({
                "status": "delivered",
                "message_id": msg.id,
            }), 200

        @self._flask_app.get(f"{self._path}/health")
        def health() -> tuple:
            return jsonify({"status": "ok", "connector": self.name}), 200

        @self._flask_app.get(f"{self._path}/response/<conversation_id>")
        def get_response(conversation_id: str) -> tuple:
            """Poll for a response to a specific conversation."""
            text = self._pending_responses.pop(conversation_id, None)
            if text:
                return jsonify({"text": text}), 200
            return jsonify({"text": None}), 204

    def _poll_outbox_loop(self) -> None:
        while self._running:
            try:
                self.process_outbox()
            except Exception as e:
                self.logger.error(f"Outbox poll error: {e}")
            time.sleep(self._poll_interval)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed Agent Webhook Connector")
    parser.add_argument("--seed-home", default=".", help="Seed home directory")
    parser.add_argument("--name", default="webhook-main", help="Connector instance name")
    parser.add_argument("--port", default=8080, type=int, help="Port to listen on")
    args = parser.parse_args()

    connector = WebhookConnector(
        name=args.name,
        seed_home=args.seed_home,
        config={"port": args.port},
    )
    connector.run()
