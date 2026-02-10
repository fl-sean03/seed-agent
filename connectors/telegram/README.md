# Telegram Connector

Telegram bot using python-telegram-bot with long polling.

## Setup

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the bot token

## Install

```bash
pip install seed-agent[telegram]
```

## Configuration

```yaml
# connectors.yml
connectors:
  - name: telegram-main
    type: telegram
    token: ${TELEGRAM_BOT_TOKEN}
    allowed_chats: []  # Chat IDs to filter (empty = all)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Token from BotFather |

## Standalone Usage

```bash
python -m connectors.telegram.connector --seed-home ~/agent
```
