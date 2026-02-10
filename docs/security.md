# Security Model

## Philosophy

A seed agent has broad permissions by design — it can modify its own code,
create files, run commands. This is necessary for self-evolution. Security
comes from:

1. **Boundaries** (CONSTITUTION.md) — what requires human confirmation
2. **Transparency** (cycle logs) — every action is logged
3. **Isolation** (process model) — connectors are separate processes
4. **Cost limits** (API-level) — enforced at the provider
5. **Review** (human-readable files) — operators can audit everything

## Threat Model

### What seeds protect against

| Threat | Mitigation |
|--------|-----------|
| Runaway costs | Cost targets in CONSTITUTION.md + API-level limits |
| Unauthorized communication | Draft-only mode for external messages |
| Credential exposure | Never log credentials, .env in .gitignore |
| Self-destructive modification | Cycle logs capture all changes |
| Connector compromise | Process isolation, per-connector permissions |

### What seeds do NOT protect against

| Threat | Why |
|--------|-----|
| Determined adversarial input | The agent processes all inbox messages |
| Prompt injection via messages | Same as any LLM-based system |
| Operator compromise | The operator has full access by design |
| API key theft | Standard credential management practices apply |

## Best Practices

### Credentials
- Store all secrets in `.env` files (gitignored)
- Use environment variable references in `connectors.yml` (e.g., `${SLACK_BOT_TOKEN}`)
- Never hardcode tokens in connector code
- Rotate credentials periodically

### Network
- Run connectors on internal networks where possible
- Use Socket Mode (Slack) or long polling (Telegram) to avoid exposing ports
- If using the webhook connector, configure a secret and verify it
- Use TLS for all external connections

### Monitoring
- Review cycle logs regularly, especially after initial deployment
- Monitor memory/ for unexpected changes
- Set up alerts for unusual API cost patterns
- Review PROMPT.md and CONSTITUTION.md changes

### Connector Security
- Each connector runs as its own process
- Limit channel/guild filters to only needed channels
- Use the most restrictive bot permissions available
- For email, use app-specific passwords (not your main password)

### File Permissions
```bash
# Recommended permissions
chmod 700 ~/seed-agent                    # Only owner
chmod 600 ~/seed-agent/.env              # Secrets
chmod 755 ~/seed-agent/seed/loop.sh      # Executable
chmod 644 ~/seed-agent/seed/memory/*.md  # Readable
```

## The Self-Modification Question

"Isn't it dangerous to let the agent modify its own code?"

Short answer: It's a feature, not a bug.

Longer answer: The agent's self-modifications are:
- **Logged**: every cycle records what changed
- **Reviewable**: all files are human-readable Markdown or bash
- **Reversible**: git tracks everything (if you init a repo)
- **Bounded**: CONSTITUTION.md defines what requires confirmation

The alternative — an agent that can't self-modify — is an agent that can't
grow. The entire point of a seed is that it evolves. The security model is
transparency + boundaries, not restriction.
