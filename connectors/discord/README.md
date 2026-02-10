# Discord Connector

Discord bot using discord.py with message content intent.

## Setup

1. Create a Discord application at [discord.com/developers](https://discord.com/developers/applications)
2. Create a Bot under your application
3. Enable **Message Content Intent** under Bot settings
4. Generate an invite URL with `bot` scope and `Send Messages`, `Read Message History` permissions
5. Invite the bot to your server

## Install

```bash
pip install seed-agent[discord]
```

## Configuration

```yaml
# connectors.yml
connectors:
  - name: discord-main
    type: discord
    token: ${DISCORD_TOKEN}
    guilds: []      # Guild IDs to filter (empty = all)
    channels: []    # Channel IDs to filter (empty = all)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DISCORD_TOKEN` | Bot token from developer portal |

## Standalone Usage

```bash
python -m connectors.discord.connector --seed-home ~/agent
```
