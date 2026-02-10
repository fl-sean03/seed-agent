# Architecture

## Overview

A seed agent is three things:

1. **An event loop** (bash) that wakes when there's work to do
2. **Connectors** (Python) that bridge communication platforms
3. **Memory** (Markdown) that persists knowledge across cycles

That's it. Everything else — skills, knowledge, behavior — the agent builds itself.

## The Event Loop

```
┌─────────────┐
│  inotifywait │ ← Watches messages/inbox/
│  (sleeping)  │    Zero cost while idle
└──────┬──────┘
       │ File appears
       ▼
┌─────────────┐
│  claude CLI  │ ← Fresh process per cycle
│  (thinking)  │    Reads inbox, writes outbox
└──────┬──────┘
       │ Cycle complete
       ▼
┌─────────────┐
│  Back to     │
│  sleeping    │
└─────────────┘
```

Each cycle is a standalone `claude` CLI invocation. No persistent process,
no accumulated state in RAM. All persistence is through files.

### Why bash?

- Universal (every Linux system has it)
- Self-modifying (the agent can rewrite loop.sh)
- Minimal dependencies (bash + inotifywait)
- The agent can understand and modify its own control flow

## Connectors

```
┌──────────┐    ┌───────────┐    ┌─────────────┐
│  Slack   │───▶│ Connector │───▶│ messages/   │
│  Server  │◀───│ Process   │◀───│ inbox/      │
└──────────┘    └───────────┘    │ outbox/     │
                                  └──────┬──────┘
┌──────────┐    ┌───────────┐           │
│ Discord  │───▶│ Connector │───────────┤
│  Server  │◀───│ Process   │           │
└──────────┘    └───────────┘           │
                                  ┌─────┴──────┐
                                  │   Agent    │
                                  │  (claude)  │
                                  └────────────┘
```

Key design decisions:
- **One process per connector**: crash isolation
- **File-based interface**: zero coupling between agent and connectors
- **Standard message format**: all platforms normalized to same JSON schema
- **Connectors are independent**: restart one without affecting others

## Memory

```
seed/memory/
├── MEMORY.md              ← Always loaded into context
├── lessons.md             ← Accumulated insights
├── self-reflection.md     ← Honest self-assessment
└── (topic files)          ← Agent creates as needed
```

Memory is Markdown because:
- Human-readable (operators can review)
- Git-trackable (version history for free)
- Self-modifiable (agent edits with standard tools)
- No schema migrations (just text files)

The agent's MEMORY.md is loaded into every cycle. It acts as a permanent
context index, linking to detailed topic files.

## Configuration

```
seed-home/
├── seed/
│   ├── loop.sh            ← The event loop
│   ├── PROMPT.md          ← Operating instructions (self-modifying)
│   ├── CONSTITUTION.md    ← Identity & boundaries (self-modifying)
│   ├── memory/            ← Persistent knowledge
│   └── skills/            ← Agent-built capabilities
├── messages/
│   ├── inbox/             ← Incoming (connectors write here)
│   ├── outbox/            ← Outgoing (agent writes here)
│   └── failed/            ← Failed sends
├── logs/                  ← Cycle logs
└── connectors.yml         ← Connector configuration
```

## Self-Modification

The agent can modify:
- `PROMPT.md` — its own operating instructions
- `CONSTITUTION.md` — its identity and boundaries
- `loop.sh` — its event loop
- `memory/*` — its knowledge base
- `skills/*` — its capabilities

This is intentional. A seed agent that can't modify itself can't grow.
The safety model relies on:
- Cycle logging (every modification is recorded)
- Human-readable files (operators can review changes)
- Boundary definitions in CONSTITUTION.md
- Cost limits enforced at the API level

## Process Lifecycle

```
1. Deploy (deploy.sh or seed init)
   → Creates directory structure
   → Copies templates or context preset
   → Installs dependencies

2. Start (seed start or systemd)
   → loop.sh begins watching inbox/
   → Connectors start as separate processes

3. Cycle (triggered by inbox message)
   → inotifywait detects new file
   → claude CLI invoked with PROMPT.md
   → Agent reads inbox, updates memory, writes outbox
   → Connectors send outbox messages

4. Growth (over time)
   → Agent accumulates knowledge in memory/
   → Agent builds new skills in skills/
   → Agent modifies its own PROMPT.md, loop.sh
   → Agent becomes increasingly context-aware
```
