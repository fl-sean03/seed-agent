#!/usr/bin/env python3
"""
Validate a seed network insight YAML file.

Usage: python validate.py path/to/insight.yaml
"""

import sys
from pathlib import Path

import yaml


REQUIRED_FIELDS = [
    "id",
    "title",
    "domain",
    "tags",
    "confidence",
    "source_seed",
    "timestamp",
    "version",
    "evidence",
]

VALID_DOMAINS = [
    "operations",
    "research",
    "development",
    "communication",
    "general",
]


def validate_insight(filepath: str) -> list[str]:
    """Validate an insight file. Returns list of errors (empty = valid)."""
    errors = []
    path = Path(filepath)

    if not path.exists():
        return [f"File not found: {filepath}"]

    content = path.read_text()

    # Check frontmatter markers
    parts = content.split("---")
    if len(parts) < 3:
        return ["Missing YAML frontmatter (must be between --- markers)"]

    # Parse YAML frontmatter
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return [f"Invalid YAML: {e}"]

    if not isinstance(data, dict):
        return ["Frontmatter must be a YAML mapping"]

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Validate field types
    if "confidence" in data:
        conf = data["confidence"]
        if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
            errors.append(f"confidence must be 0.0-1.0, got: {conf}")

    if "tags" in data:
        if not isinstance(data["tags"], list):
            errors.append("tags must be a list")

    if "evidence" in data:
        if not isinstance(data["evidence"], list):
            errors.append("evidence must be a list")

    if "domain" in data:
        if data["domain"] not in VALID_DOMAINS:
            errors.append(
                f"domain must be one of {VALID_DOMAINS}, got: {data['domain']}"
            )

    if "version" in data:
        if not isinstance(data["version"], int) or data["version"] < 1:
            errors.append("version must be a positive integer")

    # Check body content
    body = "---".join(parts[2:]).strip()
    if len(body) < 50:
        errors.append("Insight body is too short (< 50 chars). Add more detail.")

    return errors


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: validate.py <insight-file.yaml>")
        sys.exit(1)

    filepath = sys.argv[1]
    errors = validate_insight(filepath)

    if errors:
        print(f"INVALID: {filepath}")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"VALID: {filepath}")
        sys.exit(0)


if __name__ == "__main__":
    main()
