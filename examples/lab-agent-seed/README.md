# Lab Agent — Seed Configuration

A real seed agent deployed for a computational materials science research lab
at CU Boulder. This example shows how to configure a seed for an academic
research context.

## What This Agent Does

- Monitors Slack for questions from lab members
- Maintains knowledge about research projects, people, and publications
- Surfaces connections between different lab members' work
- Tracks HPC job status (when configured)
- Manages the lab website (instruction-only mode)

## Deployment

```bash
# Using the lab context
seed init --context lab

# Or manually
deploy.sh --seed-home ~/lab-agent --context lab
```

## Configuration

Edit `connectors.yml` to add your Slack workspace:

```yaml
connectors:
  - name: slack-lab
    type: slack
    bot_token: ${SLACK_BOT_TOKEN}
    app_token: ${SLACK_APP_TOKEN}
    channels: ["YOUR_CHANNEL_ID"]
```

## Memory Seed Files

The lab context includes memory templates for:
- **MEMORY.md** — Lab members, active projects, publications
- **lessons.md** — Research insights, technical tips, communication patterns
- **self-reflection.md** — Honest self-assessment

## What to Expect

- **Week 1**: Learns names, projects, and communication patterns
- **Week 2**: Starts making connections between research topics
- **Month 1**: Deep knowledge of lab context, proactive suggestions
- **Month 3+**: Institutional memory that no single person has

## Slack Setup

1. Create a Slack app at api.slack.com/apps
2. Enable Socket Mode
3. Add bot scopes: `chat:write`, `channels:history`, `groups:history`, `im:history`, `mpim:history`, `app_mentions:read`, `reactions:read`
4. Install to workspace
5. Set `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` environment variables
