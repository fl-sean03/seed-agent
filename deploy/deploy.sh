#!/bin/bash
# deploy.sh — Bootstrap a seed agent from scratch
# Usage: ./deploy.sh [--seed-home /path] [--context lab|startup|personal|developer]
#
# This script:
# 1. Checks prerequisites (claude CLI, inotifywait, python3)
# 2. Creates the seed directory structure
# 3. Copies templates (or a context preset)
# 4. Installs Python dependencies
# 5. Optionally installs the systemd service

set -euo pipefail

# Defaults
SEED_HOME="${HOME}/seed-agent"
CONTEXT=""
INSTALL_SYSTEMD=false
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --seed-home) SEED_HOME="$2"; shift 2 ;;
        --context)   CONTEXT="$2"; shift 2 ;;
        --systemd)   INSTALL_SYSTEMD=true; shift ;;
        --help|-h)
            echo "Usage: deploy.sh [--seed-home /path] [--context lab|startup|personal|developer] [--systemd]"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo "======================================"
echo "  Seed Agent — Deployment"
echo "======================================"
echo "  Seed home: $SEED_HOME"
echo "  Context:   ${CONTEXT:-none (bare seed)}"
echo ""

# --- Prerequisites ---
echo "[1/5] Checking prerequisites..."

check_cmd() {
    if ! command -v "$1" &>/dev/null; then
        echo "  MISSING: $1 — $2"
        return 1
    fi
    echo "  OK: $1"
    return 0
}

MISSING=false
check_cmd "claude" "Install from https://claude.ai/download" || MISSING=true
check_cmd "inotifywait" "Install: sudo apt install inotify-tools" || MISSING=true
check_cmd "python3" "Install: sudo apt install python3" || MISSING=true

if $MISSING; then
    echo ""
    echo "Install missing prerequisites and re-run."
    exit 1
fi

echo ""

# --- Create directories ---
echo "[2/5] Creating directory structure..."

mkdir -p "$SEED_HOME"/{seed/memory,seed/skills,messages/inbox,messages/outbox,logs}
echo "  Created: $SEED_HOME/"

# --- Copy templates ---
echo "[3/5] Setting up seed files..."

if [ -n "$CONTEXT" ] && [ -d "$SCRIPT_DIR/contexts/$CONTEXT" ]; then
    echo "  Using context: $CONTEXT"
    cp -rn "$SCRIPT_DIR/contexts/$CONTEXT"/* "$SEED_HOME/seed/" 2>/dev/null || true
else
    # Copy base templates
    for tmpl in "$SCRIPT_DIR"/seed/memory/*.template; do
        [ -f "$tmpl" ] || continue
        dest="$SEED_HOME/seed/memory/$(basename "$tmpl" .template)"
        if [ ! -f "$dest" ]; then
            cp "$tmpl" "$dest"
            echo "  Created: seed/memory/$(basename "$dest")"
        fi
    done

    for tmpl in "$SCRIPT_DIR"/seed/*.template; do
        [ -f "$tmpl" ] || continue
        dest="$SEED_HOME/seed/$(basename "$tmpl" .template)"
        if [ ! -f "$dest" ]; then
            cp "$tmpl" "$dest"
            echo "  Created: seed/$(basename "$dest")"
        fi
    done
fi

# Copy the loop
cp "$SCRIPT_DIR/seed/loop.sh" "$SEED_HOME/seed/loop.sh"
chmod +x "$SEED_HOME/seed/loop.sh"
echo "  Created: seed/loop.sh"

# Copy skills
cp -rn "$SCRIPT_DIR/seed/skills" "$SEED_HOME/seed/" 2>/dev/null || true
find "$SEED_HOME/seed/skills" -name "*.sh" -exec chmod +x {} \;
echo "  Created: seed/skills/"

echo ""

# --- Install Python dependencies ---
echo "[4/5] Installing Python dependencies..."

if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
    cd "$SCRIPT_DIR"
    python3 -m pip install -e "." --quiet 2>/dev/null || {
        echo "  Note: pip install failed. You may need to install manually."
        echo "  Run: cd $SCRIPT_DIR && pip install -e ."
    }
    echo "  Base dependencies installed"
fi

echo ""

# --- Systemd (optional) ---
if $INSTALL_SYSTEMD; then
    echo "[5/5] Installing systemd service..."

    SERVICE_FILE="/etc/systemd/system/seed-agent.service"
    TEMPLATE="$SCRIPT_DIR/deploy/systemd/seed-agent.service.template"

    if [ -f "$TEMPLATE" ]; then
        sudo bash -c "SEED_HOME='$SEED_HOME' USER='$USER' envsubst < '$TEMPLATE' > '$SERVICE_FILE'"
        sudo systemctl daemon-reload
        echo "  Installed: $SERVICE_FILE"
        echo "  Start with: sudo systemctl start seed-agent"
        echo "  Enable on boot: sudo systemctl enable seed-agent"
    else
        echo "  Template not found: $TEMPLATE"
    fi
else
    echo "[5/5] Skipping systemd (use --systemd to install)"
fi

echo ""
echo "======================================"
echo "  Deployment complete!"
echo "======================================"
echo ""
echo "  Start manually:"
echo "    cd $SEED_HOME && SEED_HOME=$SEED_HOME bash seed/loop.sh"
echo ""
echo "  Or with a connector:"
echo "    python -m connectors.cli.connector --seed-home $SEED_HOME"
echo ""
echo "  Configure connectors: edit $SEED_HOME/connectors.yml"
echo ""
