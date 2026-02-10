# CLI Connector

The simplest connector. Reads from stdin, writes to stdout.

## Usage

```bash
python -m connectors.cli.connector --seed-home ~/agent
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--seed-home` | `.` | Path to seed home directory |
| `--name` | `cli` | Connector instance name |
| `--username` | `user` | Username for messages |

## Dependencies

None. Uses only Python stdlib.

## When to Use

- Local testing and development
- Direct terminal interaction
- Debugging message flow (check messages/inbox/ after sending)
