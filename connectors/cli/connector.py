"""
CLI Connector — stdin/stdout reference implementation.

The simplest possible connector. Reads lines from stdin, writes responses
to stdout. Perfect for testing and local development.

Usage:
    python -m connectors.cli.connector --seed-home /path/to/seed
"""

from __future__ import annotations

import sys
import threading
import time

from connectors.base.connector import Connector
from connectors.base.message import (
    ConnectorInfo,
    Content,
    Conversation,
    Message,
    OutgoingMessage,
    Sender,
)


class CLIConnector(Connector):
    """Read from stdin, write to stdout. The simplest seed connector."""

    connector_type = "cli"

    def connect(self) -> None:
        self.logger.info("CLI connector ready. Type messages and press Enter.")
        self._poll_interval = self.config.get("poll_interval", 1.0)
        self._username = self.config.get("username", "user")

    def disconnect(self) -> None:
        self.logger.info("CLI connector stopped.")

    def send_message(self, msg: OutgoingMessage) -> bool:
        print(f"\n[seed] {msg.text}\n", flush=True)
        return True

    def run_loop(self) -> None:
        # Start outbox poller in background
        poller = threading.Thread(target=self._poll_outbox_loop, daemon=True)
        poller.start()

        print("=" * 50)
        print("  Seed Agent — CLI Connector")
        print("  Type a message and press Enter.")
        print("  Ctrl+C to quit.")
        print("=" * 50)
        print()

        while self._running:
            try:
                line = input(f"[{self._username}] ")
            except EOFError:
                break
            except KeyboardInterrupt:
                break

            if not line.strip():
                continue

            # Normalize to standard message format and write to inbox
            msg = Message(
                connector=ConnectorInfo(type="cli", instance=self.name),
                sender=Sender(
                    id=self._username,
                    username=self._username,
                    display_name=self._username,
                ),
                content=Content(text=line.strip()),
                conversation=Conversation(
                    id="cli",
                    type="dm",
                    name="cli",
                ),
            )
            self.write_to_inbox(msg)
            print("  (message delivered to inbox)")

    def _poll_outbox_loop(self) -> None:
        """Background thread: poll outbox and print responses."""
        while self._running:
            try:
                self.process_outbox()
            except Exception as e:
                self.logger.error(f"Outbox poll error: {e}")
            time.sleep(self._poll_interval)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed Agent CLI Connector")
    parser.add_argument(
        "--seed-home",
        default=".",
        help="Path to seed home directory",
    )
    parser.add_argument(
        "--name",
        default="cli",
        help="Connector instance name",
    )
    parser.add_argument(
        "--username",
        default="user",
        help="Username for CLI messages",
    )
    args = parser.parse_args()

    connector = CLIConnector(
        name=args.name,
        seed_home=args.seed_home,
        config={"username": args.username},
    )
    connector.run()
