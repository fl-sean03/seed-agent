# seed-agent

**Deploy autonomous AI agents that grow through experience.**

A seed agent is not a product with features. It's a framework that becomes
uniquely valuable through accumulated knowledge. Deploy a seed, connect it to
your platforms, and let it evolve.

```bash
# Deploy a seed agent in under 5 minutes
git clone https://github.com/sfhsdev/seed-agent.git
cd seed-agent
bash deploy/deploy.sh --seed-home ~/agent --context developer
```

---

## What is a seed agent?

Three components. That's it.

1. **An event loop** (bash + inotifywait) — zero cost while idle, wakes in <1s
2. **Connectors** (Python) — plug into any platform: Slack, Discord, Telegram, Email, webhooks
3. **Memory** (Markdown files) — knowledge that persists and compounds across every cycle

The agent reads messages from an inbox, thinks, writes responses to an outbox,
and updates its memory. Connectors handle the platform-specific translation.
The filesystem is the API.

```
Platform → Connector → JSON → messages/inbox/
                                      ↓
                              Agent wakes, processes
                                      ↓
              Platform ← Connector ← JSON ← messages/outbox/
```

## Why seeds instead of products?

Traditional AI tools ship with fixed features. A seed ships with **potential**.

| | Traditional AI Tool | Seed Agent |
|---|---|---|
| Day 1 | Full features, no context | Basic, but learning |
| Day 30 | Same as day 1 | Deeply contextual |
| Day 100 | Same as day 1 | Irreplaceable |
| Knowledge | Resets every conversation | Compounds permanently |
| Behavior | Same for everyone | Unique to your deployment |

A seed deployed for a research lab becomes a different intelligence than one
deployed for a startup. They diverge because their experiences diverge.

## Connectors — The Extensible Interface

Connect your seed to any communication platform. Each connector is a standalone
process with zero coupling to the agent.

| Connector | Platform | Dependencies | Lines |
|-----------|----------|-------------|-------|
| `cli` | Terminal (stdin/stdout) | None | ~70 |
| `slack` | Slack (Socket Mode) | slack-bolt | ~200 |
| `discord` | Discord | discord.py | ~180 |
| `telegram` | Telegram | python-telegram-bot | ~180 |
| `email` | Any IMAP/SMTP | None (stdlib) | ~200 |
| `webhook` | Any HTTP client | flask | ~180 |

Run multiple connectors simultaneously:

```yaml
# connectors.yml
connectors:
  - name: slack-team
    type: slack
    bot_token: ${SLACK_BOT_TOKEN}
    app_token: ${SLACK_APP_TOKEN}

  - name: email-alerts
    type: email
    imap_host: imap.gmail.com
    username: ${EMAIL_USERNAME}
    password: ${EMAIL_PASSWORD}
```

**Writing a custom connector takes ~200 lines.** See [WRITING-CONNECTORS.md](connectors/WRITING-CONNECTORS.md).

## Quick Start

### Prerequisites

