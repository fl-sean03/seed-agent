# Slack Connector

Real-time Slack communication via Socket Mode (no public URL required).

## Setup

1. Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps)
2. Enable **Socket Mode** under Settings
3. Add bot scopes: `chat:write`, `channels:history`, `groups:history`, `im:history`, `app_mentions:read`, `reactions:read`
4. Install the app to your workspace
5. Copy the Bot Token (`xoxb-...`) and App Token (`xapp-...`)

## Install

```bash
pip install seed-agent[slack]
```

## Configuration

```yaml
# connectors.yml
connectors:
  - name: slack-main
    type: slack
    bot_token: ${SLACK_BOT_TOKEN}
    app_token: ${SLACK_APP_TOKEN}
    channels: ["C0ADZ0C6BK8"]  # Channel IDs to monitor (empty = all)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SLACK_BOT_TOKEN` | Bot user OAuth token (`xoxb-...`) |
| `SLACK_APP_TOKEN` | App-level token for Socket Mode (`xapp-...`) |

## Events Handled

- **Messages** — All messages in allowed channels + all DMs
- **Mentions** — @mentions get `priority: high` metadata
- **Reactions** — Tracked as `media_type: reaction`

## Standalone Usage

```bash
python -m connectors.slack.connector --seed-home ~/agent --name slack-main
```
