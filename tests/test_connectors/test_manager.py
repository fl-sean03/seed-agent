"""Tests for the ConnectorManager."""

import tempfile
from pathlib import Path

import yaml

from connectors.base.manager import ConnectorManager, _load_connector_class


class TestConnectorManager:
    def test_from_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connectors.yml"
            config_path.write_text(yaml.dump({
                "connectors": [
                    {"name": "cli-test", "type": "cli", "username": "test"},
                ]
            }))

            manager = ConnectorManager.from_config(config_path, seed_home=tmpdir)
            assert len(manager.connectors) == 1
            assert manager.connectors[0]["name"] == "cli-test"
            assert manager.connectors[0]["type"] == "cli"

    def test_add_connector(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorManager(seed_home=tmpdir)
            manager.add_connector("test1", "cli")
            manager.add_connector("test2", "webhook", {"port": 8080})
            assert len(manager.connectors) == 2

    def test_load_connector_class(self):
        cls = _load_connector_class("cli")
        assert cls.connector_type == "cli"

    def test_status_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorManager(seed_home=tmpdir)
            status = manager.status()
            assert status == {}