- Python 3.10+
- `inotify-tools` (`sudo apt install inotify-tools`)
- [Claude Code CLI](https://claude.ai/download)

### 1. Clone and install

```bash
git clone https://github.com/sfhsdev/seed-agent.git
cd seed-agent
pip install -e "."                    # Base install
pip install -e ".[slack]"             # + Slack connector
pip install -e ".[all]"              # All connectors
```

### 2. Deploy a seed

```bash
# Bare seed (configure yourself)
bash deploy/deploy.sh --seed-home ~/agent

# Or use a context preset
bash deploy/deploy.sh --seed-home ~/agent --context lab       # Research lab
bash deploy/deploy.sh --seed-home ~/agent --context startup   # Startup ops
bash deploy/deploy.sh --seed-home ~/agent --context developer # Dev productivity
bash deploy/deploy.sh --seed-home ~/agent --context personal  # Personal assistant
```

### 3. Start the agent

```bash
# Manual start
cd ~/agent && SEED_HOME=~/agent bash seed/loop.sh

# Or use the CLI
./deploy/seed start

# Or install as a systemd service
bash deploy/deploy.sh --seed-home ~/agent --systemd
```

### 4. Connect a platform

```bash
# Test with CLI connector
python -m connectors.cli.connector --seed-home ~/agent

# Or configure connectors.yml and run all
python -c "
from connectors.base.manager import ConnectorManager
manager = ConnectorManager.from_config('connectors.yml', seed_home='$HOME/agent')
manager.start()
"
```

## Context Presets

Pre-configured starting points for common deployments:

| Context | Connectors | Best For |
|---------|-----------|----------|
| `lab` | Slack + Email | Research groups |
| `startup` | Slack + Email | Small teams, business ops |
| `personal` | CLI + Telegram | Personal assistant |
| `developer` | CLI + Webhook | Code projects, CI/CD |

Each context includes customized CONSTITUTION.md, PROMPT.md, memory templates,
and connector configuration.

## The Knowledge Network

Seeds can share knowledge. Publish insights from one seed, query them from another.

```bash
# Publish an insight
./network/publish.sh my-insight.yaml

# Query insights
./network/query.sh --tag rate-limiting
./network/query.sh --domain operations
```

See [network/PROTOCOL.md](network/PROTOCOL.md) for the insight format specification.

## Self-Modification

Seed agents can (and should) modify their own:
- `PROMPT.md` — operating instructions
- `CONSTITUTION.md` — identity and boundaries
- `loop.sh` — event loop behavior
- `memory/` — knowledge base
- `skills/` — capabilities

This is a feature. An agent that can't self-modify can't grow. Safety comes
from transparency (cycle logs), boundaries (CONSTITUTION.md), and human
oversight (readable files).

## Real Deployment Data

This isn't theoretical. See [docs/evidence.md](docs/evidence.md) for data from
actual deployments, including an agent that:

- Self-designed a multi-agent architecture on day 5
- Built its own rate limiter after a platform ban on day 3
- Reduced cycle times from 45 minutes to 4 minutes
- Processed 200+ tasks over 8+ days of continuous operation

## Documentation

| Doc | Description |
|-----|-------------|
| [Architecture](docs/architecture.md) | How the engine works |
| [What to Expect](docs/what-to-expect.md) | Growth timeline for new seeds |
| [Evidence](docs/evidence.md) | Real deployment data |
| [Security](docs/security.md) | Security model and best practices |
| [Connector Deep Dive](docs/connector-deep-dive.md) | Technical connector details |
| [Writing Connectors](connectors/WRITING-CONNECTORS.md) | Build your own connector |
| [Knowledge Network](network/PROTOCOL.md) | Insight sharing protocol |
| [Oracle Free Tier](deploy/cloud/oracle-free-tier.md) | Free cloud deployment |

## Project Structure

```
seed-agent/
├── seed/                   # The engine
│   ├── loop.sh             # Event loop (self-modifying)
│   ├── PROMPT.md.template  # Operating instructions
│   ├── CONSTITUTION.md.template
│   ├── memory/             # Knowledge templates
│   └── skills/             # Capability framework
├── connectors/             # Platform adapters
│   ├── base/               # ABC + message format + manager
│   ├── cli/                # Terminal
│   ├── slack/              # Slack Socket Mode
│   ├── discord/            # discord.py
│   ├── telegram/           # python-telegram-bot
│   ├── email/              # IMAP/SMTP (stdlib)
│   └── webhook/            # Flask HTTP
├── contexts/               # Deployment presets
├── network/                # Knowledge sharing
├── deploy/                 # Deployment tooling
├── docs/                   # Documentation
├── examples/               # Real deployment examples
└── tests/                  # Test suite
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Key areas:

- **New connectors** — the highest-impact contribution
- **Context presets** — share your deployment configuration
- **Network insights** — share what your seed has learned
- **Documentation** — improve the getting-started experience

## License

MIT. See [LICENSE](LICENSE).
