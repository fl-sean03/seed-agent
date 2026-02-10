"""Tests that all connectors can be imported regardless of optional deps."""

import importlib


class TestImportSafety:
    """All connector modules must import without their optional deps installed."""

    def test_import_slack(self):
        mod = importlib.import_module("connectors.slack.connector")
        assert hasattr(mod, "SlackConnector")
        assert mod.SlackConnector.connector_type == "slack"

    def test_import_discord(self):
        mod = importlib.import_module("connectors.discord.connector")
        assert hasattr(mod, "DiscordConnector")
        assert mod.DiscordConnector.connector_type == "discord"

    def test_import_telegram(self):
        mod = importlib.import_module("connectors.telegram.connector")
        assert hasattr(mod, "TelegramConnector")
        assert mod.TelegramConnector.connector_type == "telegram"

    def test_import_webhook(self):
        mod = importlib.import_module("connectors.webhook.connector")
        assert hasattr(mod, "WebhookConnector")
        assert mod.WebhookConnector.connector_type == "webhook"

    def test_import_cli(self):
        mod = importlib.import_module("connectors.cli.connector")
        assert hasattr(mod, "CLIConnector")
        assert mod.CLIConnector.connector_type == "cli"

    def test_import_email(self):
        mod = importlib.import_module("connectors.email.connector")
        assert hasattr(mod, "EmailConnector")
        assert mod.EmailConnector.connector_type == "email"

    def test_import_base(self):
        from connectors.base.connector import Connector
        from connectors.base.message import Message, OutgoingMessage
        from connectors.base.manager import ConnectorManager
        assert Connector is not None
        assert Message is not None
        assert ConnectorManager is not None
