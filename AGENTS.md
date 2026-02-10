# AGENTS.md

This repository contains a framework for deploying autonomous AI agents
(seed agents) that grow through experience.

## Agent Capabilities

A seed agent can:
- Receive and respond to messages across multiple platforms (Slack, Discord, Telegram, Email, HTTP webhooks, CLI)
- Maintain persistent memory in Markdown files
- Self-modify its own operating instructions, event loop, and capabilities
- Build and execute skills (standalone scripts)
- Share knowledge with other seeds via the network protocol

## Architecture

- **Engine**: bash event loop (`seed/loop.sh`) using inotifywait for zero-cost idle
- **Connectors**: Python processes that bridge communication platforms to a file-based inbox/outbox
- **Memory**: Self-modifying Markdown files loaded into every agent cycle
- **Skills**: Standalone scripts the agent creates and invokes

## Entry Points

- `seed/loop.sh` — Main agent event loop
- `connectors/cli/connector.py` — CLI connector for testing
- `connectors/base/manager.py` — Multi-connector orchestrator
- `deploy/seed` — CLI management tool (init/start/stop/status)
- `deploy/deploy.sh` — Deployment script

## Configuration

- `connectors.yml` — Connector configuration (created at deploy time)
- `seed/PROMPT.md` — Agent operating instructions (self-modifying)
- `seed/CONSTITUTION.md` — Agent identity and boundaries (self-modifying)

## Human-in-the-Loop

Actions requiring human confirmation are defined in `seed/CONSTITUTION.md`.
All agent actions are logged in `logs/cycle-*.log`. Memory files are
human-readable Markdown for operator oversight.
