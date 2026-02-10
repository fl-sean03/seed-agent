"""
Connector Manager — orchestrates multiple connectors in parallel.

Reads connectors.yml, instantiates each connector, and runs them
as separate processes for failure isolation.
"""

from __future__ import annotations

import importlib
import logging
import multiprocessing
import signal
import sys
import time
from pathlib import Path
from typing import Any

import yaml

from connectors.base.connector import Connector


logger = logging.getLogger("connector.manager")

# Registry of built-in connector types
CONNECTOR_REGISTRY: dict[str, str] = {
    "cli": "connectors.cli.connector",
    "slack": "connectors.slack.connector",
    "discord": "connectors.discord.connector",
    "telegram": "connectors.telegram.connector",
    "email": "connectors.email.connector",
    "webhook": "connectors.webhook.connector",
}


def _load_connector_class(connector_type: str) -> type[Connector]:
    """Import and return the Connector subclass for a given type."""
    if connector_type in CONNECTOR_REGISTRY:
        module_path = CONNECTOR_REGISTRY[connector_type]
    else:
        # Allow fully qualified module paths for custom connectors
        module_path = connector_type

    module = importlib.import_module(module_path)

    # Find the Connector subclass in the module
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, Connector)
            and attr is not Connector
            and attr.connector_type
        ):
            return attr

    raise ImportError(
        f"No Connector subclass found in {module_path}. "
        f"Ensure the module defines a class with connector_type set."
    )


def _run_connector(
    connector_type: str,
    name: str,
    seed_home: str,
    config: dict[str, Any],
) -> None:
    """Entry point for each connector subprocess."""
    try:
        cls = _load_connector_class(connector_type)
        connector = cls(name=name, seed_home=seed_home, config=config)
        connector.run()
    except Exception as e:
        logger.error(f"Connector {name} crashed: {e}", exc_info=True)
        sys.exit(1)


class ConnectorManager:
    """
    Manages multiple connectors as separate processes.

    Usage:
        manager = ConnectorManager.from_config("connectors.yml", seed_home="/path")
        manager.start()   # Blocks until all connectors stop or Ctrl+C
    """

    def __init__(self, seed_home: str | Path):
        self.seed_home = Path(seed_home)
        self.connectors: list[dict[str, Any]] = []
        self.processes: dict[str, multiprocessing.Process] = {}
        self._running = True

    def add_connector(
        self,
        name: str,
        connector_type: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Register a connector to be managed."""
        self.connectors.append({
            "name": name,
            "type": connector_type,
            "config": config or {},
        })

    @classmethod
    def from_config(cls, config_path: str | Path, seed_home: str | Path) -> ConnectorManager:
        """Create a manager from a connectors.yml file."""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        with open(config_path) as f:
            raw = yaml.safe_load(f)

        manager = cls(seed_home=seed_home)

        for entry in raw.get("connectors", []):
            manager.add_connector(
                name=entry["name"],
                connector_type=entry["type"],
                config={k: v for k, v in entry.items() if k not in ("name", "type")},
            )

        return manager

    def _start_connector(self, entry: dict[str, Any]) -> multiprocessing.Process:
        """Start a single connector as a subprocess."""
        name = entry["name"]
        proc = multiprocessing.Process(
            target=_run_connector,
            args=(entry["type"], name, str(self.seed_home), entry["config"]),
            name=f"connector-{name}",
            daemon=True,
        )
        proc.start()
        logger.info(f"Started connector: {name} (pid={proc.pid})")
        return proc

    def start(self, restart_on_crash: bool = True, restart_delay: float = 5.0) -> None:
        """
        Start all connectors and monitor them.
        Blocks until stopped via signal or all connectors exit.
        """
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        logger.info(f"Starting {len(self.connectors)} connector(s)...")

        # Start all connectors
        for entry in self.connectors:
            self.processes[entry["name"]] = self._start_connector(entry)

        # Monitor loop
        while self._running:
            time.sleep(2)

            for entry in self.connectors:
                name = entry["name"]
                proc = self.processes.get(name)

                if proc and not proc.is_alive():
                    exit_code = proc.exitcode
                    logger.warning(f"Connector {name} exited (code={exit_code})")

                    if restart_on_crash and self._running:
                        logger.info(f"Restarting {name} in {restart_delay}s...")
                        time.sleep(restart_delay)
                        self.processes[name] = self._start_connector(entry)

        self._shutdown()

    def _handle_signal(self, signum: int, frame: Any) -> None:
        logger.info(f"Manager received signal {signum}")
        self._running = False

    def _shutdown(self) -> None:
        """Gracefully stop all connectors."""
        logger.info("Shutting down all connectors...")
        for name, proc in self.processes.items():
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=10)
                if proc.is_alive():
                    logger.warning(f"Force-killing {name}")
                    proc.kill()
        logger.info("All connectors stopped")

    def status(self) -> dict[str, dict[str, Any]]:
        """Get status of all connectors."""
        result = {}
        for entry in self.connectors:
            name = entry["name"]
            proc = self.processes.get(name)
            result[name] = {
                "type": entry["type"],
                "pid": proc.pid if proc else None,
                "alive": proc.is_alive() if proc else False,
            }
        return result
