"""Tests for deployment scripts and templates."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent


class TestDeployScript:
    """Test deploy.sh creates the correct structure."""

    def test_bare_deploy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            seed_home = Path(tmpdir) / "agent"
            result = subprocess.run(
                ["bash", str(REPO_ROOT / "deploy" / "deploy.sh"),
                 "--seed-home", str(seed_home)],
                capture_output=True, text=True, timeout=30,
            )
            # Should succeed (pip install may fail but that's a warning)
            assert "Deployment complete" in result.stdout

            # Core structure must exist
            assert (seed_home / "seed" / "loop.sh").exists()
            assert (seed_home / "seed" / "PROMPT.md").exists()
            assert (seed_home / "seed" / "CONSTITUTION.md").exists()
            assert (seed_home / "seed" / "memory" / "MEMORY.md").exists()
            assert (seed_home / "seed" / "memory" / "lessons.md").exists()
            assert (seed_home / "seed" / "memory" / "self-reflection.md").exists()
            assert (seed_home / "seed" / "skills" / "SKILL-FORMAT.md").exists()
            assert (seed_home / "messages" / "inbox").is_dir()
            assert (seed_home / "messages" / "outbox").is_dir()
            assert (seed_home / "logs").is_dir()

    def test_deploy_with_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            seed_home = Path(tmpdir) / "agent"
            result = subprocess.run(
                ["bash", str(REPO_ROOT / "deploy" / "deploy.sh"),
                 "--seed-home", str(seed_home), "--context", "lab"],
                capture_output=True, text=True, timeout=30,
            )
            assert "Using context: lab" in result.stdout
            assert "Deployment complete" in result.stdout

    def test_deploy_idempotent(self):
        """Running deploy twice doesn't overwrite existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            seed_home = Path(tmpdir) / "agent"

            # Deploy once
            subprocess.run(
                ["bash", str(REPO_ROOT / "deploy" / "deploy.sh"),
                 "--seed-home", str(seed_home)],
                capture_output=True, text=True, timeout=30,
            )

            # Modify a memory file
            memory = seed_home / "seed" / "memory" / "MEMORY.md"
            memory.write_text("# Custom content\nI learned stuff.\n")

            # Deploy again
            subprocess.run(
                ["bash", str(REPO_ROOT / "deploy" / "deploy.sh"),
                 "--seed-home", str(seed_home)],
                capture_output=True, text=True, timeout=30,
            )

            # Custom content should be preserved (cp -n doesn't overwrite)
            assert "Custom content" in memory.read_text()


class TestSeedCLI:
    """Test the seed CLI tool."""

    def test_help(self):
        result = subprocess.run(
            ["bash", str(REPO_ROOT / "deploy" / "seed"), "help"],
            capture_output=True, text=True, timeout=10,
        )
        assert "seed" in result.stdout.lower()
        assert "init" in result.stdout
        assert "start" in result.stdout
        assert "stop" in result.stdout
        assert "status" in result.stdout

    def test_status_no_agent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["SEED_HOME"] = tmpdir
            result = subprocess.run(
                ["bash", str(REPO_ROOT / "deploy" / "seed"), "status"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            assert "STOPPED" in result.stdout


class TestTemplates:
    """Verify template files are valid."""

    def test_prompt_template_has_placeholders(self):
        tmpl = REPO_ROOT / "seed" / "PROMPT.md.template"
        content = tmpl.read_text()
        assert "{{" in content  # Has template placeholders
        assert "Your Identity" in content
        assert "Your Cycle" in content

    def test_constitution_template_has_placeholders(self):
        tmpl = REPO_ROOT / "seed" / "CONSTITUTION.md.template"
        content = tmpl.read_text()
        assert "{{IDENTITY}}" in content
        assert "{{BOUNDARIES}}" in content

    def test_memory_templates_exist(self):
        memory_dir = REPO_ROOT / "seed" / "memory"
        assert (memory_dir / "MEMORY.md.template").exists()
        assert (memory_dir / "lessons.md.template").exists()
        assert (memory_dir / "self-reflection.md.template").exists()

    def test_loop_is_executable(self):
        loop = REPO_ROOT / "seed" / "loop.sh"
        assert os.access(loop, os.X_OK)

    def test_loop_has_shebang(self):
        loop = REPO_ROOT / "seed" / "loop.sh"
        first_line = loop.read_text().split("\n")[0]
        assert first_line.startswith("#!/bin/bash")
