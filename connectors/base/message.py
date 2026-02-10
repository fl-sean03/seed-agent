"""
Standard message format for seed-agent connectors.

All connectors normalize platform-specific messages into this format.
The agent reads/writes these JSON files — it never touches connector code.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ConnectorInfo:
    """Identifies which connector produced/consumes a message."""
    type: str          # "slack", "discord", "cli", etc.
    instance: str      # "slack-main", "discord-dev", etc.


@dataclass
class Sender:
    """Who sent the message."""
    id: str
    username: str
    display_name: str = ""


@dataclass
class Content:
    """Message content."""
    text: str
    media_type: str = "text"           # "text", "image", "file", etc.
    attachments: list[dict] = field(default_factory=list)


@dataclass
class Conversation:
    """Where the message was sent."""
    id: str
    type: str = "channel"              # "channel", "dm", "group", "thread"
    name: str = ""
    thread_id: str | None = None


@dataclass
class Message:
    """
    Standard incoming message format (v1.0).

    Every connector normalizes platform-specific events into this structure.
    Written as JSON to the agent's inbox directory.
    """
    connector: ConnectorInfo
    sender: Sender
    content: Content
    conversation: Conversation
    version: str = "1.0"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def write_to(self, directory: Path) -> Path:
        """Write message as JSON to a directory. Returns the file path."""
        directory.mkdir(parents=True, exist_ok=True)
        # Use connector instance + timestamp for unique, sortable filenames
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{self.connector.instance}_{ts}.json"
        filepath = directory / filename
        filepath.write_text(self.to_json())
        return filepath

    @classmethod
    def from_dict(cls, data: dict) -> Message:
        return cls(
            version=data.get("version", "1.0"),
            id=data.get("id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", ""),
            connector=ConnectorInfo(**data["connector"]),
            sender=Sender(**data["sender"]),
            content=Content(**data["content"]),
            conversation=Conversation(**data["conversation"]),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> Message:
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_file(cls, filepath: Path) -> Message:
        return cls.from_json(filepath.read_text())


@dataclass
class OutgoingMessage:
    """
    Message the agent writes to outbox for a connector to send.

    The agent writes these to messages/outbox/<connector-instance>/.
    Each connector polls its outbox directory and sends messages.
    """
    connector_instance: str            # Which connector should send this
    conversation_id: str               # Where to send it
    text: str                          # What to send
    thread_id: str | None = None       # Reply to thread (optional)
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def write_to(self, directory: Path) -> Path:
        """Write outgoing message to a directory. Returns the file path."""
        directory.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        filename = f"out_{ts}.json"
        filepath = directory / filename
        filepath.write_text(self.to_json())
        return filepath

    @classmethod
    def from_dict(cls, data: dict) -> OutgoingMessage:
        return cls(
            connector_instance=data["connector_instance"],
            conversation_id=data["conversation_id"],
            text=data["text"],
            thread_id=data.get("thread_id"),
            metadata=data.get("metadata", {}),
            id=data.get("id", str(uuid.uuid4())),
        )

    @classmethod
    def from_file(cls, filepath: Path) -> OutgoingMessage:
        return cls.from_dict(json.loads(filepath.read_text()))
