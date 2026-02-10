"""Integration tests — message roundtrip through CLI connector."""

import json
import tempfile
import threading
import time
from pathlib import Path

from connectors.cli.connector import CLIConnector
from connectors.base.message import (
    ConnectorInfo,
    Content,
    Conversation,
    Message,
    OutgoingMessage,
    Sender,
)


class TestMessageRoundtrip:
    """Test full message flow: write to inbox, read from outbox."""

    def test_inbox_write_creates_valid_json(self):
        """Connector writes valid JSON that the agent can read."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = CLIConnector(name="cli-test", seed_home=tmpdir)
            conn.connect()

            msg = Message(
                connector=ConnectorInfo(type="cli", instance="cli-test"),
                sender=Sender(id="u1", username="sean", display_name="Sean"),
                content=Content(text="test message"),
                conversation=Conversation(id="cli", type="dm", name="cli"),
            )
            filepath = conn.write_to_inbox(msg)

            # Verify the file is valid JSON and has correct structure
            data = json.loads(filepath.read_text())
            assert data["version"] == "1.0"
            assert data["content"]["text"] == "test message"
            assert data["sender"]["username"] == "sean"
            assert data["connector"]["type"] == "cli"
            assert data["connector"]["instance"] == "cli-test"

    def test_outbox_read_and_send(self, capsys):
        """Agent writes to outbox, connector reads and sends."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = CLIConnector(name="cli-test", seed_home=tmpdir)
            conn.connect()

            # Simulate agent writing to outbox
            out_msg = OutgoingMessage(
                connector_instance="cli-test",
                conversation_id="cli",
                text="agent response",
            )
            out_msg.write_to(conn.outbox)

            # Connector processes outbox
            sent = conn.process_outbox()
            assert sent == 1

            captured = capsys.readouterr()
            assert "agent response" in captured.out

    def test_multiple_messages_ordered(self):
        """Multiple messages are processed in chronological order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = CLIConnector(name="cli-test", seed_home=tmpdir)
            conn.connect()

            # Write 3 messages
            for i in range(3):
                msg = Message(
                    connector=ConnectorInfo(type="cli", instance="cli-test"),
                    sender=Sender(id="u1", username="user"),
                    content=Content(text=f"message {i}"),
                    conversation=Conversation(id="cli", type="dm"),
                )
                msg.write_to(conn.inbox)
                time.sleep(0.01)  # Ensure different timestamps

            # Read all inbox files
            files = sorted(conn.inbox.glob("*.json"))
            assert len(files) == 3

            # Verify order
            texts = []
            for f in files:
                data = json.loads(f.read_text())
                texts.append(data["content"]["text"])
            assert texts == ["message 0", "message 1", "message 2"]

    def test_outbox_per_connector_isolation(self):
        """Each connector has its own outbox directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn1 = CLIConnector(name="cli-1", seed_home=tmpdir)
            conn2 = CLIConnector(name="cli-2", seed_home=tmpdir)

            # They share inbox but have separate outboxes
            assert conn1.inbox == conn2.inbox
            assert conn1.outbox != conn2.outbox
            assert conn1.outbox.name == "cli-1"
            assert conn2.outbox.name == "cli-2"

    def test_failed_messages_moved(self):
        """Bad outbox files are moved to failed/, not lost."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = CLIConnector(name="cli-test", seed_home=tmpdir)

            # Write invalid JSON to outbox
            bad = conn.outbox / "bad.json"
            bad.write_text("{invalid json")

            messages = conn.poll_outbox()
            assert len(messages) == 0

            # File moved to failed/
            assert (conn.failed / "bad.json").exists()
            assert not bad.exists()


class TestConnectorConfig:
    """Test config handling edge cases."""

    def test_empty_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = CLIConnector(name="test", seed_home=tmpdir)
            assert conn.get_config("nonexistent") is None
            assert conn.get_config("nonexistent", "default") == "default"

    def test_nested_outbox_creation(self):
        """Outbox directories are created even for deeply nested paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = CLIConnector(name="deep-nested-name", seed_home=tmpdir)
            assert conn.outbox.is_dir()
            assert conn.outbox.name == "deep-nested-name"
