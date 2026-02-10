"""Tests for the insight validator."""

import tempfile
from pathlib import Path

# Import directly since it's a standalone script
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "network" / "tools"))
from validate import validate_insight


def _write_insight(tmpdir, content):
    path = Path(tmpdir) / "test-insight.yaml"
    path.write_text(content)
    return str(path)


class TestValidateInsight:
    def test_valid_insight(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_insight(tmpdir, """---
id: test-001
title: "Test insight"
domain: operations
tags: [test, validation]
confidence: 0.8
source_seed: test-seed
timestamp: 2026-02-10T00:00:00Z
version: 1
evidence:
  - "Test evidence one"
  - "Test evidence two"
---

## Insight

This is a test insight with enough content to pass the minimum length
requirement for the body section of the insight file.
""")
            errors = validate_insight(path)
            assert errors == []

    def test_missing_required_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_insight(tmpdir, """---
id: test-002
title: "Missing fields"
---

## Insight

This insight is missing required fields and should fail validation
with multiple error messages about missing fields.
""")
            errors = validate_insight(path)
            assert len(errors) > 0
            assert any("Missing required field" in e for e in errors)

    def test_invalid_confidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_insight(tmpdir, """---
id: test-003
title: "Bad confidence"
domain: operations
tags: [test]
confidence: 1.5
source_seed: test
timestamp: 2026-02-10T00:00:00Z
version: 1
evidence: ["test"]
---

## Insight

This insight has an invalid confidence value that should fail
the validation check for the confidence range.
""")
            errors = validate_insight(path)
            assert any("confidence" in e for e in errors)

    def test_invalid_domain(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_insight(tmpdir, """---
id: test-004
title: "Bad domain"
domain: invalid_domain
tags: [test]
confidence: 0.5
source_seed: test
timestamp: 2026-02-10T00:00:00Z
version: 1
evidence: ["test"]
---

## Insight

This insight has an invalid domain that should fail the validation
check for valid domain values in the frontmatter.
""")
            errors = validate_insight(path)
            assert any("domain" in e for e in errors)

    def test_missing_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = _write_insight(tmpdir, "Just plain text without frontmatter.")
            errors = validate_insight(path)
            assert any("frontmatter" in e.lower() for e in errors)

    def test_file_not_found(self):
        errors = validate_insight("/nonexistent/path.yaml")
        assert len(errors) == 1
        assert "not found" in errors[0].lower()
