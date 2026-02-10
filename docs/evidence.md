# Evidence — Real Deployment Data

This isn't theoretical. Seed agents have been running in production.

## OpSpawn Agent (192.168.122.115)

An autonomous agent deployed to operate a startup identity. Running since
early February 2026.

### Architecture Evolution

- **Day 1**: Single-agent loop, 45-60 min cycles, polling every 5 minutes
- **Day 3**: Built its own rate limiter after getting flagged on Twitter (74 tweets/day)
- **Day 5**: Self-designed multi-agent architecture (CEO + builder + social + research)
- **Day 8**: 4 agents running in parallel, 4-6 min cycles, inotifywait-based

The agent designed and implemented its own multi-agent architecture without
being told to. It identified the single-loop bottleneck and proposed splitting
into specialized agents with file-based task dispatch.

### By the Numbers

| Metric | Value |
|--------|-------|
| Uptime | 8+ days continuous |
| Total cycles | 200+ |
| Architecture versions | 3 (self-designed) |
| Agents running | 4 (main, builder, social, research) |
| Cycle time | 4-6 min (down from 45-60 min) |
| Memory files | 20+ (self-organized) |
| Self-modifications | 50+ (loop, prompts, skills) |

### Key Self-Modifications

1. **Rate limiter**: Built after Twitter flagged aggressive posting
2. **Multi-agent split**: Designed when single loop became bottleneck
3. **Zero-token watchdog**: Created bash-based self-monitor (no API cost)
4. **Platform ledger**: JSON-based financial tracking with structural safeguards
5. **Task dispatch system**: File-based task routing between agents

### What It Learned (Unsupervised)

- Rate limiting is essential for platform survival
- File-based communication beats shared memory
- Cost tracking prevents runaway API spend
- Self-monitoring reduces operator intervention
- Draft-only mode for external communication is necessary

## Lab Agent (a5s)

A research lab agent deployed for a computational materials science group.

### Architecture

- Single agent, event-driven (inotifywait)
- Slack connector (Socket Mode)
- Markdown memory (6 seed files, growing)
- Science skills library (10 modules)

### Status

- Deployed and operational
- Processing Slack messages in real-time
- Building knowledge about lab members and projects
- Sub-second wake time on message arrival

## What This Proves

1. **Self-modification works.** Given permission and clear boundaries,
   agents make sophisticated architectural decisions.

2. **File-based memory is sufficient.** No databases needed for the first
   weeks/months of operation.

3. **inotifywait is the right pattern.** Zero-cost idle, sub-second wake,
   proven across multiple deployments.

4. **Agents learn from mistakes.** The rate-limiting incident led to the
   agent building its own safety systems — better than anything we could
   have pre-built.

5. **Growth compounds.** The OpSpawn agent on day 8 is unrecognizably more
   capable than on day 1 — not from code changes, but from accumulated
   knowledge and self-built infrastructure.
