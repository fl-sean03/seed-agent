"""Tests for the connector base class."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from connectors.base.connector import Connector
from connectors.base.message import (
    ConnectorInfo,
    Content,
    Conversation,
    Message,
    OutgoingMessage,
    Sender,
)


class DummyConnector(Connector):
    """Minimal connector implementation for testing."""

    connector_type = "dummy"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connected = False
        self.disconnected = False
        self.sent_messages = []

    def connect(self):
        self.connected = True

    def disconnect(self):
        self.disconnected = True

    def send_message(self, msg):
        self.sent_messages.append(msg)
        return True

    def run_loop(self):
        pass


class TestConnectorBase:
    def test_init_creates_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = DummyConnector(name="test", seed_home=tmpdir)
            assert (Path(tmpdir) / "messages" / "inbox").is_dir()
            assert (Path(tmpdir) / "messages" / "outbox" / "test").is_dir()
            assert (Path(tmpdir) / "messages" / "failed").is_dir()
            assert (Path(tmpdir) / "logs").is_dir()

    def test_write_to_inbox(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = DummyConnector(name="test", seed_home=tmpdir)
            msg = Message(
                connector=ConnectorInfo(type="dummy", instance="test"),
                sender=Sender(id="u1", username="user"),
                content=Content(text="hello"),
                conversation=Conversation(id="c1", type="dm"),
            )
            filepath = conn.write_to_inbox(msg)
            assert filepath.exists()

            data = json.loads(filepath.read_text())
            assert data["content"]["text"] == "hello"

    def test_poll_outbox(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = DummyConnector(name="test", seed_home=tmpdir)

            # Write an outgoing message to the outbox
            out_msg = OutgoingMessage(
                connector_instance="test",
                conversation_id="c1",
                text="response",
            )
            out_msg.write_to(conn.outbox)

            # Poll should return it and delete the file
            messages = conn.poll_outbox()
            assert len(messages) == 1
            assert messages[0].text == "response"

            # File should be deleted
            assert len(list(conn.outbox.glob("*.json"))) == 0

    def test_process_outbox(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = DummyConnector(name="test", seed_home=tmpdir)

            # Write two outgoing messages
            for text in ["msg1", "msg2"]:
                OutgoingMessage(
                    connector_instance="test",
                    conversation_id="c1",
                    text=text,
                ).write_to(conn.outbox)

            sent = conn.process_outbox()
            assert sent == 2
            assert len(conn.sent_messages) == 2

    def test_get_config_from_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = DummyConnector(
                name="test",
                seed_home=tmpdir,
                config={"key1": "value1", "key2": "value2"},
            )
            assert conn.get_config("key1") == "value1"
            assert conn.get_config("missing", "default") == "default"

    def test_get_config_env_expansion(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = DummyConnector(
                name="test",
                seed_home=tmpdir,
                config={"token": "${TEST_SEED_TOKEN}"},
            )
            with patch.dict("os.environ", {"TEST_SEED_TOKEN": "secret123"}):
                assert conn.get_config("token") == "secret123"

    def test_get_config_env_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = DummyConnector(name="test", seed_home=tmpdir)
            with patch.dict("os.environ", {"MY_TOKEN": "from_env"}):
                assert conn.get_config("missing", env_key="MY_TOKEN") == "from_env"

    def test_run_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = DummyConnector(name="test", seed_home=tmpdir)
            conn.run()
            assert conn.connected
            assert conn.disconnected

    def test_bad_outbox_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = DummyConnector(name="test", seed_home=tmpdir)

            # Write invalid JSON to outbox
            bad_file = conn.outbox / "bad.json"
            bad_file.write_text("not json")

            messages = conn.poll_outbox()
            assert len(messages) == 0

            # Should be moved to failed
            assert (conn.failed / "bad.json").exists()
