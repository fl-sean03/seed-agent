#!/bin/bash
# query.sh — Query insights from the seed network
# Usage: ./query.sh --tag <tag> | --domain <domain> | --text <text>

set -euo pipefail

NETWORK_DIR="$(cd "$(dirname "$0")" && pwd)"
INSIGHTS_DIR="$NETWORK_DIR/insights"

usage() {
    echo "Usage: query.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --tag TAG          Search by tag"
    echo "  --domain DOMAIN    Search by domain"
    echo "  --text TEXT        Search by text content"
    echo "  --all              List all insights"
    echo "  --format brief     Show only titles (default: full)"
    exit 1
}

if [ $# -eq 0 ]; then
    usage
fi

SEARCH_TAG=""
SEARCH_DOMAIN=""
SEARCH_TEXT=""
SHOW_ALL=false
FORMAT="full"

while [[ $# -gt 0 ]]; do
    case $1 in
        --tag) SEARCH_TAG="$2"; shift 2 ;;
        --domain) SEARCH_DOMAIN="$2"; shift 2 ;;
        --text) SEARCH_TEXT="$2"; shift 2 ;;
        --all) SHOW_ALL=true; shift ;;
        --format) FORMAT="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

if [ ! -d "$INSIGHTS_DIR" ]; then
    echo "No insights found. Publish some first."
    exit 0
fi

# Find matching files
MATCHES=()

while IFS= read -r -d '' file; do
    MATCH=false

    if $SHOW_ALL; then
        MATCH=true
    fi

    if [ -n "$SEARCH_DOMAIN" ]; then
        if echo "$file" | grep -q "/$SEARCH_DOMAIN/"; then
            MATCH=true
        fi
    fi

    if [ -n "$SEARCH_TAG" ]; then
        if grep -q "$SEARCH_TAG" "$file" 2>/dev/null; then
            MATCH=true
        fi
    fi

    if [ -n "$SEARCH_TEXT" ]; then
        if grep -qi "$SEARCH_TEXT" "$file" 2>/dev/null; then
            MATCH=true
        fi
    fi

    if $MATCH; then
        MATCHES+=("$file")
    fi
done < <(find "$INSIGHTS_DIR" -name "*.yaml" -o -name "*.yml" | tr '\n' '\0')

echo "Found ${#MATCHES[@]} insight(s)"
echo ""

for file in "${MATCHES[@]}"; do
    if [ "$FORMAT" = "brief" ]; then
        # Extract title from frontmatter
        TITLE=$(python3 -c "
import yaml
with open('$file') as f:
    content = f.read()
parts = content.split('---')
if len(parts) >= 3:
    data = yaml.safe_load(parts[1])
    print(data.get('title', '(no title)'))
" 2>/dev/null || echo "(parse error)")
        echo "  - $TITLE  [$file]"
    else
        echo "=== $(basename "$file") ==="
        cat "$file"
        echo ""
        echo "---"
        echo ""
    fi
done
