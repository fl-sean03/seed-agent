#!/bin/bash
# Skill: Summarize — condense stdin text
# Usage: echo "text" | ./run.sh [max_words]

set -euo pipefail

MAX_WORDS="${1:-100}"
INPUT=$(cat)

if [ -z "$INPUT" ]; then
    echo "Error: No input provided. Pipe text to stdin." >&2
    exit 1
fi

# Count words
WORD_COUNT=$(echo "$INPUT" | wc -w)

if [ "$WORD_COUNT" -le "$MAX_WORDS" ]; then
    # Already short enough
    echo "$INPUT"
else
    # Simple truncation — agent should replace this with LLM summarization
    echo "$INPUT" | tr '\n' ' ' | xargs | cut -d' ' -f1-"$MAX_WORDS"
    echo "... (truncated from $WORD_COUNT words)"
fi
