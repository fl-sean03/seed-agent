"""Tests that connectors raise ImportError at connect() time when deps missing."""

import tempfile
import pytest

from connectors.webhook.connector import WebhookConnector, _HAS_FLASK
from connectors.slack.connector import SlackConnector, _HAS_SLACK
from connectors.discord.connector import DiscordConnector, _HAS_DISCORD
from connectors.telegram.connector import TelegramConnector, _HAS_TELEGRAM


class TestMissingDeps:
    """Connectors without their deps should raise ImportError in connect(), not import."""

    @pytest.mark.skipif(_HAS_FLASK, reason="Flask is installed")
    def test_webhook_missing_flask(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = WebhookConnector(name="test", seed_home=tmpdir)
            with pytest.raises(ImportError, match="Flask"):
                conn.connect()

    @pytest.mark.skipif(_HAS_SLACK, reason="slack-bolt is installed")
    def test_slack_missing_bolt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = SlackConnector(name="test", seed_home=tmpdir)
            with pytest.raises(ImportError, match="slack-bolt"):
                conn.connect()

    @pytest.mark.skipif(_HAS_DISCORD, reason="discord.py is installed")
    def test_discord_missing_discordpy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = DiscordConnector(name="test", seed_home=tmpdir)
            with pytest.raises(ImportError, match="discord.py"):
                conn.connect()

    @pytest.mark.skipif(_HAS_TELEGRAM, reason="python-telegram-bot is installed")
    def test_telegram_missing_telegrambot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = TelegramConnector(name="test", seed_home=tmpdir)
            with pytest.raises(ImportError, match="python-telegram-bot"):
                conn.connect()
