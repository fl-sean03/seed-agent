"""Tests for the standard message format."""

import json
import tempfile
from pathlib import Path

from connectors.base.message import (
    ConnectorInfo,
    Content,
    Conversation,
    Message,
    OutgoingMessage,
    Sender,
)


def _make_message(**kwargs):
    defaults = dict(
        connector=ConnectorInfo(type="test", instance="test-1"),
        sender=Sender(id="u1", username="testuser", display_name="Test User"),
        content=Content(text="hello world"),
        conversation=Conversation(id="c1", type="channel", name="#test"),
    )
    defaults.update(kwargs)
    return Message(**defaults)


class TestMessage:
    def test_create_message(self):
        msg = _make_message()
        assert msg.version == "1.0"
        assert msg.connector.type == "test"
        assert msg.sender.username == "testuser"
        assert msg.content.text == "hello world"
        assert msg.conversation.id == "c1"
        assert msg.id  # UUID generated

    def test_to_dict(self):
        msg = _make_message()
        d = msg.to_dict()
        assert d["version"] == "1.0"
        assert d["connector"]["type"] == "test"
        assert d["sender"]["username"] == "testuser"
        assert d["content"]["text"] == "hello world"

    def test_to_json(self):
        msg = _make_message()
        j = msg.to_json()
        parsed = json.loads(j)
        assert parsed["content"]["text"] == "hello world"

    def test_from_dict(self):
        msg = _make_message()
        d = msg.to_dict()
        restored = Message.from_dict(d)
        assert restored.content.text == msg.content.text
        assert restored.connector.type == msg.connector.type
        assert restored.sender.id == msg.sender.id

    def test_from_json(self):
        msg = _make_message()
        j = msg.to_json()
        restored = Message.from_json(j)
        assert restored.content.text == "hello world"

    def test_write_and_read(self):
        msg = _make_message()
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = msg.write_to(Path(tmpdir))
            assert filepath.exists()
            assert filepath.suffix == ".json"

            restored = Message.from_file(filepath)
            assert restored.content.text == "hello world"
            assert restored.connector.instance == "test-1"

    def test_metadata(self):
        msg = _make_message(metadata={"priority": "high", "source": "test"})
        assert msg.metadata["priority"] == "high"
        d = msg.to_dict()
        assert d["metadata"]["source"] == "test"

    def test_attachments(self):
        msg = _make_message(
            content=Content(
                text="check this",
                attachments=[{"url": "http://example.com/file.pdf", "name": "file.pdf"}],
            )
        )
        assert len(msg.content.attachments) == 1
        assert msg.content.attachments[0]["url"] == "http://example.com/file.pdf"

    def test_thread_id(self):
        msg = _make_message(
            conversation=Conversation(id="c1", type="channel", thread_id="t123")
        )
        assert msg.conversation.thread_id == "t123"


class TestOutgoingMessage:
    def test_create(self):
        msg = OutgoingMessage(
            connector_instance="slack-main",
            conversation_id="C123",
            text="response text",
        )
        assert msg.connector_instance == "slack-main"
        assert msg.text == "response text"
        assert msg.id  # UUID generated

    def test_to_json(self):
        msg = OutgoingMessage(
            connector_instance="slack-main",
            conversation_id="C123",
            text="hello",
            thread_id="t456",
        )
        j = msg.to_json()
        parsed = json.loads(j)
        assert parsed["connector_instance"] == "slack-main"
        assert parsed["thread_id"] == "t456"

    def test_write_and_read(self):
        msg = OutgoingMessage(
            connector_instance="test",
            conversation_id="c1",
            text="outgoing",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = msg.write_to(Path(tmpdir))
            assert filepath.exists()

            restored = OutgoingMessage.from_file(filepath)
            assert restored.text == "outgoing"
            assert restored.conversation_id == "c1"

    def test_metadata(self):
        msg = OutgoingMessage(
            connector_instance="email",
            conversation_id="user@example.com",
            text="body",
            metadata={"subject": "Re: Hello"},
        )
        assert msg.metadata["subject"] == "Re: Hello"
