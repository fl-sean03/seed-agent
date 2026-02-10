"""Tests for the CLI connector."""

import tempfile
from pathlib import Path

from connectors.cli.connector import CLIConnector


class TestCLIConnector:
    def test_connector_type(self):
        assert CLIConnector.connector_type == "cli"

    def test_init(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = CLIConnector(name="cli-test", seed_home=tmpdir)
            assert conn.name == "cli-test"
            assert conn.connector_type == "cli"

    def test_connect(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = CLIConnector(
                name="cli-test",
                seed_home=tmpdir,
                config={"username": "testuser"},
            )
            conn.connect()
            assert conn._username == "testuser"

    def test_send_message(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = CLIConnector(name="cli-test", seed_home=tmpdir)
            conn.connect()

            from connectors.base.message import OutgoingMessage
            msg = OutgoingMessage(
                connector_instance="cli-test",
                conversation_id="cli",
                text="test response",
            )
            result = conn.send_message(msg)
            assert result is True

            captured = capsys.readouterr()
            assert "test response" in captured.out
