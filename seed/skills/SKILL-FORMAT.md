# Skill Format — How to Write a Seed Skill

A skill is a standalone script or tool that the agent can invoke. Skills live
in `seed/skills/` and are discoverable by the agent through this directory.

## Structure

Each skill is a directory containing:

```
skills/
└── my-skill/
    ├── README.md          # What the skill does, when to use it
    ├── run.sh             # Entry point (or run.py)
    └── (supporting files)
```

## Requirements

1. **Self-contained**: A skill should work with minimal dependencies
2. **Documented**: README.md explains what, when, and how
3. **Executable**: `run.sh` or `run.py` as entry point
4. **Exit codes**: 0 = success, non-zero = failure
5. **stdout**: Output results to stdout (the agent reads this)
6. **stderr**: Errors and debug info to stderr

## README.md Template

```markdown
# Skill: [name]

## What It Does
[One sentence description]

## When to Use
[When should the agent invoke this skill?]

## Usage
```bash
./run.sh [arguments]
```

## Arguments
- `arg1`: [description]

## Output
[What the skill outputs on success]

## Dependencies
[Any packages or tools needed]
```

## Example: Web Search Skill

```bash
#!/bin/bash
# skills/web-search/run.sh
# Search the web and return summarized results
query="$1"
if [ -z "$query" ]; then
    echo "Usage: run.sh <search query>" >&2
    exit 1
fi
# Agent would implement the actual search logic
curl -s "https://api.search.example/q=$query" | jq '.results[:5]'
```

## The Agent Can Create Skills

Skills are not pre-defined. The agent can (and should) create new skills
when it identifies recurring tasks. The skill format is intentionally simple
to make this easy.
