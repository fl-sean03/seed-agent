#!/bin/bash
# loop.sh — Event-driven seed agent loop
# The agent only wakes when there's a message to process.
# This file is self-modifying. The agent can and should rewrite it.

set -euo pipefail

SEED_HOME="${SEED_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"
LOG_DIR="$SEED_HOME/logs"
INBOX="$SEED_HOME/messages/inbox"
OUTBOX="$SEED_HOME/messages/outbox"
MEMORY="$SEED_HOME/seed/memory"
PROMPT="$SEED_HOME/seed/PROMPT.md"
CYCLE_COUNT=0
MAX_CYCLE_SECONDS="${MAX_CYCLE_SECONDS:-600}"

mkdir -p "$LOG_DIR" "$INBOX" "$OUTBOX" "$MEMORY"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $*" >> "$LOG_DIR/loop.log"
}

log "Seed agent loop starting (event-driven mode)"
log "SEED_HOME=$SEED_HOME"
log "Waiting for inbox messages..."

# Pre-flight: verify claude CLI is available
if ! command -v claude &>/dev/null; then
    log "ERROR: claude CLI not found in PATH"
    echo "ERROR: claude CLI not found. Install from https://claude.ai/download" >&2
    exit 1
fi

# Pre-flight: verify inotifywait is available
if ! command -v inotifywait &>/dev/null; then
    log "ERROR: inotifywait not found. Install: apt install inotify-tools"
    echo "ERROR: inotifywait not found. Install: sudo apt install inotify-tools" >&2
    exit 1
fi

while true; do
    # Wait for a message to arrive — zero cost while idle
    inotifywait -q -e create "$INBOX" 2>/dev/null || true

    # Brief pause to batch rapid messages
    sleep 2

    # Count messages
    INBOX_COUNT=$(find "$INBOX" -name '*.json' -type f 2>/dev/null | wc -l)
    if [ "$INBOX_COUNT" -eq 0 ]; then
        continue  # Spurious wake
    fi

    CYCLE_COUNT=$((CYCLE_COUNT + 1))
    CYCLE_START=$(date +%s)
    CYCLE_LOG="$LOG_DIR/cycle-$(date +%Y%m%d-%H%M%S).log"

    log "Cycle $CYCLE_COUNT starting ($INBOX_COUNT messages)"
    echo "=== Cycle $CYCLE_COUNT start: $(date) ===" >> "$CYCLE_LOG"
    echo "Inbox messages: $INBOX_COUNT" >> "$CYCLE_LOG"

    # Run the agent for one conversation cycle
    cd "$SEED_HOME"
    timeout "$MAX_CYCLE_SECONDS" claude --dangerously-skip-permissions \
        -p "You have $INBOX_COUNT new message(s) in your inbox at messages/inbox/. Read them, respond via messages/outbox/, and update memory. Follow seed/PROMPT.md." \
        2>&1 | tee -a "$CYCLE_LOG" || true

    CYCLE_END=$(date +%s)
    DURATION=$((CYCLE_END - CYCLE_START))

    echo "=== Cycle $CYCLE_COUNT end: $(date) (${DURATION}s) ===" >> "$CYCLE_LOG"
    log "Cycle $CYCLE_COUNT completed in ${DURATION}s ($INBOX_COUNT messages)"

    # Clean up old cycle logs (keep last 50)
    ls -1t "$LOG_DIR"/cycle-*.log 2>/dev/null | tail -n +51 | xargs -r rm
done
