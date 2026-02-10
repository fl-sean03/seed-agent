"""
Abstract base connector for seed-agent.

Every connector follows the same contract:
  Platform -> Connector -> normalize to JSON -> write to inbox/
  Agent <- reads inbox/ <- processes
  Agent -> writes JSON to outbox/ -> Connector polls -> sends to Platform

The agent never imports connector code. The filesystem IS the interface.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from connectors.base.message import Message, OutgoingMessage


class Connector(ABC):
    """
    Base class for all seed-agent connectors.

    Subclasses must implement:
        connector_type: str property identifying the platform
        connect(): Authenticate and set up the connection
        disconnect(): Graceful shutdown
        send_message(msg): Send an outgoing message to the platform
        run_loop(): Main event loop (blocking)

    The base class provides:
        write_to_inbox(msg): Write a normalized Message to the inbox
        poll_outbox(): Read and remove outgoing messages from the outbox
        run(): Full lifecycle (connect -> run_loop -> disconnect)
    """

    connector_type: str = ""

    def __init__(
        self,
        name: str,
        seed_home: str | Path,
        config: dict[str, Any] | None = None,
    ):
        self.name = name
        self.seed_home = Path(seed_home)
        self.config = config or {}

        # Standard directories
        self.inbox = self.seed_home / "messages" / "inbox"
        self.outbox = self.seed_home / "messages" / "outbox" / self.name
        self.failed = self.seed_home / "messages" / "failed"
        self.log_dir = self.seed_home / "logs"

        # Create directories
        for d in [self.inbox, self.outbox, self.failed, self.log_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Logger
        self.logger = logging.getLogger(f"connector.{self.name}")
        self._setup_logging()

        # Graceful shutdown
        self._running = True
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _setup_logging(self) -> None:
        log_file = self.log_dir / f"{self.name}.log"
        handler = logging.FileHandler(log_file)
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # Also log to stdout
        stdout_handler = logging.StreamHandler()
        stdout_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        self.logger.addHandler(stdout_handler)

    def _handle_signal(self, signum: int, frame: Any) -> None:
        self.logger.info(f"Received signal {signum}, shutting down...")
        self._running = False

    # --- Methods subclasses MUST implement ---

    @abstractmethod
    def connect(self) -> None:
        """Authenticate and set up the connection to the platform."""
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Graceful shutdown. Clean up resources."""
        ...

    @abstractmethod
    def send_message(self, msg: OutgoingMessage) -> bool:
        """Send an outgoing message to the platform. Return True on success."""
        ...

    @abstractmethod
    def run_loop(self) -> None:
        """
        Main event loop. This should block and process incoming events.
        Check self._running periodically to support graceful shutdown.
        """
        ...

    # --- Methods provided by base class ---

    def write_to_inbox(self, msg: Message) -> Path:
        """Write a normalized incoming message to the agent's inbox."""
        filepath = msg.write_to(self.inbox)
        self.logger.info(
            f"Inbox: [{msg.connector.type}] {msg.sender.username}: "
            f"{msg.content.text[:80]}"
        )
        return filepath

    def poll_outbox(self) -> list[OutgoingMessage]:
        """Read and remove outgoing messages from this connector's outbox."""
        messages = []
        for filepath in sorted(self.outbox.glob("*.json")):
            try:
                msg = OutgoingMessage.from_file(filepath)
                messages.append(msg)
                filepath.unlink()
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.error(f"Bad outbox file {filepath}: {e}")
                # Move to failed
                filepath.rename(self.failed / filepath.name)
        return messages

    def process_outbox(self) -> int:
        """Poll outbox and send all pending messages. Returns count sent."""
        messages = self.poll_outbox()
        sent = 0
        for msg in messages:
            try:
                if self.send_message(msg):
                    sent += 1
                    self.logger.info(
                        f"Outbox: sent to {msg.conversation_id}: {msg.text[:80]}"
                    )
                else:
                    self.logger.warning(f"Failed to send message {msg.id}")
            except Exception as e:
                self.logger.error(f"Error sending message {msg.id}: {e}")
        return sent

    def run(self) -> None:
        """Full connector lifecycle: connect -> run_loop -> disconnect."""
        self.logger.info(f"Starting connector: {self.name} ({self.connector_type})")
        self.logger.info(f"  Inbox:  {self.inbox}")
        self.logger.info(f"  Outbox: {self.outbox}")

        try:
            self.connect()
            self.logger.info(f"Connected to {self.connector_type}")
            self.run_loop()
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        except Exception as e:
            self.logger.error(f"Connector error: {e}", exc_info=True)
        finally:
            self.disconnect()
            self.logger.info(f"Connector {self.name} stopped")

    def get_config(self, key: str, default: Any = None, env_key: str | None = None) -> Any:
        """
        Get a config value. Checks:
        1. Self.config dict
        2. Environment variable (if env_key provided)
        3. Default value
        """
        value = self.config.get(key)
        if value is not None:
            # Expand env vars in string values (e.g. "${SLACK_BOT_TOKEN}")
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_name = value[2:-1]
                return os.environ.get(env_name, default)
            return value
        if env_key:
            return os.environ.get(env_key, default)
        return default
