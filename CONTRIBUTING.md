# Contributing to seed-agent

## Highest-Impact Contributions

### 1. New Connectors

Every new connector expands where seeds can live. See
[WRITING-CONNECTORS.md](connectors/WRITING-CONNECTORS.md) for the developer guide.

Wanted connectors:
- **Matrix** — open-source chat (matrix-nio)
- **GitHub** — issue/PR events via webhooks
- **Twitter/X** — social media engagement
- **WhatsApp** — via Twilio or Meta API
- **RSS** — feed monitoring
- **SMS** — via Twilio

### 2. Context Presets

Share your deployment configuration so others can start faster.
Add a new directory under `contexts/` with:
- `CONSTITUTION.md`
- `PROMPT.md`
- `connectors.yml`
- `memory/` (seed files)

### 3. Network Insights

If your seed has learned something generalizable, publish it as an insight.
See [network/PROTOCOL.md](network/PROTOCOL.md) for the format.

### 4. Documentation

Improve the getting-started experience. First-time deployment should take
under 5 minutes with clear instructions.

## Development Setup

```bash
git clone https://github.com/sfhsdev/seed-agent.git
cd seed-agent
pip install -e ".[dev]"
pytest
```

## Pull Request Guidelines

- Keep PRs focused (one connector, one feature, one fix)
- Include tests for new connectors
- Update relevant documentation
- Test with the CLI connector before submitting

## Code Style

- Python 3.10+ with type hints
- Connectors should be under 250 lines of core logic
- Prefer stdlib over external dependencies where reasonable
- Follow the existing patterns in `connectors/base/`

## License

By contributing, you agree that your contributions will be licensed under
the MIT License.
