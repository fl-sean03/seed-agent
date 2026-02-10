# Connectors — Platform Adapters for Seed Agents

Connectors bridge between communication platforms and your seed agent.
Each connector is a standalone process that normalizes platform-specific
events into a standard JSON message format.

## Architecture

```
Platform → Connector Process → normalize to JSON → write to messages/inbox/
Agent ← inotifywait wakes ← reads inbox/ ← processes
Agent → writes JSON to messages/outbox/<connector>/ → Connector polls → sends to Platform
```

**The agent never imports connector code.** The filesystem IS the interface.

## Available Connectors

| Connector | Platform | Auth Method | Dependencies |
|-----------|----------|-------------|--------------|
| **cli** | Terminal | None | None |
| **slack** | Slack | Socket Mode (no public URL) | slack-bolt |
| **discord** | Discord | Bot token | discord.py |
| **telegram** | Telegram | Bot API | python-telegram-bot |
| **email** | Any IMAP/SMTP | Username + password | None (stdlib) |
| **webhook** | Any HTTP client | Optional secret | flask |

## Quick Start

### 1. CLI (simplest — for testing)

```bash
python -m connectors.cli.connector --seed-home ~/seed-agent
```

### 2. Using connectors.yml

```yaml
connectors:
  - name: slack-main
    type: slack
    bot_token: ${SLACK_BOT_TOKEN}
    app_token: ${SLACK_APP_TOKEN}
    channels: ["C0ADZ0C6BK8"]

  - name: email-alerts
    type: email
    imap_host: imap.gmail.com
    smtp_host: smtp.gmail.com
    username: ${EMAIL_USERNAME}
    password: ${EMAIL_PASSWORD}
    poll_interval: 60
```

```python
from connectors.base.manager import ConnectorManager

manager = ConnectorManager.from_config("connectors.yml", seed_home="~/seed-agent")
manager.start()  # Runs all connectors as separate processes
```

### 3. Run a single connector directly

```bash
# Each connector is a standalone script
python -m connectors.slack.connector --seed-home ~/seed-agent
python -m connectors.discord.connector --seed-home ~/seed-agent
python -m connectors.webhook.connector --seed-home ~/seed-agent --port 8080
```

## Standard Message Format

Every connector normalizes to this JSON schema (v1.0):

```json
{
  "version": "1.0",
  "id": "unique-message-id",
  "timestamp": "2026-02-10T16:45:00Z",
  "connector": {
    "type": "slack",
    "instance": "slack-main"
  },
  "sender": {
    "id": "U12345",
    "username": "sean",
    "display_name": "Sean F."
  },
  "content": {
    "text": "Message text here",
    "media_type": "text",
    "attachments": []
  },
  "conversation": {
    "id": "C0ADZ0C6BK8",
    "type": "channel",
    "name": "#general",
    "thread_id": null
  },
  "metadata": {}
}
```

## Process Model

Each connector runs as its own process:
- **Failure isolation**: one connector crashing doesn't affect others
- **Independent restart**: restart one without touching the rest
- **Simple debugging**: read JSON files in messages/inbox/ to see what happened
- **Zero coupling**: the agent and connectors share no code

## Writing Custom Connectors

See [WRITING-CONNECTORS.md](WRITING-CONNECTORS.md) for the developer guide.
