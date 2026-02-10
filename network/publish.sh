#!/bin/bash
# publish.sh — Publish an insight to the seed network
# Usage: ./publish.sh path/to/insight.yaml

set -euo pipefail

NETWORK_DIR="$(cd "$(dirname "$0")" && pwd)"
INSIGHTS_DIR="$NETWORK_DIR/insights"

if [ $# -eq 0 ]; then
    echo "Usage: publish.sh <insight-file.yaml>"
    echo ""
    echo "Validates and publishes an insight to the local network store."
    exit 1
fi

INSIGHT_FILE="$1"

if [ ! -f "$INSIGHT_FILE" ]; then
    echo "Error: File not found: $INSIGHT_FILE"
    exit 1
fi

# Validate
if command -v python3 &>/dev/null && [ -f "$NETWORK_DIR/tools/validate.py" ]; then
    python3 "$NETWORK_DIR/tools/validate.py" "$INSIGHT_FILE"
    if [ $? -ne 0 ]; then
        echo "Error: Validation failed. Fix the issues and try again."
        exit 1
    fi
fi

# Extract domain from frontmatter
DOMAIN=$(python3 -c "
import yaml, sys
with open('$INSIGHT_FILE') as f:
    content = f.read()
# Extract YAML frontmatter between --- markers
parts = content.split('---')
if len(parts) >= 3:
    data = yaml.safe_load(parts[1])
    print(data.get('domain', 'general'))
else:
    print('general')
" 2>/dev/null || echo "general")

# Create domain directory
mkdir -p "$INSIGHTS_DIR/$DOMAIN"

# Copy insight
FILENAME=$(basename "$INSIGHT_FILE")
DEST="$INSIGHTS_DIR/$DOMAIN/$FILENAME"
cp "$INSIGHT_FILE" "$DEST"

echo "Published: $DEST"
echo "Domain: $DOMAIN"
echo ""
echo "To share with other seeds, sync the insights/ directory."
