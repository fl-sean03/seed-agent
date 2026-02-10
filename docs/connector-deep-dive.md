# Connector Deep Dive

## Why Connectors Are the Core Feature

The seed engine (loop.sh + memory) is simple by design. The connectors are
what make a seed useful — they're the interface between the agent and the world.

OpenClaw (179K stars) has 14+ channel plugins. That extensibility is a major
factor in their adoption. We take a similar approach but with a simpler,
more isolated architecture.

## Architecture Comparison

| Aspect | OpenClaw | Seed Framework |
|--------|----------|---------------|
| Language | TypeScript | Python |
| Coupling | Gateway layer (tight) | Filesystem (zero) |
| Plugin SDK | Complex manifest + hooks | Simple ABC, 4 methods |
| Process model | Single process, all channels | Separate process per connector |
| Failure mode | One channel can crash all | Failures isolated |
| Debugging | Protocol layers | Read JSON files |
| Custom connectors | Complex SDK | 200-line Python class |

## The Filesystem Interface

This is the key insight: **the filesystem is the API**.

```
Connector → write JSON → messages/inbox/
                                    ↓
                         inotifywait wakes agent
                                    ↓
                         Agent reads, processes
                                    ↓
Agent → write JSON → messages/outbox/<connector>/
                                    ↓
                         Connector polls, sends
```

Benefits:
- **Zero coupling**: Agent and connectors share no code, no imports, no types
- **Language agnostic**: Connectors could be written in any language
- **Debuggable**: `cat messages/inbox/*.json` shows exactly what happened
- **Reliable**: Files persist through crashes, restarts, upgrades
- **Simple**: No message brokers, no queues, no pub/sub

## Message Flow in Detail

### Incoming (Platform → Agent)

1. Platform event arrives (Slack message, Discord event, email, etc.)
2. Connector receives it via platform SDK
3. Connector normalizes to standard Message format
4. Connector writes JSON file to `messages/inbox/`
5. inotifywait detects the new file
6. Agent loop wakes and starts a new cycle
7. Agent reads all inbox messages
8. Agent processes and deletes the files

### Outgoing (Agent → Platform)

1. Agent decides to send a message
2. Agent writes JSON to `messages/outbox/<connector-name>/`
3. Connector's outbox poller (every 2s) detects the file
4. Connector reads the OutgoingMessage JSON
5. Connector sends via platform SDK
6. Connector deletes the file on success
7. On failure, moves to `messages/failed/`

### Failure Handling

- **Connector crash**: Other connectors unaffected. Manager auto-restarts.
- **Send failure**: Message moved to `messages/failed/`, not lost.
- **Agent crash**: Unprocessed inbox messages remain for next cycle.
- **Manager crash**: All connectors stop. Systemd restarts.

## Multi-Connector Orchestration

The `ConnectorManager` runs multiple connectors as separate processes:

```python
from connectors.base.manager import ConnectorManager

manager = ConnectorManager.from_config("connectors.yml", seed_home="/path")
manager.start()  # Blocks, monitors all connectors
```

Features:
- Auto-restart on crash (configurable delay)
- Status reporting (`manager.status()`)
- Graceful shutdown on SIGTERM/SIGINT
- Per-connector logging

## Writing a New Connector

The barrier is intentionally low. A working connector needs:

1. **A class** that extends `Connector` with `connector_type` set
2. **Four methods**: `connect()`, `disconnect()`, `send_message()`, `run_loop()`
3. That's it.

The base class handles:
- Directory creation
- Logging setup
- Signal handling
- Inbox writing (`write_to_inbox()`)
- Outbox polling (`poll_outbox()`, `process_outbox()`)
- Config with env var expansion (`get_config()`)
- Full lifecycle (`run()`)

See [WRITING-CONNECTORS.md](../connectors/WRITING-CONNECTORS.md) for the
complete developer guide.

## Connector-Specific Notes

### CLI
- Simplest connector, ~70 lines
- stdin/stdout, great for testing
- No external dependencies

### Slack
- Uses Socket Mode (no public URL needed)
- Handles messages, mentions, reactions
- Filters by channel allowlist + allows all DMs

### Discord
- Uses discord.py with message_content intent
- Filters by guild and/or channel
- Handles DMs and server messages

### Telegram
- Uses python-telegram-bot with long polling
- Filters by chat ID allowlist
- Handles private and group chats

### Email
- Pure stdlib (imaplib/smtplib) — no external deps
- Polls IMAP for unseen messages
- Sends via SMTP with TLS
- Handles threading via In-Reply-To headers

### Webhook
- Flask HTTP endpoint
- Accepts POST with JSON body
- Optional secret verification
- Includes health check and response polling endpoints
- Enables integration with any platform that can send HTTP
